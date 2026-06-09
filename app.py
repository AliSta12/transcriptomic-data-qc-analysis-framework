from src.analysis_engine.analysis_engine_pipeline import AnalysisEnginePipeline
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_cleaner.data_cleaner_pipeline import DataCleanerPipeline


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
            cleaner = DataCleanerPipeline()
            result = cleaner.run(
                expression_df=expression_df,
                metadata_df=metadata_df,
            )

            st.session_state["cleaner_result"] = result

            st.success(
                f"Data Cleaner finished successfully. "
                f"Final status: {result.final_status}"
            )

        except Exception as error:
            st.error("Data Cleaner failed.")
            st.exception(error)


if "cleaner_result" in st.session_state:
    result = st.session_state["cleaner_result"]

    st.header("3. Data Cleaner results")

    st.subheader("Data readiness report")
    st.dataframe(result.data_readiness_report)

    st.subheader("Data quality report")
    st.dataframe(result.data_quality_report)

    st.subheader("Harmonization report")
    st.dataframe(result.harmonization_report)

    st.subheader("Audit log")
    st.dataframe(result.audit_log)

    st.subheader("Cleaned expression matrix preview")
    st.dataframe(result.cleaned_expression_matrix.head())

    st.subheader("Clean metadata preview")
    st.dataframe(result.clean_metadata.head())
if "cleaner_result" in st.session_state:

    result = st.session_state["cleaner_result"]

    st.header("4. Analysis Engine")

    if st.button("Run Analysis Engine"):

        try:

            output_directory = "outputs/streamlit_demo"

            analysis_result = AnalysisEnginePipeline().run(
                expression_df=result.cleaned_expression_matrix,
                metadata_df=result.clean_metadata,
                output_directory=output_directory,
            )

            st.session_state["analysis_result"] = analysis_result

            st.success(
                "Analysis Engine finished successfully."
            )

        except Exception as error:
            st.error("Analysis Engine failed.")
            st.exception(error)


if "analysis_result" in st.session_state:

    analysis = st.session_state["analysis_result"]

    st.header("5. Analysis Results")

    st.subheader("Dataset Overview")
    st.dataframe(
        analysis.dataset_overview.summary_dataframe
    )

    st.subheader("Class Distribution")
    st.image(
        analysis.class_distribution.plot_path
    )

    st.subheader("PCA")
    st.image(
        analysis.pca_analysis.plot_path
    )

    st.subheader("Top Variable Genes")
    st.image(
        analysis.variable_gene_analysis.barplot_path
    )

    st.subheader("Heatmap")
    st.image(
        analysis.heatmap.plot_path
    )

    st.subheader("Sample Clustering")
    st.image(
        analysis.sample_clustering.plot_path
    )

    st.subheader("Analysis Summary")
    st.dataframe(
        analysis.analysis_summary.summary_dataframe
    )
