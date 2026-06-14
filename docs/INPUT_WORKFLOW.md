# Input Workflow

This document describes how input data can enter the Transcriptomic Data QC & Analysis Framework.

The project follows the principle:

**Rule-Based Cleaning with Transparent Reporting**

The application should always make clear:

1. What was detected?
2. What was selected or changed?
3. Why was this decision made?
4. When is manual review required?

---

## 1. Manual Upload

The user can manually upload two files:

- expression matrix
- metadata file

This is the default and most direct workflow.

### Requirements

Expression matrix:

- CSV, TSV or XLSX
- contains gene expression values
- can be harmonized to the internal format: sample × gene
- expression values must be numeric after harmonization

Metadata file:

- CSV, TSV or XLSX
- must contain at least:
  - `sample_id`
  - `group`

Optional metadata columns include:

- `dataset`
- `subtype`
- `stage`
- `batch`
- `tissue`

---

## 2. Dataset Intake Auto-Selection

The user can provide a local folder containing a downloaded public dataset.

Dataset Intake scans supported tabular files and classifies candidate files using explicit rules.

Supported file types:

- `.csv`
- `.tsv`
- `.txt`
- `.xlsx`
- `.csv.gz`
- `.tsv.gz`
- `.txt.gz`

Dataset Intake tries to identify:

- expression matrix
- metadata file

Automatic selection is allowed only when:

- exactly one high-confidence expression matrix candidate is found
- exactly one high-confidence metadata candidate is found

If both files are auto-selected, the user can pass them to the Data Cleaner using the Streamlit button:

**Use selected files for Data Cleaner**

The files are not cleaned automatically. The user still has to run the Data Cleaner manually.

---

## 3. Manual Input Review Fallback

If Dataset Intake cannot safely identify both required files, the application stops the automatic path and requires manual review.

Examples:

- no supported tabular files were detected
- expression matrix candidate is missing
- metadata candidate is missing
- multiple high-confidence expression matrix candidates were found
- multiple high-confidence metadata candidates were found
- file format is mixed, ambiguous or not safely readable
- required metadata columns are missing
- sample identifiers need manual inspection

In this case, the application shows:

**Input Review & Repair Guidance**

The user should manually check the candidate files, correct them if needed, and then use the manual upload workflow.

---

## 4. Why manual review is important

The application should not guess silently.

If the rules are not sufficient to safely prepare the dataset, the system must make this visible to the user.

This protects the analysis from hidden assumptions and keeps the workflow transparent, reproducible and suitable for public transcriptomic datasets.

---

## 5. Current MVP boundary

Dataset Intake does not perform:

- automatic GEO API download
- automatic TCGA API download
- FASTQ or BAM processing
- normalization of raw sequencing reads
- differential expression analysis
- pathway analysis
- survival analysis
- machine learning

These features may be considered future development, but they are not part of the current MVP.
