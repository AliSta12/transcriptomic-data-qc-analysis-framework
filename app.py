import time

from src.analysis_engine.analysis_engine_pipeline import AnalysisEnginePipeline
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_cleaner.data_cleaner_pipeline import DataCleanerPipeline
from src.dataset_intake.file_discovery import run_dataset_intake
from src.reporting.final_analysis_report_generator import FinalAnalysisReportGenerator

st.set_page_config(
    page_title="Transcriptomic Data QC & Analysis Framework",
    layout="wide",
)

st.title("Transcriptomic Data QC & Analysis Framework")

st.markdown(
    """
    Rule-based cleaning, harmonization and quality control
    of transcriptomic expression datasets.
    """
)


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if filename.endswith(".tsv"):
        return pd.read_csv(uploaded_file, sep="\t")

    if filename.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)

    raise ValueError("Unsupported file format.")


def read_local_table_file(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)
    filename = path.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(path)

    if filename.endswith(".csv.gz"):
        return pd.read_csv(path, compression="gzip")

    if filename.endswith(".tsv"):
        return pd.read_csv(path, sep="\t")

    if filename.endswith(".tsv.gz"):
        return pd.read_csv(path, sep="\t", compression="gzip")

    if filename.endswith(".xlsx"):
        return pd.read_excel(path)

    raise ValueError(f"Unsupported file format selected by Dataset Intake: {path.name}")


st.header("0. Dataset Intake")

st.caption(
    "Optional rule-based scan of a locally downloaded public dataset folder. "
    "This step helps identify candidate expression and metadata files before manual upload."
)

with st.expander("Run Dataset Intake on a local dataset folder", expanded=False):
    dataset_directory = st.text_input(
        "Local dataset folder",
        value="data/raw/pancan/TCGA-PANCAN-HiSeq-801x20531",
        help=(
            "Provide a local folder containing files from a downloaded public dataset. "
            "The app will scan supported tabular files and report candidate input files."
        ),
    )

    intake_output_directory = st.text_input(
        "Dataset Intake output directory",
        value="outputs/streamlit_dataset_intake",
    )

    if st.button("Run Dataset Intake"):
        try:
            start_time = time.time()

            with st.spinner("Scanning dataset folder with rule-based Dataset Intake..."):
                intake_result = run_dataset_intake(
                    dataset_directory=dataset_directory,
                    output_directory=intake_output_directory,
                )

            elapsed_time = time.time() - start_time

            st.session_state["dataset_intake_result"] = intake_result

            st.success(
                f"Dataset Intake completed successfully in {elapsed_time:.2f} seconds."
            )

        except Exception as error:
            st.error("Dataset Intake failed.")
            st.exception(error)

    if "dataset_intake_result" in st.session_state:
        intake_result = st.session_state["dataset_intake_result"]
        selected_files = intake_result["selected_files"]
        discovery_report = intake_result["discovery_report"]

        auto_selected_count = (
            selected_files["selection_status"]
            .eq("auto_selected")
            .sum()
        )

        if auto_selected_count == 2:
            st.success(
                "Dataset Intake found one high-confidence expression matrix "
                "and one high-confidence metadata file."
            )
        else:
            st.warning(
                "Dataset Intake could not safely auto-select all required files. "
                "Manual review is required."
            )

        st.subheader("Selected Input Files")
        st.caption(
            "Automatic selection is performed only when high-confidence candidates are unique. "
            "These files are not passed to the Data Cleaner automatically yet."
        )

        selected_display = selected_files.copy()
        selected_display["file_name"] = selected_display["file_path"].apply(
            lambda value: Path(value).name if value else ""
        )

        st.dataframe(
            selected_display[
                [
                    "role",
                    "file_name",
                    "selection_status",
                    "confidence",
                    "reason",
                ]
            ],
            width="stretch",
        )

        if auto_selected_count == 2:
            if st.button("Use selected files for Data Cleaner"):
                expression_row = selected_files[
                    selected_files["role"] == "expression_matrix"
                ].iloc[0]
                metadata_row = selected_files[
                    selected_files["role"] == "metadata"
                ].iloc[0]

                st.session_state["use_dataset_intake_files"] = True
                st.session_state["dataset_intake_expression_path"] = expression_row["file_path"]
                st.session_state["dataset_intake_metadata_path"] = metadata_row["file_path"]

                st.session_state.pop("cleaner_result", None)
                st.session_state.pop("analysis_result", None)
                st.session_state.pop("uploaded_files_signature", None)

                st.success(
                    "Selected Dataset Intake files will be used in the Data Cleaner section."
                )
        else:
            st.info(
                "Dataset Intake did not auto-select both required files. "
                "Please use manual upload or review the detected files."
            )

            if st.button("Go to Input Review"):
                st.session_state["show_input_review"] = True
                st.session_state["input_review_source"] = "Dataset Intake"
                st.session_state["input_review_message"] = (
                    "Dataset Intake could not safely auto-select both required input files. "
                    "The dataset needs manual review before it can be cleaned and analyzed."
                )
                st.success(
                    "Input Review guidance is now available below the Dataset Intake section."
                )

        with st.expander("Show detailed Dataset Intake discovery report", expanded=False):
            st.caption(
                "Full audit-style report with file scores, preview statistics, "
                "classification reasons and warnings."
            )

            if discovery_report.empty:
                st.info(
                    "No supported tabular files were detected in the selected folder."
                )
            else:
                discovery_display = discovery_report.copy()
                discovery_display["file_path"] = discovery_display["file_path"].apply(
                    lambda value: Path(value).name
                )

                st.dataframe(
                    discovery_display,
                    width="stretch",
                )

        st.caption(
            "Saved outputs: "
            f"{intake_result['output_paths']['dataset_intake_report']} and "
            f"{intake_result['output_paths']['selected_input_files']}"
        )

if st.session_state.get("show_input_review", False):
    st.header("Input Review & Repair Guidance")

    st.warning(
        st.session_state.get(
            "input_review_message",
            "Manual review is required before continuing.",
        )
    )

    st.markdown(
        """
        This section explains what the user should check manually when the app
        cannot safely prepare the dataset using explicit rules.
        """
    )

    st.subheader("What was detected?")

    if "dataset_intake_result" in st.session_state:
        selected_files = st.session_state["dataset_intake_result"]["selected_files"].copy()

        selected_files["file_name"] = selected_files["file_path"].apply(
            lambda value: Path(value).name if value else ""
        )

        st.dataframe(
            selected_files[
                [
                    "role",
                    "file_name",
                    "selection_status",
                    "confidence",
                    "reason",
                ]
            ],
            width="stretch",
        )
    else:
        st.info("No Dataset Intake result is currently available.")

    st.subheader("Recommended manual checks")

    st.markdown(
        """
        Before uploading corrected files, check that:

        - the expression matrix file contains samples and gene expression values,
        - the metadata file contains at least `sample_id` and `group`,
        - `sample_id` values match between expression data and metadata,
        - expression values are numeric,
        - files are saved as CSV, TSV or XLSX,
        - the expression matrix can be harmonized to the internal format: sample × gene.
        """
    )

    st.subheader("Recommended next action")

    st.info(
        "Open the candidate files locally, correct the structure if needed, "
        "save the corrected files, and upload them manually in section 1."
    )

    if st.button("Hide Input Review"):
        st.session_state["show_input_review"] = False
        st.rerun()


st.header("1. Upload input files")

st.info(
    """
    Upload a gene expression matrix and metadata file.

    Requirements:
    - expression matrix: CSV, TSV or XLSX
    - metadata file: must contain `sample_id` and `group` columns
    - internal format after harmonization: sample × gene

    This app works with processed expression matrices, not FASTQ or BAM files.
    """
)

use_intake_files = st.session_state.get("use_dataset_intake_files", False)

if use_intake_files:
    st.info(
        "Using files selected by Dataset Intake. "
        "You can clear this selection to return to manual upload or demo dataset."
    )

    col_clear_intake, _ = st.columns([1, 3])
    with col_clear_intake:
        if st.button("Clear Dataset Intake selection"):
            st.session_state["use_dataset_intake_files"] = False
            st.session_state.pop("dataset_intake_expression_path", None)
            st.session_state.pop("dataset_intake_metadata_path", None)
            st.session_state.pop("uploaded_files_signature", None)
            st.rerun()

use_demo_dataset = False

if not use_intake_files:
    use_demo_dataset = st.checkbox(
        "Use prepared GEO demo dataset",
        value=False,
        help=(
            "Loads the processed GEO GSE15852 expression matrix and metadata "
            "from the local data/processed directory."
        ),
    )

expression_file = None
metadata_file = None

if not use_intake_files and not use_demo_dataset:
    expression_file = st.file_uploader(
        "Upload expression matrix",
        type=["csv", "tsv", "xlsx"],
    )

    metadata_file = st.file_uploader(
        "Upload metadata file",
        type=["csv", "tsv", "xlsx"],
    )
elif use_demo_dataset:
    st.info(
        "Prepared GEO demo dataset selected: "
        "data/processed/geo_gse15852/expression_matrix.tsv and metadata.tsv"
    )

input_files_available = (
    use_intake_files
    or use_demo_dataset
    or (
        expression_file is not None
        and metadata_file is not None
    )
)

if input_files_available:
    if use_intake_files:
        intake_expression_path = Path(
            st.session_state["dataset_intake_expression_path"]
        )
        intake_metadata_path = Path(
            st.session_state["dataset_intake_metadata_path"]
        )

        uploaded_files_signature = (
            "dataset_intake",
            str(intake_expression_path),
            intake_expression_path.stat().st_size,
            str(intake_metadata_path),
            intake_metadata_path.stat().st_size,
        )
    elif use_demo_dataset:
        demo_expression_path = Path(
            "data/processed/geo_gse15852/expression_matrix.tsv"
        )
        demo_metadata_path = Path(
            "data/processed/geo_gse15852/metadata.tsv"
        )

        uploaded_files_signature = (
            "demo_geo_gse15852",
            str(demo_expression_path),
            demo_expression_path.stat().st_size,
            str(demo_metadata_path),
            demo_metadata_path.stat().st_size,
        )
    else:
        uploaded_files_signature = (
            expression_file.name,
            expression_file.size,
            metadata_file.name,
            metadata_file.size,
        )

    files_changed = (
        st.session_state.get("uploaded_files_signature")
        != uploaded_files_signature
    )

    if files_changed:
        start_time = time.time()

        with st.spinner("Reading input files..."):
            if use_intake_files:
                expression_df = read_local_table_file(intake_expression_path)
                metadata_df = read_local_table_file(intake_metadata_path)
            elif use_demo_dataset:
                expression_df = pd.read_csv(
                    demo_expression_path,
                    sep="\t",
                )
                metadata_df = pd.read_csv(
                    demo_metadata_path,
                    sep="\t",
                )
            else:
                expression_df = read_uploaded_file(expression_file)
                metadata_df = read_uploaded_file(metadata_file)

        elapsed_time = time.time() - start_time

        st.session_state["uploaded_files_signature"] = uploaded_files_signature
        st.session_state["expression_df"] = expression_df
        st.session_state["metadata_df"] = metadata_df
        st.session_state["raw_preview_load_time"] = elapsed_time

        if use_intake_files:
            st.session_state["dataset_name"] = intake_expression_path.name
        elif use_demo_dataset:
            st.session_state["dataset_name"] = "GEO GSE15852 Demo Dataset"
        else:
            st.session_state["dataset_name"] = expression_file.name

        st.session_state.pop("cleaner_result", None)
        st.session_state.pop("analysis_result", None)

    expression_df = st.session_state["expression_df"]
    metadata_df = st.session_state["metadata_df"]

    st.success(
        "Input files are ready for preview "
        f"({st.session_state['raw_preview_load_time']:.2f} seconds)."
    )

    st.subheader("Input preview")
    st.caption(
        "Preview shows raw uploaded files before rule-based cleaning and harmonization."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.write("Raw expression matrix")
        st.dataframe(
            expression_df.head(),
            width="stretch",
        )

    with col2:
        st.write("Raw metadata")
        st.dataframe(
            metadata_df.head(),
            width="stretch",
        )

    st.header("2. Run Data Cleaner")

    if st.button("Run Data Cleaner"):
        try:
            start_time = time.time()

            with st.spinner("Running rule-based cleaning and QC..."):
                cleaner = DataCleanerPipeline()
                result = cleaner.run(
                    expression_df=expression_df,
                    metadata_df=metadata_df,
                )

            elapsed_time = time.time() - start_time

            st.session_state["cleaner_result"] = result
            st.session_state.pop("analysis_result", None)

            st.success(
                f"Data Cleaner finished successfully in {elapsed_time:.2f} seconds. "
                f"Final status: {result.final_status}"
            )

        except Exception as error:
            st.error("Data Cleaner failed.")
            st.exception(error)


if "cleaner_result" in st.session_state:
    result = st.session_state["cleaner_result"]

    st.header("3. Data Cleaner results")

    with st.expander("Data readiness report", expanded=True):
        readiness_status = result.data_readiness_report["overall_status"].iloc[0]

        if readiness_status == "READY_FOR_ANALYSIS":
            st.success("Dataset is ready for exploratory analysis.")
        elif readiness_status == "READY_WITH_WARNINGS":
            st.warning(
                "Dataset is ready for exploratory analysis, but warnings should be reviewed."
            )
        else:
            st.error(
                "Dataset requires review before exploratory analysis."
            )

        st.dataframe(
            result.data_readiness_report,
            width="stretch",
        )

    with st.expander("Data quality report"):
        st.caption(
            "QC statuses summarize detected issues. "
            "WARNING means that the dataset can still be analyzed, but the issue should be reviewed in the report."
        )
        st.dataframe(
            result.data_quality_report,
            width="stretch",
        )

    with st.expander("Harmonization report"):
        st.caption(
            "This report documents structural changes applied before analysis, "
            "including data orientation and standardized column names."
        )
        st.dataframe(
            result.harmonization_report,
            width="stretch",
        )

    with st.expander("Audit log"):
        st.caption(
            "The audit log records automatic rule-based decisions made by the Data Cleaner, "
            "including the detected issue, applied rule, decision, status and reason."
        )
        st.dataframe(
            result.audit_log,
            width="stretch",
        )

    with st.expander("Cleaned expression matrix preview"):
        st.caption(
            "Preview of the harmonized expression matrix in sample × gene format. "
            "Only the first rows are displayed."
        )
        st.dataframe(
            result.cleaned_expression_matrix.head(),
            width="stretch",
        )

    with st.expander("Clean metadata preview"):
        st.caption(
            "Preview of standardized metadata after column harmonization. "
            "If the input metadata does not contain a dataset column, the value is set to 'unknown'."
        )
        st.dataframe(
            result.clean_metadata.head(),
            width="stretch",
        )

if "cleaner_result" in st.session_state:

    result = st.session_state["cleaner_result"]

    st.header("4. Analysis Engine")

    if st.button("Run Analysis Engine"):

        try:
            start_time = time.time()

            output_directory = "outputs/streamlit_demo"

            with st.spinner("Running exploratory transcriptomic analysis..."):
                analysis_result = AnalysisEnginePipeline().run(
                    expression_df=result.cleaned_expression_matrix,
                    metadata_df=result.clean_metadata,
                    output_directory=output_directory,
                )

            elapsed_time = time.time() - start_time

            st.session_state["analysis_result"] = analysis_result

            st.success(
                f"Analysis Engine finished successfully in {elapsed_time:.2f} seconds."
            )

        except Exception as error:
            st.error("Analysis Engine failed.")
            st.exception(error)


if "analysis_result" in st.session_state:

    analysis = st.session_state["analysis_result"]

    st.header("5. Analysis Results")
    st.success(
        "Exploratory transcriptomic analysis results are available below."
    )
    (
        overview_tab,
        class_tab,
        pca_tab,
        variable_genes_tab,
        heatmap_tab,
        clustering_tab,
        summary_tab,
    ) = st.tabs(
        [
            "Overview",
            "Class Distribution",
            "PCA",
            "Variable Genes",
            "Heatmap",
            "Clustering",
            "Summary",
        ]
    )

    with overview_tab:
        st.subheader("Dataset Overview")
        st.caption(
            "Summary of the cleaned dataset used by the Analysis Engine."
        )
        st.dataframe(
            analysis.dataset_overview.summary_dataframe,
            width="stretch",
        )

    with class_tab:
        st.subheader("Class Distribution")
        st.caption(
            "Shows the number and percentage of samples in each biological group. "
            "This helps assess class balance before interpreting PCA and clustering."
        )
        st.image(
            analysis.class_distribution.plot_path,
            width="stretch",
        )

    with pca_tab:
        st.subheader("PCA")
        st.caption(
            "PCA visualizes sample-level variation in the cleaned expression matrix. "
            "Points represent samples and colors represent metadata groups. "
            "This is an exploratory visualization, not a formal differential expression analysis."
        )
        st.image(
            analysis.pca_analysis.plot_path,
            width="stretch",
        )

    with variable_genes_tab:
        st.subheader("Top Variable Genes")
        st.caption(
            "Shows the top 50 genes ranked by expression variance across samples. "
            "This ranking is exploratory and is used for visualization, not formal differential expression analysis."
        )
        st.image(
            analysis.variable_gene_analysis.barplot_path,
            width="stretch",
        )

    with heatmap_tab:
        st.subheader("Heatmap")
        st.caption(
            "Heatmap of the top 50 most variable genes across samples. "
            "For large datasets, sample labels are hidden to keep the visualization readable."
        )
        st.image(
            analysis.heatmap.plot_path,
            width="stretch",
        )

    with clustering_tab:
        st.subheader("Sample Clustering")
        st.caption(
            "Hierarchical clustering visualizes similarity between samples based on the cleaned expression matrix. "
            "For large datasets, sample labels are hidden to avoid an unreadable plot."
        )
        st.image(
            analysis.sample_clustering.plot_path,
            width="stretch",
        )

    with summary_tab:
        st.subheader("Analysis Summary")
        st.caption(
            "Concise summary of exploratory analysis outputs generated from the cleaned dataset."
        )
        st.dataframe(
            analysis.analysis_summary.summary_dataframe,
            width="stretch",
        )

    st.header("6. Final PDF Report")

    st.caption(
        "Generate a final report containing data quality assessment, "
        "cleaning and harmonization summary, exploratory analysis results and visualizations."
    )

    if st.button("Generate final PDF report"):
        try:
            start_time = time.time()

            with st.spinner("Generating final PDF report..."):
                report_result = FinalAnalysisReportGenerator().generate(
                    cleaner_result=st.session_state["cleaner_result"],
                    analysis_result=st.session_state["analysis_result"],
                    dataset_name=st.session_state.get(
                        "dataset_name",
                        "Uploaded Dataset",
                    ),
                    output_directory="outputs/streamlit_demo",
                )

            elapsed_time = time.time() - start_time

            st.success(
                f"Final PDF report generated successfully in {elapsed_time:.2f} seconds."
            )

            with open(report_result.pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="Download final_report.pdf",
                    data=pdf_file,
                    file_name="final_report.pdf",
                    mime="application/pdf",
                )

        except Exception as error:
            st.error(
                "Final PDF report generation failed."
            )
            st.exception(error)
