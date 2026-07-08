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

    if filename.endswith(".txt"):
        return pd.read_csv(path, sep=None, engine="python")

    if filename.endswith(".txt.gz"):
        return pd.read_csv(
            path,
            sep=None,
            engine="python",
            compression="gzip",
        )

    if filename.endswith(".xlsx"):
        return pd.read_excel(path)

    raise ValueError(f"Unsupported file format selected by Dataset Intake: {path.name}")


def normalize_local_folder_path(raw_path: str) -> Path:
    """
    Convert common Windows/WSL folder path formats to a path readable by Python
    running inside WSL/Linux.

    Supported examples:
    - data/raw/my_dataset
    - /home/alista/project/data/raw/my_dataset
    - C:\\Users\\Name\\dataset -> /mnt/c/Users/Name/dataset
    - \\\\wsl$\\Ubuntu\\home\\alista\\dataset -> /home/alista/dataset
    """
    cleaned_path = raw_path.strip().strip('"').strip("'")

    normalized_for_detection = cleaned_path.replace("/", "\\")

    if normalized_for_detection.lower().startswith("\\\\wsl$\\"):
        parts = normalized_for_detection.split("\\")
        if len(parts) >= 5:
            return Path("/" + "/".join(parts[4:]))

    if len(cleaned_path) >= 3 and cleaned_path[1] == ":" and cleaned_path[2] in {"\\", "/"}:
        drive_letter = cleaned_path[0].lower()
        path_without_drive = cleaned_path[3:].replace("\\", "/")
        return Path(f"/mnt/{drive_letter}/{path_without_drive}")

    return Path(cleaned_path).expanduser()


st.header("1. Select input files")

st.caption(
    "Provide one expression matrix and one metadata file. "
    "You can upload files manually or scan a local folder and let the app suggest candidate files."
)

current_use_intake_files = st.session_state.get("use_dataset_intake_files", False)

st.subheader("Choose input method")

selected_input_method = st.radio(
    "Choose input method",
    ["Manual upload", "Scan local folder"],
    index=1 if current_use_intake_files else 0,
    horizontal=True,
    label_visibility="collapsed",
)

if selected_input_method == "Manual upload" and current_use_intake_files:
    st.session_state["use_dataset_intake_files"] = False
    st.session_state.pop("dataset_intake_expression_path", None)
    st.session_state.pop("dataset_intake_metadata_path", None)
    st.session_state.pop("uploaded_files_signature", None)
    current_use_intake_files = False

st.subheader("Input requirements")

with st.expander("Show input requirements", expanded=False):
    if selected_input_method == "Manual upload":
        st.markdown(
            """
            Manual upload requires two files:

            - expression matrix: CSV, TSV or XLSX,
            - metadata file: CSV, TSV or XLSX,
            - metadata must contain `sample_id` and `group` columns,
            - expression values should be numeric.

            The app works with processed expression matrices, not FASTQ or BAM files.
            """
        )
    else:
        st.markdown(
            """
            Folder scan requires a local folder available to this Streamlit app.

            The folder should contain candidate tabular files:

            - expression matrix: CSV, TSV, TXT, XLSX or compressed CSV/TSV/TXT,
            - metadata file: CSV, TSV, TXT, XLSX or compressed CSV/TSV/TXT,
            - metadata must contain `sample_id` and `group` columns after harmonization.

            The scan suggests candidate files, but you must confirm them with
            **Use these files** before running the Data Cleaner.
            """
        )


if selected_input_method == "Scan local folder":
    dataset_directory = st.text_input(
        "Folder path on this computer",
        value="",
        placeholder="Example: data/raw/my_dataset_folder",
        help=(
            "Paste a local folder path. The app accepts Linux/WSL paths, relative "
            "project paths, Windows drive paths and \\\\wsl$ paths."
        ),
    )

    st.caption(
        "Paste a folder path visible to this app. Examples: "
        "`data/raw/my_dataset`, "
        "`/home/alista/.../data/raw/my_dataset`, "
        "`C:\\\\Users\\\\Name\\\\dataset`, "
        "or `\\\\wsl$\\\\Ubuntu\\\\home\\\\alista\\\\dataset`. "
        "The app will convert common Windows/WSL paths when possible."
    )

    if dataset_directory.strip():
        resolved_dataset_directory = normalize_local_folder_path(dataset_directory)
        st.caption(f"Resolved path used by the app: `{resolved_dataset_directory}`")

    intake_output_directory = "outputs/streamlit_dataset_intake"

    scan_button_disabled = not dataset_directory.strip()

    if scan_button_disabled:
        st.info("Enter a local folder path to enable folder scanning.")

    if st.button("Scan folder", disabled=scan_button_disabled):
        try:
            dataset_directory_path = normalize_local_folder_path(dataset_directory)

            if not dataset_directory_path.exists():
                raise FileNotFoundError(
                    f"Dataset folder does not exist: {dataset_directory_path}"
                )

            if not dataset_directory_path.is_dir():
                raise NotADirectoryError(
                    f"Selected path is not a folder: {dataset_directory_path}"
                )

            start_time = time.time()

            with st.spinner("Scanning dataset folder with rule-based Dataset Intake..."):
                intake_result = run_dataset_intake(
                    dataset_directory=dataset_directory_path,
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

        st.subheader("Files selected by scan")
        st.caption(
            "The scan selected these files because each required role had one "
            "high-confidence candidate. Review them before using them for cleaning."
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
            if st.button("Use these files"):
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
                    "These files are now selected for cleaning."
                )
        else:
            st.info(
                "Dataset Intake did not auto-select both required files. "
                "Please use manual upload or review the detected files. "
                "If this folder contains only a GEO series matrix file, preprocess it "
                "into separate expression and metadata tables before running the Data Cleaner."
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

    input_review_source = st.session_state.get("input_review_source", "Unknown")

    st.warning(
        st.session_state.get(
            "input_review_message",
            "Manual review is required before continuing.",
        )
    )

    if "last_cleaner_error" in st.session_state:
        st.subheader("Detected Data Cleaner issue")
        st.error(st.session_state["last_cleaner_error"])

    st.markdown(
        """
        This section explains what the user should check manually when the app
        cannot safely prepare the dataset using explicit rules.
        """
    )

    st.subheader("What was detected?")

    if input_review_source == "Data Cleaner":
        st.info(
            "The issue was detected while running the Data Cleaner on the selected "
            "input files. The files were loaded for preview, but they could not be "
            "processed using the available rule-based cleaning rules."
        )

    elif input_review_source == "Dataset Intake":
        if "dataset_intake_result" in st.session_state:
            selected_files = st.session_state["dataset_intake_result"][
                "selected_files"
            ].copy()

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

    else:
        st.info(
            "Manual review was activated, but the source of the issue was not specified."
        )

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

    if input_review_source == "Data Cleaner":
        st.info(
            "Correct the uploaded expression matrix or metadata file, then upload "
            "the corrected files again in section 1."
        )
    else:
        st.info(
            "Open the candidate files locally, correct the structure if needed, "
            "save the corrected files, and upload them manually in section 1."
        )

    if st.button("Hide Input Review"):
        st.session_state["show_input_review"] = False
        st.session_state.pop("last_cleaner_error", None)
        st.rerun()


use_intake_files = st.session_state.get("use_dataset_intake_files", False)

if use_intake_files:
    st.info(
        "Using files selected by folder scan. "
        "You can clear this selection to return to manual upload."
    )

    col_clear_intake, _ = st.columns([1, 3])
    with col_clear_intake:
        if st.button("Clear Dataset Intake selection"):
            st.session_state["use_dataset_intake_files"] = False
            st.session_state.pop("dataset_intake_expression_path", None)
            st.session_state.pop("dataset_intake_metadata_path", None)
            st.session_state.pop("uploaded_files_signature", None)
            st.session_state.pop("cleaner_result", None)
            st.session_state.pop("analysis_result", None)
            st.rerun()

expression_file = None
metadata_file = None

if not use_intake_files and selected_input_method == "Manual upload":
    expression_file = st.file_uploader(
        "Upload expression matrix",
        type=["csv", "tsv", "xlsx"],
    )

    metadata_file = st.file_uploader(
        "Upload metadata file",
        type=["csv", "tsv", "xlsx"],
    )
elif selected_input_method == "Scan local folder" and not use_intake_files:
    pass

input_files_available = (
    use_intake_files
    or (
        expression_file is not None
        and metadata_file is not None
    )
)

if not input_files_available:
    st.subheader("Input status")

    if selected_input_method == "Manual upload":
        st.info(
            "No input files are selected yet. Upload one expression matrix and one "
            "metadata file to continue."
        )
    else:
        st.info(
            "No input files are selected yet. Scan a local folder, review the detected "
            "candidate files, and then click 'Use these files'."
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
        else:
            st.session_state["dataset_name"] = expression_file.name

        dataset_display_name = st.session_state["dataset_name"]

        generic_expression_file_names = {
            "expression_matrix.csv",
            "expression_matrix.tsv",
            "expression_matrix.xlsx",
        }

        if dataset_display_name.lower() in generic_expression_file_names:
            if "dataset" in metadata_df.columns:
                dataset_values = (
                    metadata_df["dataset"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .unique()
                    .tolist()
                )

                if len(dataset_values) == 1 and dataset_values[0]:
                    dataset_display_name = (
                        f"{dataset_values[0]} analysis-ready dataset"
                    )
                else:
                    dataset_display_name = "Analysis-ready expression dataset"
            else:
                dataset_display_name = "Analysis-ready expression dataset"

        st.session_state["dataset_display_name"] = dataset_display_name

        st.session_state.pop("cleaner_result", None)
        st.session_state.pop("analysis_result", None)

    expression_df = st.session_state["expression_df"]
    metadata_df = st.session_state["metadata_df"]

    st.subheader("Current input selection")

    if use_intake_files:
        current_source = "Scan local folder"
        current_expression_name = Path(
            st.session_state["dataset_intake_expression_path"]
        ).name
        current_metadata_name = Path(
            st.session_state["dataset_intake_metadata_path"]
        ).name
    else:
        current_source = "Manual upload"
        current_expression_name = expression_file.name
        current_metadata_name = metadata_file.name

    st.info(
        f"Source: {current_source}\n\n"
        f"Expression matrix: {current_expression_name}\n\n"
        f"Metadata file: {current_metadata_name}\n\n"
        "Status: Ready for preview"
    )

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

    if st.session_state.get("show_input_review", False):
        st.warning(
            "Input Review is active. Review the guidance above, correct the input files, "
            "and then upload the corrected files again."
        )

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
            st.session_state["show_input_review"] = True
            st.session_state["input_review_source"] = "Data Cleaner"
            st.session_state["input_review_message"] = (
                "Data Cleaner failed while processing the selected input files. "
                "Please manually review the expression matrix and metadata structure."
            )
            st.session_state["last_cleaner_error"] = str(error)

            st.error("Data Cleaner failed.")
            st.exception(error)

            st.warning(
                "Input Review has been activated automatically because the input files "
                "could not be processed using the available rule-based cleaning rules. "
                "The page will reload and show the Input Review section above the upload area."
            )

            st.rerun()

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

            if st.button("Go to Input Review", key="go_to_input_review_after_not_ready"):
                st.session_state["show_input_review"] = True
                st.session_state["input_review_source"] = "Data Cleaner"
                st.session_state["input_review_message"] = (
                    "Data Cleaner completed, but the dataset is not ready for analysis. "
                    "Please review the readiness report, metadata columns, sample identifiers "
                    "and expression matrix structure."
                )
                st.rerun()

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

        st.markdown("#### QC decision summary")

        for _, row in result.data_quality_report.iterrows():
            status = row["status"]
            check = row["check"]
            metric = row["metric"]
            details = row["details"]

            if status == "PASS":
                st.success(f"{check} — PASS")
            elif status == "WARNING":
                st.warning(f"{check} — WARNING")
            elif status == "REQUIRES REVIEW":
                st.error(f"{check} — REQUIRES REVIEW")
            else:
                st.info(f"{check} — {status}")

            st.caption(f"Metric: {metric}")
            st.write(details)

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

    st.subheader("Download Data Cleaner outputs")
    st.caption(
        "Download harmonized data and transparent QC reports generated by the Data Cleaner."
    )

    cleaner_downloads = {
        "clean_expression_matrix.csv": (
            "Clean expression matrix",
            result.cleaned_expression_matrix,
        ),
        "clean_metadata.csv": (
            "Clean metadata",
            result.clean_metadata,
        ),
        "audit_log.csv": (
            "Audit log",
            result.audit_log,
        ),
        "harmonization_report.csv": (
            "Harmonization report",
            result.harmonization_report,
        ),
        "data_quality_report.csv": (
            "Data quality report",
            result.data_quality_report,
        ),
        "data_readiness_report.csv": (
            "Data readiness report",
            result.data_readiness_report,
        ),
    }

    cleaner_download_columns = st.columns(3)

    for index, (file_name, (button_label, dataframe)) in enumerate(
        cleaner_downloads.items()
    ):
        with cleaner_download_columns[index % 3]:
            st.download_button(
                label=button_label,
                data=dataframe.to_csv(index=False).encode("utf-8"),
                file_name=file_name,
                mime="text/csv",
                key=f"download_cleaner_{file_name}",
            )

if "cleaner_result" in st.session_state:

    result = st.session_state["cleaner_result"]

    st.header("4. Analysis Engine")

    expression_values = result.cleaned_expression_matrix.drop(
        columns=["sample_id"],
        errors="ignore",
    )
    remaining_missing_values = int(expression_values.isna().sum().sum())
    analysis_blocked = (
        result.final_status == "REQUIRES_REVIEW"
        or remaining_missing_values > 0
    )

    if analysis_blocked:
        st.session_state.pop("analysis_result", None)

        st.warning(
            "Exploratory analysis is disabled because the cleaned dataset still "
            "requires review or contains missing expression values."
        )

        st.caption(
            "Review the Data Cleaner reports and audit log before running PCA, "
            "heatmap generation and sample clustering. PCA cannot be computed "
            "when the expression matrix still contains missing values."
        )

        st.write(
            {
                "data_cleaner_final_status": result.final_status,
                "remaining_missing_expression_values": remaining_missing_values,
            }
        )

    if st.button("Run Analysis Engine", disabled=analysis_blocked):

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

    st.subheader("Download Analysis Engine outputs")
    st.caption(
        "Download exploratory analysis tables and visualizations generated from the cleaned dataset."
    )

    analysis_output_directory = Path("outputs/streamlit_demo")
    analysis_download_files = {
        "top_50_variable_genes.csv": "Top 50 variable genes",
        "top_100_variable_genes.csv": "Top 100 variable genes",
        "analysis_summary.csv": "Analysis summary CSV",
        "analysis_summary.md": "Analysis summary MD",
        "class_distribution.png": "Class distribution plot",
        "pca_plot.png": "PCA plot",
        "top_variable_genes_barplot.png": "Variable genes plot",
        "heatmap_top50_variable_genes.png": "Heatmap",
        "sample_clustering_dendrogram.png": "Sample clustering",
    }

    analysis_download_columns = st.columns(3)

    for index, (file_name, button_label) in enumerate(
        analysis_download_files.items()
    ):
        file_path = analysis_output_directory / file_name

        if not file_path.exists():
            continue

        if file_path.suffix == ".png":
            mime_type = "image/png"
        elif file_path.suffix == ".md":
            mime_type = "text/markdown"
        else:
            mime_type = "text/csv"

        with analysis_download_columns[index % 3]:
            with open(file_path, "rb") as output_file:
                st.download_button(
                    label=button_label,
                    data=output_file,
                    file_name=file_name,
                    mime=mime_type,
                    key=f"download_analysis_{file_name}",
                )

    st.header("6. Final PDF Report")

    st.caption(
        "Generate a final report containing data quality assessment, "
        "cleaning and harmonization summary, exploratory analysis results and visualizations."
    )

    default_dataset_display_name = st.session_state.get(
        "dataset_name",
        "Uploaded Dataset",
    )

    dataset_display_name = st.text_input(
        "Dataset display name for PDF report",
        value=st.session_state.get(
            "dataset_display_name",
            default_dataset_display_name,
        ),
        help=(
            "Optional presentation name shown in the final PDF report. "
            "This does not change the uploaded files, QC logic or analysis results."
        ),
    )

    st.session_state["dataset_display_name"] = (
        dataset_display_name.strip()
        or default_dataset_display_name
    )

    if st.button("Generate final PDF report"):
        try:
            start_time = time.time()

            with st.spinner("Generating final PDF report..."):
                report_result = FinalAnalysisReportGenerator().generate(
                    cleaner_result=st.session_state["cleaner_result"],
                    analysis_result=st.session_state["analysis_result"],
                    dataset_name=st.session_state.get(
                        "dataset_display_name",
                        st.session_state.get(
                            "dataset_name",
                            "Uploaded Dataset",
                        ),
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
