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
    "Upload a gene expression matrix and metadata file. "
    "Metadata must contain sample_id and group columns. "
    "Supported formats: CSV, TSV and XLSX. "
    "This app works with processed expression matrices, not FASTQ or BAM files. "
    "After harmonization, the internal data format is sample × gene."
)

expression_file = st.file_uploader(
    "Upload expression matrix",
    type=["csv", "tsv", "xlsx"],
)

metadata_file = st.file_uploader(
    "Upload metadata file",
    type=["csv", "tsv", "xlsx"],
)

if expression_file is not None and metadata_file is not None:
    expression_df = read_uploaded_file(expression_file)
    metadata_df = read_uploaded_file(metadata_file)

    st.subheader("Input preview")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Expression matrix")
        st.dataframe(expression_df.head())

    with col2:
        st.write("Metadata")
        st.dataframe(metadata_df.head())

    st.header("2. Run Data Cleaner")

    if st.button("Run Data Cleaner"):
        try:
            start_time = time.time()

            with st.spinner("Running rule-based data cleaning and QC..."):
                cleaner = DataCleanerPipeline()
                result = cleaner.run(
                    expression_df=expression_df,
                    metadata_df=metadata_df,
                )

            elapsed_time = time.time() - start_time

            st.session_state["cleaner_result"] = result

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
        st.dataframe(result.data_readiness_report)

    with st.expander("Data quality report"):
        st.dataframe(result.data_quality_report)

    with st.expander("Harmonization report"):
        st.dataframe(result.harmonization_report)

    with st.expander("Audit log"):
        st.dataframe(result.audit_log)

    with st.expander("Cleaned expression matrix preview"):
        st.dataframe(result.cleaned_expression_matrix.head())

    with st.expander("Clean metadata preview"):
        st.dataframe(result.clean_metadata.head())


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
        st.dataframe(
            analysis.dataset_overview.summary_dataframe
        )

    with class_tab:
        st.subheader("Class Distribution")
        st.image(
            analysis.class_distribution.plot_path
        )

    with pca_tab:
        st.subheader("PCA")
        st.image(
            analysis.pca_analysis.plot_path
        )

    with variable_genes_tab:
        st.subheader("Top Variable Genes")
        st.image(
            analysis.variable_gene_analysis.barplot_path
        )

    with heatmap_tab:
        st.subheader("Heatmap")
        st.image(
            analysis.heatmap.plot_path
        )

    with clustering_tab:
        st.subheader("Sample Clustering")
        st.image(
            analysis.sample_clustering.plot_path
        )

    with summary_tab:
        st.subheader("Analysis Summary")
        st.dataframe(
            analysis.analysis_summary.summary_dataframe
        )

    st.header("6. Final PDF Report")

    if st.button("Generate final PDF report"):
        try:
            start_time = time.time()

            with st.spinner("Generating final PDF report..."):
                report_result = FinalAnalysisReportGenerator().generate(
                    cleaner_result=st.session_state["cleaner_result"],
                    analysis_result=st.session_state["analysis_result"],
                    dataset_name=expression_file.name,
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
