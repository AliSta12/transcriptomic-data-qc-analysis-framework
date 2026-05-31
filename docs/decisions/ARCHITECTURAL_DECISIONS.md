# ARCHITECTURAL_DECISIONS.md

# Transcriptomic Data QC & Analysis Framework

This document records the most important architectural decisions made during project planning.

---

## AD-001

### Internal Working Format

Decision:

All expression matrices are converted to:

sample × gene

Description:

* rows represent samples
* columns represent genes
* first column = sample_id

Reason:

This format is directly compatible with PCA, clustering, heatmaps and most Python analysis libraries.

Status:

Accepted

---

## AD-002

### Supported Data Sources

Decision:

The framework supports more than one public transcriptomic dataset.

Initial datasets:

* UCI PANCAN
* GEO expression dataset

Reason:

The project must demonstrate harmonization of heterogeneous transcriptomic datasets.

Status:

Accepted

---

## AD-003

### Rule-Based Data Cleaning

Decision:

Data Cleaner performs automated cleaning only when a predefined rule exists.

Reason:

All operations must be transparent, reproducible and explainable.

Status:

Accepted

---

## AD-004

### Transparent Reporting

Decision:

Every automatic action performed by the Data Cleaner must be documented.

Generated files:

* audit_log.csv
* harmonization_report.csv
* data_quality_report.csv
* data_readiness_report.csv

Reason:

Users must be able to verify what was changed and why.

Status:

Accepted

---

## AD-005

### Handling Missing Values

Decision:

Low levels of missing values may be imputed using gene median.

High levels of missing values trigger filtering or review.

Reason:

Small amounts of missing data can be safely handled in exploratory analysis.

Status:

Accepted

---

## AD-006

### Duplicate Genes

Decision:

Duplicate genes are aggregated using mean expression values when all duplicated gene expression values are numeric.

Otherwise, they are marked as REQUIRES REVIEW.

Reason:

Duplicate genes may bias exploratory analyses and visualizations.

Status:

Accepted

---

## AD-007

### Duplicate Samples

Decision:

Duplicate samples are not removed automatically.

They are marked as:

REQUIRES REVIEW

Reason:

A duplicate sample may represent either a data error or a valid technical replicate.

Status:

Accepted

---

## AD-008

### Analysis Scope

Decision:

The MVP includes exploratory transcriptomic analysis only.

Not included:

* DESeq2
* edgeR
* limma
* GSEA
* pathway analysis
* survival analysis
* machine learning

Reason:

The project focuses on data preparation, quality control and exploratory analysis.

Status:

Accepted

---

## AD-009

### User Interface

Decision:

The framework uses Streamlit as the graphical user interface.

Reason:

Rapid development and easy demonstration during project presentation.

Status:

Accepted
