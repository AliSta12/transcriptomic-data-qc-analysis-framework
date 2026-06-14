import time

from src.analysis_engine.analysis_engine_pipeline import AnalysisEnginePipeline
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_cleaner.data_cleaner_pipeline import DataCleanerPipeline
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

if not use_demo_dataset:
    expression_file = st.file_uploader(
        "Upload expression matrix",
        type=["csv", "tsv", "xlsx"],
    )

    metadata_file = st.file_uploader(
        "Upload metadata file",
        type=["csv", "tsv", "xlsx"],
    )
else:
    st.info(
        "Prepared GEO demo dataset selected: "
        "data/processed/geo_gse15852/expression_matrix.tsv and metadata.tsv"
    )

input_files_available = (
    use_demo_dataset
    or (
        expression_file is not None
        and metadata_file is not None
    )
)

if input_files_available:
    if use_demo_dataset:
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
            if use_demo_dataset:
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

        if use_demo_dataset:
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
