# Data Dictionary


---

## Table of Contents

1. [Lookup / Reference Tables](#1-lookup--reference-tables)
   - race
   - chemoTreatment
   - labLocation
   - DrugExposure
   - ETSFusion
   - tissueSite
   - pathology
   - variantClassification
   - variantType
2. [Core Entity Tables](#2-core-entity-tables)
   - Patient
   - patientIdMapper
   - Sample
   - SampleIDMapper
   - tumor_matching_normal
3. [Gene Information](#3-gene-information)
   - geneInfo
4. [Expression Tables](#4-expression-tables)
   - mrna_polya
   - mrna_capture
5. [Copy Number Alteration](#5-copy-number-alteration)
   - CNA
6. [Variant Tables](#6-variant-tables)
   - variant
   - observation

---

## 1. Lookup / Reference Tables

### `race`

| Column  | Type                | PK/FK | Description                                                   |
|---------|---------------------|-------|---------------------------------------------------------------|
| raceID  | TINYINT UNSIGNED    | PK    | Auto-incremented surrogate key for the race/ethnicity category. |
| race    | VARCHAR(20)         |       | Race or ethnicity label (e.g., `White Non-Hispanic`, `White Hispanic`, `Unknown or not reported`). Sourced from `RACE` field in `data_clinical_patient.txt`. |

---

### `chemoTreatment`

| Column        | Type             | PK/FK | Description                                                                                                       |
|---------------|------------------|-------|-------------------------------------------------------------------------------------------------------------------|
| chemoRegimenID | TINYINT UNSIGNED | PK    | Auto-incremented surrogate key for the chemotherapy regimen.                                                     |
| regimen       | VARCHAR(50)      |       | Name of the chemotherapy regimen category (e.g., `abiraterone+Dutasteride`, `Standard of care enzalutamide`). Sourced from `CHEMO_REGIMEN_CATEGORY` in `data_clinical_patient.txt`. |

---

### `labLocation`

| Column      | Type      | PK/FK | Description                                                                                                 |
|-------------|-----------|-------|-------------------------------------------------------------------------------------------------------------|
| labID       | TINYINT UNSIGNED | PK | Auto-incremented surrogate key for the laboratory site.                                               |
| labLocation | CHAR(20)  |       | Name or abbreviation of the contributing lab / tissue source site (e.g., `DFCI`, `Michigan`, `MSK`). Sourced from `TISSUE_SOURCE_SITE` in `data_clinical_sample.txt`. |

---

### `DrugExposure`

| Column        | Type             | PK/FK | Description                                                                                                                      |
|---------------|------------------|-------|----------------------------------------------------------------------------------------------------------------------------------|
| drugExposureID | TINYINT UNSIGNED | PK   | Auto-incremented surrogate key for the drug exposure category.                                                                  |
| drugExposure  | VARCHAR(15)      |       | Abiraterone (ABI) and Enzalutamide (ENZA) exposure status (e.g., `Naive`, `Exposed`, `On treatment`). Sourced from `ABI_ENZA_EXPOSURE_STATUS` in `data_clinical_sample.txt`. |

---

### `ETSFusion`

| Column     | Type             | PK/FK | Description                                                                                                                        |
|------------|------------------|-------|------------------------------------------------------------------------------------------------------------------------------------|
| ETSFusionID | TINYINT UNSIGNED | PK   | Auto-incremented surrogate key for the ETS fusion status.                                                                         |
| ETSFusion  | VARCHAR(20)      |       | ETS gene fusion status or identity as detected by sequencing (e.g., `Positive`, `Negative`, `No Data`, specific fusion like `TMPRSS2-ERG`). Sourced from `ETS_FUSION_SEQ` in `data_clinical_sample.txt`. |

---

### `tissueSite`

| Column      | Type             | PK/FK | Description                                                                                                     |
|-------------|------------------|-------|-----------------------------------------------------------------------------------------------------------------|
| tissueSiteID | TINYINT UNSIGNED | PK   | Auto-incremented surrogate key for the tissue site.                                                            |
| tissueSite  | VARCHAR(20)      |       | Anatomical site from which the biopsy specimen was collected (e.g., `Prostate`, `LN`, `Bone`, `Liver`, `Other Soft tissue`). Sourced from `TISSUE_SITE` in `data_clinical_sample.txt`. |

---

### `pathology`

| Column     | Type             | PK/FK | Description                                                                                                          |
|------------|------------------|-------|----------------------------------------------------------------------------------------------------------------------|
| pathologyID | TINYINT UNSIGNED | PK   | Auto-incremented surrogate key for the pathology classification.                                                    |
| pathology  | VARCHAR(20)      |       | Histological pathology classification of the tumor sample (e.g., `Adenocarcinoma`, `Not available`, `Inadequate for diagnosis`). Sourced from `PATHOLOGY_CLASSIFICATION` in `data_clinical_sample.txt`. |

---

### `variantClassification`

| Column     | Type             | PK/FK | Description                                                                                                          |
|------------|------------------|-------|----------------------------------------------------------------------------------------------------------------------|
| variantClassificationID | TINYINT UNSIGNED | PK   | Auto-incremented surrogate key for the variant classification.                                                    |
| variant_classification  | VARCHAR(35)      |       | Functional classification of the variant (e.g., Missense_Mutation, Nonsense_Mutation, Frame_Shift_Del, Silent). Sourced from MAF Variant_Classification.|

---

### `variantTypeID`

| Column     | Type             | PK/FK | Description                                                                                                          |
|------------|------------------|-------|----------------------------------------------------------------------------------------------------------------------|
| variantTypeID | TINYINT UNSIGNED | PK   | Auto-incremented surrogate key for the pathology classification.                                                    |
| variant_type  | CHAR(3)      |       | Molecular type of the variant (SNP, INS, DEL). Sourced from MAF Variant_Type.|

---

## 2. Core Entity Tables

### `Patient`

| Column         | Type             | PK/FK | Description                                                                                                               |
|----------------|------------------|-------|---------------------------------------------------------------------------------------------------------------------------|
| patientID      | CHAR(8)          | PK    | Unique patient identifier (e.g., `1115015`). Sourced from `PATIENT_ID` in `data_clinical_patient.txt`.                   |
| raceID         | TINYINT UNSIGNED | FK → race | Foreign key to `race.raceID`. Encodes the patient's race/ethnicity category.                                      |
| gender         | CHAR(1)          |       | Patient biological sex (`M` = Male, `F` = Female). Sourced from `SEX` in `data_clinical_patient.txt`.                    |
| chemoRegimenID | TINYINT UNSIGNED | FK → chemoTreatment | Foreign key to `chemoTreatment.chemoRegimenID`. Encodes the patient's assigned chemotherapy regimen.   |
| diagnosisAge   | DECIMAL(3,1) |       | Patient's age (in years) at initial prostate cancer diagnosis. Sourced from `AGE_AT_DIAGNOSIS` in `data_clinical_patient.txt`. |
| survivalStatus | INT              |       | Patient's overall survival status. `0` = LIVING; `1` = DECEASED. Sourced from `OS_STATUS` in `data_clinical_patient.txt`. |
| overallSurvival | DECIMAL(3,1)    |       | Overall survival time in months since initial diagnosis. Sourced from `OS_MONTHS` in `data_clinical_patient.txt`.         |


---

### `patientIdMapper`

| Column          | Type        | PK/FK          | Description                                                              |
|-----------------|-------------|----------------|--------------------------------------------------------------------------|
| patientID       | CHAR(8)     | PK, FK → Patient | Foreign key to `Patient.patientID`.  |
| otherIdentifier | VARCHAR(30) | PK             | An alternative or legacy identifier for the same patient. |

---

### `Sample`

| Column                 | Type             | PK/FK              | Description                                                                                                                                                                                                                                       |
|------------------------|------------------|--------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| sample_ID              | INT              | PK                 | Auto-incremented surrogate key for the sample record.                                                                                                                                                                                            |
| sample_identifier      | VARCHAR(50)      |                    | Human-readable sample identifier (e.g., `DFCI.11-104.02-Tumor`). Sourced from `SAMPLE_ID` in `data_clinical_sample.txt`.                                                                                                                        |
| patientID              | CHAR(8)          | FK → Patient       | Foreign key to `Patient.patientID`. Links the sample to its donor patient.                                                                                                                                                                       |
| labID                  | TINYINT UNSIGNED | FK → labLocation   | Foreign key to `labLocation.labID`. Indicates which lab collected and processed the sample.                                                                                                                                                      |
| neuroEndocrineFeatures | BOOL             |                    | Whether the sample exhibits neuroendocrine features (`TRUE`/`FALSE`). Sourced from `NEUROENDOCRINE_FEATURES` in `data_clinical_sample.txt`.                                                                                                       |
| drugExposureID         | TINYINT UNSIGNED | FK → DrugExposure  | Foreign key to `DrugExposure.drugExposureID`. Encodes ABI/ENZA exposure status at time of sample procurement.                                                                                                                                    |
| taxaneExposure         | BOOL             |                    | Whether the patient had prior taxane (chemotherapy) exposure at the time of sample procurement (`TRUE`/`FALSE`). Sourced from `TAXANE_EXPOSURE_STATUS` in `data_clinical_sample.txt`.                                                            |
| ETSFusionID            | TINYINT UNSIGNED | FK → ETSFusion     | Foreign key to `ETSFusion.ETSFusionID`. Encodes the ETS gene fusion status detected in this sample.                                                                                                                                             |
| tissueSiteID           | TINYINT UNSIGNED | FK → tissueSite    | Foreign key to `tissueSite.tissueSiteID`. Anatomical location of the biopsy.                                                                                                                                                                    |
| patientAgeAtProcurement | DECIMAL(3,1)    |                    | Patient age in years at the time the specimen was collected. Sourced from `AGE_AT_PROCUREMENT` in `data_clinical_sample.txt`.                                                                                                                    |
| gleasonScore           | TINYINT UNSIGNED |                    | Radical prostatectomy Gleason score (integer 1–10). A higher score indicates more aggressive, poorly differentiated tumor histology. Sourced from `GLEASON_SCORE` in `data_clinical_sample.txt`.                                                 |
| pathologyID            | TINYINT UNSIGNED | FK → pathology     | Foreign key to `pathology.pathologyID`. Histological classification of the tumor.                                                                                                                                                               |
| offARIS                | BOOL             |                    | Whether the patient was off androgen receptor inhibitor (ARSI) therapy at time of sampling (`TRUE`/`FALSE`). Sourced from `OFF_ARSI` in `data_clinical_sample.txt`.                                                                              |
| mutationalBurden       | DECIMAL(5,3)     |                    | Tumor mutational burden (TMB), counted as nonsynonymous somatic mutations. Sourced from `TMB_NONSYNONYMOUS` in `data_clinical_sample.txt`.                                                                                                        |

---

### `SampleIDMapper`

| Column   | Type        | PK/FK          | Description                                                                                   |
|----------|-------------|----------------|-----------------------------------------------------------------------------------------------|
| sampleID | INT         | PK, FK → Sample | Foreign key to `Sample.sample_ID`. Part of composite primary key.                           |
| altID    | VARCHAR(20) |                | An alternative identifier for this sample (e.g., the numeric patient-level ID used as `OTHER_SAMPLE_ID` in `data_clinical_sample.txt`). 

---

### `tumor_matching_normal`

| Column           | Type        | PK/FK          | Description                                                                                                          |
|------------------|-------------|----------------|----------------------------------------------------------------------------------------------------------------------|
| tumor_sample_ID  | INT         | PK, FK → Sample | Foreign key to `Sample.sample_ID`. Identifies the tumor sample. Also serves as the primary key (one matched normal per tumor). |
| matched_normal   | VARCHAR(50) |                | Identifier of the matched normal sample used for somatic variant calling in the mutation file. |

---

## 3. Gene Information

### `geneInfo`

| Column      | Type        | PK/FK | Description                                                                                 |
|-------------|-------------|-------|---------------------------------------------------------------------------------------------|
| geneID      | INT         | PK    | Auto-incremented surrogate key for the gene record.                                        |
| hugo_symbol | VARCHAR(50) |       | HUGO Gene Nomenclature Committee (HGNC) approved gene symbol (e.g., `TP53`, `AR`, `PTEN`). |
| entrez_ID   | INT         |       | NCBI Entrez Gene ID corresponding to the gene. May be 0 if not yet mapped to a hugo symbol in this databse project. |

---

## 4. Expression Tables

> Both expression tables share the same structure. Values are in FPKM (Fragments Per Kilobase of transcript per Million mapped reads). They differ only in library preparation method.

### `mrna_polya`

| Column   | Type          | PK/FK          | Description                                                                                                 |
|----------|---------------|----------------|-------------------------------------------------------------------------------------------------------------|
| polya_ID | INT           | PK             | Auto-incremented surrogate key for this mRNA polyA expression entry.                                       |
| sampleID | INT           | FK → Sample    | Foreign key to `Sample.sample_ID`. The sample in which expression was measured.                            |
| geneID   | INT           | FK → geneInfo  | Foreign key to `geneInfo.geneID`. The gene whose expression is recorded.                                   |
| fpkm     | DECIMAL(12,4) |                | Gene expression level in FPKM as measured by polyA-selected RNA-seq library preparation. Sourced from the polyA expression data file. |

---

### `mrna_capture`

| Column     | Type          | PK/FK          | Description                                                                                                     |
|------------|---------------|----------------|-----------------------------------------------------------------------------------------------------------------|
| capture_ID | INT           | PK             | Auto-incremented surrogate key for this mRNA capture expression entry.                                         |
| sampleID   | INT           | FK → Sample    | Foreign key to `Sample.sample_ID`. The sample in which expression was measured.                                |
| geneID     | INT           | FK → geneInfo  | Foreign key to `geneInfo.geneID`. The gene whose expression is recorded.                                       |
| fpkm       | DECIMAL(12,4) |                | Gene expression level in FPKM as measured by capture-based RNA-seq library preparation. Sourced from the capture expression data file. |

---

## 5. Copy Number Alteration

### `CNA`

| Column      | Type    | PK/FK          | Description                                                                                                                          |
|-------------|---------|----------------|--------------------------------------------------------------------------------------------------------------------------------------|
| CNA_entryID | INT     | PK             | Auto-incremented surrogate key for this CNA record.                                                                                 |
| sampleID    | INT     | FK → Sample    | Foreign key to `Sample.sample_ID`. The sample in which the CNA was detected.                                                        |
| geneID      | INT     | FK → geneInfo  | Foreign key to `geneInfo.geneID`. The gene affected by the copy number alteration.                                                  |
| CNA         | TINYINT |                | Discrete copy number alteration value (signed integer). Typical values:  -2 = homozygous deletion; -1 = hemizygous deletion; 0 = neutral / no change; 1 = gain; 2 = high level amplification.|

---

## 6. Variant Tables

### `variant` (with reference to NCBI build GRCh37)

| Column                 | Type        | PK/FK | Description                                                                                                                           |
|------------------------|-------------|-------|---------------------------------------------------------------------------------------------------------------------------------------|
| variantID              | INT         | PK    | Auto-incremented surrogate key for the variant record.                                                                               |
| reference_allele       | VARCHAR(50) |       | Reference genome allele at this position (e.g., `A`, `GCTA`). Sourced from the MAF file `Reference_Allele` column.                   |
| chromosome             | CHAR(2)     |       | Chromosome on which the variant is located (e.g., `1`, `X`, `MT`). Sourced from MAF `Chromosome`.                                   |
| stat_pos               | INT         |       | Start position of the variant on the chromosome (1-based genomic coordinate). Sourced from MAF `Start_Position`.                     |
| end_pos                | INT         |       | End position of the variant on the chromosome (1-based). For SNVs, equals `stat_pos`. Sourced from MAF `End_Position`.               |
| alt_allele             | VARCHAR(50) |       | Alternate (mutant) allele observed in the tumor (e.g., `T`, `–`). Sourced from MAF `Tumor_Seq_Allele2`.                              |
| dbSNPid                | VARCHAR(11) |       | dbSNP rsID if the variant is a known polymorphism (e.g., `rs12345678`). NULL if novel. Sourced from MAF `dbSNP_RS`.                  |
| variantClassificationID | TINYINT | FK → variantClassification| Foreign key to variantClassification.variantClassificationID. Functional classification of the variant (e.g., Missense_Mutation, Nonsense_Mutation, Frame_Shift_Del, Silent). |
| variantTypeID          | TINYINT    | FK → variantType |Foreign key to variantType.variantTypeID. Molecular type of the variant (SNP, INS, DEL). Sourced from MAF Variant_Type. |
| hgvsp_short            | VARCHAR(25) |       | Short-form HGVS protein-level notation for the amino acid change (e.g., `p.V600E`). NULL for synonymous or non-coding variants. Sourced from MAF `HGVSp_Short`. |


---

### `observation`

| Column        | Type | PK/FK             | Description                                                                                     |
|---------------|------|-------------------|-------------------------------------------------------------------------------------------------|
| observationID | INT  | PK                | Auto-incremented surrogate key for this variant observation.                                   |
| sampleID      | INT  | FK → Sample       | Foreign key to `Sample.sample_ID`. The sample in which the variant was observed.               |
| variantID     | INT  | FK → variant      | Foreign key to `variant.variantID`. The specific variant that was detected.                    |
| gene_ID       | INT  | FK → geneInfo     | Foreign key to `geneInfo.geneID`. The gene in which the variant is located. May be NULL for intergenic variants. |

---
