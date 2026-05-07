import pandas as pd
import numpy as np

def generate_mutation_sql_optimized(maf_file, output_file):
    try:
        # Load the MAF file
        df = pd.read_csv(maf_file, sep='\t', comment='#', low_memory=False)
    except Exception as e:
        print(f"Error reading {maf_file}: {e}")
        return

    # --- 1. Data Cleaning ---
    df['Chromosome'] = df['Chromosome'].astype(str).str.replace('chr', '', case=False)
    def format_chromosome(c):
        c = c.upper()
        if c.isdigit():
            val = int(c)
            if 1 <= val <= 9: return f"0{val}"
            elif 10 <= val <= 22: return str(val)
        elif c in ['X', 'Y', 'M']: return f" {c}"
        return None
    df['Chromosome'] = df['Chromosome'].apply(format_chromosome)
    df = df.dropna(subset=['Chromosome'])

    def clean_rsid(val):
        if pd.isna(val) or str(val).lower() in ['nan', 'novel', '']:
            return 'NULL'
        first_id = str(val).split('|')[0].strip()
        cleaned_id = first_id.replace("'", "''")
        return f"'{cleaned_id}'"

    df['Hugo_Symbol_clean'] = df['Hugo_Symbol'].astype(str).str.replace("'", "''")
    df['Reference_Allele_clean'] = df['Reference_Allele'].astype(str).str.slice(0, 50).str.replace("'", "''")
    df['Tumor_Seq_Allele2_clean'] = df['Tumor_Seq_Allele2'].astype(str).str.slice(0, 50).str.replace("'", "''")
    df['Variant_Classification_clean'] = df['Variant_Classification'].astype(str).str.slice(0, 35).str.replace("'", "''")
    df['Variant_Type_clean'] = df['Variant_Type'].astype(str).str.slice(0, 3).str.replace("'", "''")
    df['dbSNP_RS_clean'] = df['dbSNP_RS'].apply(clean_rsid)
    
    def clean_hgvsp(val):
        if pd.isna(val) or str(val).lower() == 'nan': return 'NULL'
        cleaned = str(val).replace("'", "''")[:25]
        return f"'{cleaned}'"
    df['HGVSp_Short_clean'] = df['HGVSp_Short'].apply(clean_hgvsp)

    with open(output_file, 'w') as f:
        # --- Performance Header ---
        f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
        f.write("SET UNIQUE_CHECKS = 0;\n")
        f.write("SET AUTOCOMMIT = 0;\n")
        f.write("START TRANSACTION;\n\n")

        # --- Step 1: Bulk Populate geneInfo ---
        f.write("-- Step 1: Populating geneInfo\n")
        unique_genes = df[['Hugo_Symbol_clean', 'Entrez_Gene_Id']].drop_duplicates()
        gene_rows = []
        for _, row in unique_genes.iterrows():
            entrez = int(row['Entrez_Gene_Id']) if pd.notna(row['Entrez_Gene_Id']) else 0
            gene_rows.append(f"('{row['Hugo_Symbol_clean']}', {entrez})")
        
        for i in range(0, len(gene_rows), 1000):
            batch = gene_rows[i:i+1000]
            f.write("INSERT IGNORE INTO geneInfo (hugo_symbol, entrez_id) VALUES\n" + ",\n".join(batch) + ";\n")

        # --- Step 2: tumor_matching_normal ---
        f.write("\n-- Step 2: Populating tumor_matching_normal\n")
        matching = df[['Tumor_Sample_Barcode', 'Matched_Norm_Sample_Barcode']].drop_duplicates()
        for _, row in matching.iterrows():
            tumor = str(row['Tumor_Sample_Barcode']).replace("'", "''")
            normal = str(row['Matched_Norm_Sample_Barcode']).replace("'", "''")
            if normal.lower() not in ['nan', 'na', '']:
                f.write(f"INSERT INTO tumor_matching_normal (tumor_sample_ID, matched_normal) "
                        f"SELECT t.sample_ID, '{normal}' FROM Sample t "
                        f"WHERE t.sample_identifier = '{tumor}';\n")

        # --- Step 3: Populate variant (Updated for Lookup Tables) ---
        # Note: Since variant now requires IDs from lookup tables, we use INSERT INTO ... SELECT
        f.write("\n-- Step 3: Populating variant table via lookup subqueries\n")
        var_cols = ['Reference_Allele_clean', 'Chromosome', 'Start_Position', 'End_Position', 
                    'Tumor_Seq_Allele2_clean', 'Variant_Classification_clean', 'Variant_Type_clean', 
                    'HGVSp_Short_clean', 'dbSNP_RS_clean']
        unique_variants = df[var_cols].drop_duplicates()
        
        for _, row in unique_variants.iterrows():
            query = (
                f"INSERT IGNORE INTO variant (reference_allele, chromosome, stat_pos, end_pos, alt_allele, "
                f"dbSNPid, variantClassificationID, variantTypeID, hgvsp_short) \n"
                f"SELECT '{row['Reference_Allele_clean']}', '{row['Chromosome']}', {int(row['Start_Position'])}, "
                f"{int(row['End_Position'])}, '{row['Tumor_Seq_Allele2_clean']}', {row['dbSNP_RS_clean']}, "
                f"vc.variantClassificationID, vt.variantTypeID, {row['HGVSp_Short_clean']} \n"
                f"FROM variantClassification vc, variantType vt \n"
                f"WHERE vc.variant_classification = '{row['Variant_Classification_clean']}' \n"
                f"AND vt.variant_type = '{row['Variant_Type_clean']}';\n"
            )
            f.write(query)

        # --- Step 4: observation using Subqueries ---
        f.write("\n-- Step 4: Populating observation table\n")
        for _, row in df.iterrows():
            tumor = str(row['Tumor_Sample_Barcode']).replace("'", "''")
            hugo = row['Hugo_Symbol_clean']
            
            query = (
                f"INSERT INTO observation (sampleID, variantID, gene_ID) "
                f"SELECT s.sample_ID, v.variantID, g.geneID "
                f"FROM Sample s, variant v, geneInfo g "
                f"WHERE s.sample_identifier = '{tumor}' "
                f"AND g.hugo_symbol = '{hugo}' "
                f"AND v.chromosome = '{row['Chromosome']}' AND v.stat_pos = {int(row['Start_Position'])} "
                f"AND v.reference_allele = '{row['Reference_Allele_clean']}' AND v.alt_allele = '{row['Tumor_Seq_Allele2_clean']}' "
                f"LIMIT 1;\n"
            )
            f.write(query)

        # --- Performance Footer ---
        f.write("\nCOMMIT;\n")
        f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
        f.write("SET UNIQUE_CHECKS = 1;\n")
        f.write("SET AUTOCOMMIT = 1;\n")

    print(f"Success: {output_file} updated for normalized lookup tables.")

if __name__ == "__main__":
    generate_mutation_sql_optimized('../data/raw/data_mutations.txt', '../sql/2_populate_mutations.sql')
