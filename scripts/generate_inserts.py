import pandas as pd
import numpy as np

# Mapping dictionary for specific clinical terms to fit schema constraints
CLINICAL_MAPPING = {
    # Race replacements
    "Unknown or not reported": "unknown",
    "Black or African American": "African American",
    "Native American/ Alaska Native": "Native American",
    
    # Pathology / General replacements
    "Inadequate for diagnosis": "Inadequate",
    "Not Available": "NA",
    "Not available": "NA",
    "Adenocarcinoma with NE features": "Adenocarcinoma"
}

def clean_sql_val(val, limit=None):
    """Applies custom mapping, cleans for SQL, and optionally truncates."""
    if pd.isna(val) or str(val).lower() == 'nan':
        return 'NULL'
    
    val_str = str(val).strip()
    
    # Apply specific replacements requested
    if val_str in CLINICAL_MAPPING:
        val_str = CLINICAL_MAPPING[val_str]
    
    # Escape quotes
    s = val_str.replace("'", "''")
    
    # Truncate if still over limit (safety fallback)
    if limit:
        s = s[:limit]
    return s

def generate_sql_script(patient_file, sample_file, mapping_file, output_file):
    # Load data
    patient_df = pd.read_csv(patient_file, sep='\t', comment='#')
    sample_df = pd.read_csv(sample_file, sep='\t', comment='#')
    mapping_df = pd.read_csv(mapping_file, sep='\t')
    
    # ID cleaning
    patient_df['PATIENT_ID'] = patient_df['PATIENT_ID'].astype(str).str.zfill(8)
    sample_df['PATIENT_ID'] = sample_df['PATIENT_ID'].astype(str).str.zfill(8)
    mapping_df['SU2C Study Identifier'] = mapping_df['SU2C Study Identifier'].astype(str).str.zfill(8)

    # --- Performance Header ---
    sql_statements = [
        "-- Auto-generated Optimized SQL Insert Script\n",
        "SET FOREIGN_KEY_CHECKS = 0;\n",
        "SET UNIQUE_CHECKS = 0;\n",
        "SET AUTOCOMMIT = 0;\n",
        "START TRANSACTION;\n\n"
    ]

    def create_lookup(df, column, table_name, col_name, limit):
        raw_vals = [str(x) for x in df[column].unique() if pd.notna(x)]
        lookup = {}
        processed_entries = []
        seen_mapped_strs = {} 

        for val in sorted(raw_vals):
            mapped_str = CLINICAL_MAPPING.get(val, val)[:limit].replace("'", "''")
            if mapped_str not in seen_mapped_strs:
                entry_id = len(seen_mapped_strs) + 1
                seen_mapped_strs[mapped_str] = entry_id
                processed_entries.append(f"('{mapped_str}')")
            lookup[val] = seen_mapped_strs[mapped_str]
        
        if "Unknown" not in lookup:
            unknown_id = len(seen_mapped_strs) + 1
            processed_entries.append("('Unknown')")
            default_id = unknown_id
        else:
            default_id = lookup.get("Unknown")

        sql_statements.append(f"INSERT INTO {table_name} ({col_name}) VALUES\n" + ",\n".join(processed_entries) + ";\n\n")
        return lookup, default_id

    # 1. Populate Lookup Tables
    race_lookup, race_def = create_lookup(patient_df, 'RACE', 'race', 'race', 20)
    chemo_lookup, chemo_def = create_lookup(patient_df, 'CHEMO_REGIMEN_CATEGORY', 'chemoTreatment', 'regimen', 50)
    lab_lookup, lab_def = create_lookup(sample_df, 'TISSUE_SOURCE_SITE', 'labLocation', 'labLocation', 20)
    drug_lookup, drug_def = create_lookup(sample_df, 'ABI_ENZA_EXPOSURE_STATUS', 'DrugExposure', 'drugExposure', 15)
    fusion_lookup, fusion_def = create_lookup(sample_df, 'ETS_FUSION_SEQ', 'ETSFusion', 'ETSFusion', 20)
    site_lookup, site_def = create_lookup(sample_df, 'TISSUE_SITE', 'tissueSite', 'tissueSite', 20)
    path_lookup, path_def = create_lookup(sample_df, 'PATHOLOGY_CLASSIFICATION', 'pathology', 'pathology', 20)

    # 2. Populate Patient Table in Batches
    patient_rows = []
    added_pids = set()
    for _, row in patient_df.iterrows():
        pid = row['PATIENT_ID']
        gender = 'M' if row['SEX'] == 'Male' else ('F' if row['SEX'] == 'Female' else 'U')
        status = 1 if 'DECEASED' in str(row['OS_STATUS']) else 0
        rid = race_lookup.get(str(row['RACE']), race_def)
        cid = chemo_lookup.get(str(row['CHEMO_REGIMEN_CATEGORY']), chemo_def)
        
        # UPDATED: DECIMAL(3,1) for diagnosisAge and overallSurvival
        age = float(row['AGE_AT_DIAGNOSIS']) if pd.notna(row['AGE_AT_DIAGNOSIS']) else 0.0
        os = float(row['OS_MONTHS']) if pd.notna(row['OS_MONTHS']) else 0.0
        
        # Using formatting to ensure one decimal place
        patient_rows.append(f"('{pid}', {rid}, '{gender}', {cid}, {age:.1f}, {status}, {os:.1f})")
        added_pids.add(pid)
    
    for i in range(0, len(patient_rows), 1000):
        batch = patient_rows[i:i+1000]
        sql_statements.append("INSERT INTO Patient (patientID, raceID, gender, chemoRegimenID, diagnosisAge, survivalStatus, overallSurvival) VALUES\n" + ",\n".join(batch) + ";\n")

    # 3. Populate patientIdMapper
    mapper_rows = []
    for _, row in mapping_df.iterrows():
        pid, other = row['SU2C Study Identifier'], row['Identifier']
        if pid in added_pids and pd.notna(other):
            mapper_rows.append(f"('{pid}', '{clean_sql_val(other, 30)}')")
    
    if mapper_rows:
        sql_statements.append("\nINSERT INTO patientIdMapper (patientID, otherIdentifier) VALUES\n" + ",\n".join(mapper_rows) + ";\n")

    # 4. Populate Sample Table in Batches
    sample_rows = []
    sample_db_tracker = {}
    current_idx = 1
    for _, row in sample_df.iterrows():
        pid = row['PATIENT_ID']
        if pid not in added_pids: continue
        
        lab = lab_lookup.get(str(row['TISSUE_SOURCE_SITE']), lab_def)
        ne = 1 if row['NEUROENDOCRINE_FEATURES'] == 'Yes' else 0
        drug = drug_lookup.get(str(row['ABI_ENZA_EXPOSURE_STATUS']), drug_def)
        tax = 1 if row['TAXANE_EXPOSURE_STATUS'] == 'Exposed' else 0
        fus = fusion_lookup.get(str(row['ETS_FUSION_SEQ']), fusion_def)
        site = site_lookup.get(str(row['TISSUE_SITE']), site_def)
        
        # UPDATED: DECIMAL(3,1) for patientAgeAtProcurement
        age_p = float(row['AGE_AT_PROCUREMENT']) if pd.notna(row['AGE_AT_PROCUREMENT']) else 0.0
        
        try:
            gs = int(float(row['GLEASON_SCORE']))
        except:
            gs = 0
            
        path = path_lookup.get(str(row['PATHOLOGY_CLASSIFICATION']), path_def)
        off_a = 1 if row['OFF_ARSI'] == 1.0 else 0
        
        # UPDATED: DECIMAL(4,3) for mutationalBurden
        tmb = float(row['TMB_NONSYNONYMOUS']) if pd.notna(row['TMB_NONSYNONYMOUS']) else 0.000
        
        sid = clean_sql_val(row['SAMPLE_ID'], 50)
        # Using formatting to ensure correct precision
        sample_rows.append(f"('{sid}', '{pid}', {lab}, {ne}, {drug}, {tax}, {fus}, {site}, {age_p:.1f}, {gs}, {path}, {off_a}, {tmb:.3f})")
        sample_db_tracker[row['SAMPLE_ID']] = current_idx
        current_idx += 1

    if sample_rows:
        for i in range(0, len(sample_rows), 1000):
            batch = sample_rows[i:i+1000]
            sql_statements.append("\nINSERT INTO Sample (sample_identifier, patientID, labID, neuroEndocrineFeatures, drugExposureID, taxaneExposure, ETSFusionID, tissueSiteID, patientAgeAtProcurement, gleasonScore, pathologyID, offARIS, mutationalBurden) VALUES\n" + ",\n".join(batch) + ";\n")

    # 5. Populate SampleIDMapper
    for _, row in sample_df.iterrows():
        sid, alt = row['SAMPLE_ID'], row['OTHER_SAMPLE_ID']
        if sid in sample_db_tracker and pd.notna(alt):
            sql_statements.append(f"INSERT INTO SampleIDMapper (sampleID, altID) SELECT sample_ID, '{clean_sql_val(alt, 20)}' FROM Sample WHERE sample_identifier = '{clean_sql_val(sid, 50)}';\n")

    # --- Performance Footer ---
    sql_statements.append("\nCOMMIT;\n")
    sql_statements.append("SET FOREIGN_KEY_CHECKS = 1;\n")
    sql_statements.append("SET UNIQUE_CHECKS = 1;\n")
    sql_statements.append("SET AUTOCOMMIT = 1;\n")

    with open(output_file, 'w') as f:
        f.writelines(sql_statements)
    print(f"Success: {output_file} generated with transactions and updated DECIMAL precision.")

if __name__ == "__main__":
    generate_sql_script('../data/raw/data_clinical_patient.txt', '../data/raw/data_clinical_sample.txt', '../data/raw/patient_id_mapping.txt', '../sql/1_populate_clinical.sql')
