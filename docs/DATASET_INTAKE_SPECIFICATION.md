# Dataset Intake Module Specification

## Purpose

The Dataset Intake Module is responsible for rule-based discovery and selection of input files from a locally downloaded public transcriptomic dataset.

This module operates before the Data Cleaner.

Its goal is to help the user identify:

- expression matrix file
- metadata / labels / phenotype file

without requiring the user to manually inspect every file in a downloaded dataset folder.

The module must follow the main project principle:

**Rule-Based Cleaning with Transparent Reporting**

Therefore, every automatic file selection must be:

- based on explicit rules
- assigned a confidence level
- explained with human-readable reasons
- saved in an intake report
- possible to override manually by the user

---

## Scope

The Dataset Intake Module supports local datasets that have already been downloaded by the user.

Supported input sources in v1:

- local folder
- extracted dataset directory

Future development:

- ZIP archives
- TAR.GZ archives
- GEO API download
- TCGA API download

The module does not perform biological analysis and does not clean expression values. It only identifies candidate input files.

---

## Position in the Workflow

Recommended workflow:

1. User downloads a public dataset manually.
2. User provides a local dataset folder to the app.
3. Dataset Intake scans the folder.
4. Dataset Intake identifies candidate files.
5. Dataset Intake selects files automatically only if confidence is high.
6. If confidence is not high, the user selects files manually.
7. Selected files are passed to the Data Cleaner.
8. Data Cleaner performs rule-based cleaning, harmonization and QC.
9. Analysis Engine performs exploratory analysis.
10. Final PDF report summarizes the workflow and results.

---

## Responsibilities

The Dataset Intake Module should:

- scan a dataset folder recursively
- identify supported tabular files
- ignore obvious documentation or irrelevant files
- classify candidate files as expression_matrix, metadata, ignored or unknown
- calculate a score for each file
- assign confidence level: high, medium or low
- generate a report explaining decisions
- return selected expression and metadata files if automatic selection is safe

The module should not:

- download datasets from GEO or TCGA
- perform expression cleaning
- perform normalization
- perform differential expression analysis
- perform survival analysis
- modify original downloaded files

---

## Supported File Types

Dataset Intake v1 should inspect:

- CSV
- TSV
- TXT
- XLSX

Files may be skipped if they are too large for safe preview. In that case, the module should record the reason in the intake report.

---

## Candidate Roles

### expression_matrix

A file may be classified as an expression matrix candidate if it has:

- many numeric columns
- matrix-like shape
- likely sample or gene identifiers
- at least several rows and columns
- filename suggesting expression data

Possible filename keywords:

- expression
- expr
- counts
- count
- matrix
- data
- gene

Expected internal format after later harmonization:

- sample x gene
- first column: sample_id
- expression values numeric

The Dataset Intake Module does not need to guarantee final orientation. Orientation is handled later by the Data Cleaner / harmonization module.

---

### metadata

A file may be classified as a metadata candidate if it has:

- sample identifiers
- group-like or phenotype-like columns
- mostly categorical/textual columns
- row count compatible with the number of samples in the expression matrix
- filename suggesting labels, metadata or phenotype data

Possible filename keywords:

- metadata
- meta
- labels
- label
- phenotype
- pheno
- clinical
- samples
- sample
- classes
- annotation

Minimum required metadata after cleaning:

- sample_id
- group

Optional metadata columns:

- dataset
- subtype
- stage
- batch
- tissue

---

### ignored

A file may be classified as ignored if it appears to be:

- README
- license
- documentation
- platform annotation
- supplementary description
- image
- archive
- log
- unrelated text file

Possible filename keywords:

- readme
- license
- gpl
- platform
- annotation
- supplementary
- manifest

---

### unknown

A file should be classified as unknown if there is not enough evidence to assign a role.

Unknown files should not be auto-selected.

---

## Scoring Rules

Each inspected file receives separate scores for expression and metadata roles.

### Expression Matrix Score

Positive signals:

- supported tabular extension: +1
- filename contains expression/data/matrix/counts/gene keyword: +2
- file has more than 20 columns: +2
- file has more than 50 rows: +1
- more than 70 percent of non-identifier values are numeric: +3
- first column looks like gene or sample identifiers: +1
- matrix-like shape detected: +2

Negative signals:

- filename contains readme/license/platform/annotation: -3
- file has fewer than 3 columns: -2
- values are mostly text: -3
- file appears to be metadata-like: -2

---

### Metadata Score

Positive signals:

- supported tabular extension: +1
- filename contains metadata/labels/phenotype/clinical/sample keyword: +2
- contains sample-like column: +3
- contains group-like column: +3
- row count is compatible with selected expression matrix sample count: +3
- contains mostly categorical/text columns: +1

Negative signals:

- has hundreds or thousands of numeric columns: -4
- appears to be expression-matrix-like: -3
- filename contains readme/license/platform: -3

---

## Confidence Levels

Suggested confidence thresholds:

- high: score >= 7
- medium: score between 4 and 6
- low: score between 1 and 3
- ignored/unknown: score <= 0 or conflicting evidence

Automatic selection is allowed only when:

- exactly one high-confidence expression matrix candidate exists
- exactly one high-confidence metadata candidate exists
- the metadata file is compatible with the expression matrix
- no conflicting high-confidence candidate exists

If multiple candidates have similar high scores, the user must choose manually.

---

## Compatibility Checks

After candidate detection, the module should check whether expression and metadata files are compatible.

Possible checks:

- metadata row count matches expression sample count
- metadata sample identifiers overlap with expression sample identifiers
- labels/classes count matches number of expression samples
- metadata contains or can be mapped to sample_id
- metadata contains or can be mapped to group

Compatibility evidence should be recorded in the intake report.

---

## Required Outputs

### dataset_intake_report.csv

This file records all inspected files and decisions.

Required columns:

- file_path
- file_name
- file_type
- predicted_role
- expression_score
- metadata_score
- confidence
- selected
- reasons
- warnings

Example:

file_path,file_name,file_type,predicted_role,expression_score,metadata_score,confidence,selected,reasons,warnings
data.csv,data.csv,csv,expression_matrix,9,1,high,yes,"many numeric columns; filename contains data; matrix-like shape",""
labels.csv,labels.csv,csv,metadata,1,8,high,yes,"filename contains labels; row count matches expression matrix",""
README.txt,README.txt,txt,ignored,-2,-2,low,no,"documentation-like filename",""

---

### selected_input_files.csv

This file records the final selected files.

Required columns:

- role
- file_path
- selection_status
- confidence
- reason

Example:

role,file_path,selection_status,confidence,reason
expression_matrix,data.csv,auto_selected,high,"highest confidence expression matrix candidate"
metadata,labels.csv,auto_selected,high,"highest confidence metadata candidate compatible with expression matrix"

Possible selection statuses:

- auto_selected
- user_selected
- not_selected
- requires_review

---

## Streamlit Integration

A future Streamlit section may be added before manual upload:

0. Dataset Intake

Possible interface:

1. User enters or selects local dataset folder.
2. App scans the folder.
3. App displays a table of detected files.
4. App shows automatically selected candidates if confidence is high.
5. App allows manual override.
6. Selected files are passed to the existing Data Cleaner workflow.

The existing manual upload workflow should remain available.

---

## Reporting Integration

The final PDF report may include a short summary:

Input files were selected using rule-based dataset intake.
Expression matrix: data.csv
Metadata file: labels.csv
Selection mode: auto_selected
Reason: high-confidence candidates with compatible sample counts.

The full dataset_intake_report.csv should be saved as an output artifact.

---

## Auditability Requirements

Every automatic file selection must answer:

1. What was detected?
2. What was selected?
3. Why was it selected?

If the module cannot answer these questions clearly, automatic selection must not be performed.

---

## MVP v1 Implementation Plan

### Phase 1

- create src/dataset_intake/file_discovery.py
- scan local folder
- list supported files
- calculate basic file statistics
- classify files using simple rules
- generate dataset_intake_report.csv

### Phase 2

- add automatic selection for high-confidence cases
- generate selected_input_files.csv
- add unit tests

### Phase 3

- integrate with Streamlit as optional workflow
- keep manual upload workflow unchanged

### Phase 4

- include intake summary in final PDF report

---

## Out of Scope for v1

The following features are not part of Dataset Intake v1:

- automatic GEO download
- automatic TCGA download
- FASTQ/BAM processing
- normalization
- differential expression analysis
- pathway analysis
- survival analysis
- machine learning
- automatic biological interpretation of dataset purpose

---

## Design Principle

The Dataset Intake Module should be conservative.

It is better to ask the user to confirm file selection than to silently choose the wrong files.

Automatic selection is allowed only when the evidence is strong and transparent.
