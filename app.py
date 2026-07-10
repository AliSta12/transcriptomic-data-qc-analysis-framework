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


def format_column_label(column_name: str) -> str:
    label_map = {
        "sample_id": "Sample ID",
        "overall_status": "Overall status",
        "readiness_status": "Readiness status",
        "pass_count": "PASS checks",
        "warning_count": "WARNING checks",
        "fail_count": "FAIL checks",
        "review_count": "REQUIRES REVIEW checks",
        "analysis_step": "Analysis step",
        "rule_applied": "Rule applied",
        "old_value": "Old value",
        "new_value": "New value",
    }

    column_text = str(column_name)
    return label_map.get(
        column_text,
        column_text.replace("_", " ").strip().capitalize(),
    )


def prepare_display_dataframe(
    dataframe: pd.DataFrame,
    column_order: list[str] | None = None,
    max_rows: int | None = None,
) -> pd.DataFrame:
    display_df = dataframe.copy()

    if column_order is not None:
        ordered_columns = [
            column for column in column_order
            if column in display_df.columns
        ]
        remaining_columns = [
            column for column in display_df.columns
            if column not in ordered_columns
        ]
        display_df = display_df[ordered_columns + remaining_columns]

    if max_rows is not None:
        display_df = display_df.head(max_rows)

    return display_df.rename(
        columns={
            column: format_column_label(column)
            for column in display_df.columns
        }
    )




def table_column_width(column_name: str) -> str | None:
    compact_columns = {
        "Status",
        "Metric",
        "Metric value",
        "Value",
        "Entries",
        "Count",
        "PASS checks",
        "WARNING checks",
        "FAIL checks",
        "REQUIRES REVIEW checks",
        "Group",
        "Dataset",
        "Stage",
        "Location",
        "Gender",
        "Age",
        "Individual id",
    }

    medium_columns = {
        "Sample ID",
        "Check",
        "Module",
        "Action",
        "Target",
        "Decision",
        "Original element",
        "Standardized element",
        "Element type",
        "Transformation",
        "Old value",
        "New value",
        "Timestamp",
        "Analysis step",
    }

    wide_columns = {
        "Details",
        "Reason",
        "Rule applied",
        "Rule-based decision",
        "Detected issue",
        "Result",
    }

    if column_name in compact_columns:
        return "small"

    if column_name in medium_columns:
        return "medium"

    if column_name in wide_columns:
        return "large"

    # Unknown columns, including gene columns, should use Streamlit auto-sizing.
    return None


def build_table_column_config(dataframe: pd.DataFrame) -> dict:
    if not hasattr(st, "column_config"):
        return {}

    column_config = {}

    for column in dataframe.columns:
        width = table_column_width(str(column))

        if width is None:
            continue

        try:
            column_config[column] = st.column_config.Column(
                width=width,
            )
        except Exception:
            return {}

    return column_config



def format_table_cell_value(value: object) -> str:
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)


def left_align_table_values(dataframe: pd.DataFrame) -> pd.DataFrame:
    display_df = dataframe.copy()

    for column in display_df.columns:
        display_df[column] = display_df[column].map(format_table_cell_value)

    return display_df


def show_table(
    dataframe: pd.DataFrame,
    height: int = 280,
    column_order: list[str] | None = None,
    max_rows: int | None = None,
) -> None:
    if dataframe is None or dataframe.empty:
        st.info("No rows to display.")
        return

    display_df = prepare_display_dataframe(
        dataframe=dataframe,
        column_order=column_order,
        max_rows=max_rows,
    )
    display_df = left_align_table_values(display_df)

    column_config = build_table_column_config(display_df)

    try:
        st.dataframe(
            display_df,
            width="stretch",
            height=height,
            hide_index=True,
            column_config=column_config,
        )
    except TypeError:
        st.dataframe(
            display_df,
            width="stretch",
            height=height,
        )


def build_expression_preview(
    expression_df: pd.DataFrame,
    max_rows: int = 10,
    max_genes: int = 10,
) -> pd.DataFrame:
    if "sample_id" not in expression_df.columns:
        return expression_df.head(max_rows)

    gene_columns = [
        column for column in expression_df.columns
        if column != "sample_id"
    ]
    preview_columns = ["sample_id"] + gene_columns[:max_genes]
    return expression_df[preview_columns].head(max_rows)


def show_centered_plot(
    image_path: str,
    size: str = "medium",
) -> None:
    plot_widths = {
        "medium": 900,
        "heatmap": 900,
        "wide": 1000,
    }
    column_ratios = {
        "medium": [0.75, 3, 0.75],
        "heatmap": [0.75, 3, 0.75],
        "wide": [0.5, 3, 0.5],
    }

    plot_width = plot_widths.get(size, plot_widths["medium"])
    ratios = column_ratios.get(size, column_ratios["medium"])

    _, center, _ = st.columns(ratios)

    with center:
        st.image(
            image_path,
            width=plot_width,
        )


def format_metric_display_value(
    value: object,
    integer: bool = False,
) -> str:
    if pd.isna(value):
        return "N/A"

    if integer:
        try:
            numeric_value = float(value)
            if numeric_value.is_integer():
                return str(int(numeric_value))
        except (TypeError, ValueError):
            pass

    return str(value)


def humanize_metric_name(metric_name: str) -> str:
    metric_labels = {
        "sample_count": "Sample count",
        "gene_count": "Gene count",
        "group_count": "Group count",
        "min_expression": "Minimum expression",
        "max_expression": "Maximum expression",
        "mean_expression": "Mean expression",
        "median_expression": "Median expression",
    }

    metric_text = str(metric_name)
    return metric_labels.get(
        metric_text,
        metric_text.replace("_", " ").strip().capitalize(),
    )


def prepare_overview_display_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    display_df = dataframe.copy()

    if "metric" in display_df.columns and "value" in display_df.columns:
        integer_metrics = {
            "sample_count",
            "gene_count",
            "group_count",
        }

        display_df["value"] = display_df.apply(
            lambda row: format_metric_display_value(
                row["value"],
                integer=str(row["metric"]) in integer_metrics,
            ),
            axis=1,
        )
        display_df["metric"] = display_df["metric"].apply(humanize_metric_name)

    return display_df


def get_metric_value(
    dataframe: pd.DataFrame,
    metric_name: str,
    default: str = "N/A",
    integer: bool = False,
) -> str:
    if dataframe is None or dataframe.empty:
        return default

    if "metric" not in dataframe.columns or "value" not in dataframe.columns:
        return default

    matching_rows = dataframe[dataframe["metric"] == metric_name]

    if matching_rows.empty:
        return default

    return format_metric_display_value(
        matching_rows.iloc[0]["value"],
        integer=integer,
    )


def get_readiness_value(
    dataframe: pd.DataFrame,
    candidate_columns: list[str],
    default: str = "N/A",
) -> str:
    if dataframe is None or dataframe.empty:
        return default

    row = dataframe.iloc[0]

    for column in candidate_columns:
        if column in dataframe.columns:
            value = row[column]
            if pd.notna(value):
                return str(value)

    return default


def show_readiness_summary(data_readiness_report: pd.DataFrame) -> None:
    status = get_readiness_value(
        data_readiness_report,
        ["overall_status", "readiness_status"],
    )

    if status == "READY_FOR_ANALYSIS":
        st.success("READY_FOR_ANALYSIS — Dataset is ready for exploratory analysis.")
    elif status == "READY_WITH_WARNINGS":
        st.warning(
            "READY_WITH_WARNINGS — Dataset is ready for exploratory analysis, "
            "but QC warnings should be reviewed before interpretation."
        )
    else:
        st.error(
            f"{status} — Dataset requires review before exploratory analysis."
        )

    st.caption(
        "Detailed QC findings are summarized below. Full QC reports are available "
        "in Data Cleaner downloads."
    )


def metric_label_for_check(check_name: str) -> str:
    label_map = {
        "Numeric Data Check": "Detected invalid expression values",
        "Missing Data": "Detected missing expression values",
        "Duplicate Samples": "Detected duplicate samples",
        "Duplicate Genes": "Detected duplicate genes",
        "Metadata Consistency": "Detected metadata issues",
        "Constant Genes": "Detected constant genes",
        "Low Variance Genes": "Detected low-variance genes",
    }
    return label_map.get(str(check_name), "Metric value")


def qc_decision_for_check(check_name: str, status: str) -> str:
    if status == "FAIL":
        return "Resolve before analysis"

    if status == "REQUIRES REVIEW":
        return "Manual review required"

    decision_map = {
        "Numeric Data Check": "Converted invalid values to missing",
        "Missing Data": "Imputed low-missing genes; removed high-missing genes",
        "Constant Genes": "Removed from analytical dataset",
        "Duplicate Samples": "No automatic removal",
        "Duplicate Genes": "Aggregated when numeric",
        "Metadata Consistency": "Checked sample/group compatibility",
        "Low Variance Genes": "Reported for review",
    }

    return decision_map.get(str(check_name), "See detailed explanation")


def show_qc_decision_summary(data_quality_report: pd.DataFrame) -> None:
    st.markdown("#### Issues requiring attention")

    if data_quality_report is None or data_quality_report.empty:
        st.info("No QC checks available.")
        return

    issue_statuses = ["WARNING", "FAIL", "REQUIRES REVIEW"]
    issue_rows = data_quality_report[
        data_quality_report["status"].isin(issue_statuses)
    ]
    passed_rows = data_quality_report[
        data_quality_report["status"] == "PASS"
    ]

    if issue_rows.empty:
        st.success("No warnings, failed checks or manual-review checks detected.")
    else:
        issue_summary_rows = []

        for _, row in issue_rows.iterrows():
            status = str(row["status"])
            check = str(row["check"])

            issue_summary_rows.append(
                {
                    "Status": status,
                    "Check": check,
                    "Count": row["metric"],
                    "Action": qc_decision_for_check(check, status),
                }
            )

        show_table(
            pd.DataFrame(issue_summary_rows),
            height=180,
        )

        with st.expander("Detailed QC explanations", expanded=False):
            for _, row in issue_rows.iterrows():
                status = str(row["status"])
                check = str(row["check"])
                metric = row["metric"]
                details = str(row["details"])

                st.markdown(f"**{check} — {status}**")
                st.caption(f"{metric_label_for_check(check)}: {metric}")
                st.write(details)

    if not passed_rows.empty:
        passed_check_names = (
            passed_rows["check"]
            .astype(str)
            .tolist()
        )

        with st.expander(f"Passed checks ({len(passed_rows)})", expanded=False):
            st.write(", ".join(passed_check_names))


def show_audit_decision_summary(audit_log: pd.DataFrame) -> None:
    if audit_log is None or audit_log.empty:
        st.info("No audit log entries recorded.")
        return

    summary_columns = [
        column for column in [
            "status",
            "action",
            "decision",
            "rule_applied",
        ]
        if column in audit_log.columns
    ]

    if not summary_columns:
        return

    summary_df = (
        audit_log
        .groupby(summary_columns, dropna=False)
        .size()
        .reset_index(name="entries")
    )

    show_table(
        summary_df,
        height=180,
    )


def show_dataframe_download_button(
    file_name: str,
    label: str,
    dataframe: pd.DataFrame,
    key: str,
) -> None:
    st.download_button(
        label=label,
        data=dataframe.to_csv(index=False).encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
        key=key,
    )


def show_file_download_button(
    file_path: Path,
    label: str,
    key: str,
) -> None:
    if not file_path.exists():
        return

    if file_path.suffix == ".png":
        mime_type = "image/png"
    elif file_path.suffix == ".md":
        mime_type = "text/markdown"
    else:
        mime_type = "text/csv"

    with open(file_path, "rb") as output_file:
        st.download_button(
            label=label,
            data=output_file,
            file_name=file_path.name,
            mime=mime_type,
            key=key,
        )



def reset_input_dependent_results() -> None:
    st.session_state.pop("cleaner_result", None)
    st.session_state.pop("analysis_result", None)
    st.session_state.pop("uploaded_files_signature", None)


def format_intake_status(value: object) -> str:
    status_text = str(value or "").replace("_", " ").strip()
    return status_text.capitalize() if status_text else "Not selected"


def safe_row_value(row: pd.Series, candidate_columns: list[str]) -> str:
    for column in candidate_columns:
        if column in row.index and pd.notna(row[column]):
            value = str(row[column]).strip()
            if value:
                return value

    return ""


def build_intake_selection_status_table(selected_files: pd.DataFrame) -> pd.DataFrame:
    if selected_files is None or selected_files.empty:
        return pd.DataFrame(
            [
                {
                    "Role": "expression_matrix",
                    "Status": "Not selected",
                    "File": "",
                    "Confidence": "",
                    "Reason": "No candidate selected.",
                },
                {
                    "Role": "metadata",
                    "Status": "Not selected",
                    "File": "",
                    "Confidence": "",
                    "Reason": "No candidate selected.",
                },
            ]
        )

    rows = []

    for _, row in selected_files.iterrows():
        file_path = safe_row_value(row, ["file_path"])
        rows.append(
            {
                "Role": safe_row_value(row, ["role"]),
                "Status": format_intake_status(
                    safe_row_value(row, ["selection_status"])
                ),
                "File": Path(file_path).name if file_path else "",
                "Confidence": safe_row_value(row, ["confidence"]),
                "Reason": safe_row_value(row, ["reason"]),
            }
        )

    return pd.DataFrame(rows)


def get_discovery_candidate_paths(discovery_report: pd.DataFrame) -> list[str]:
    if discovery_report is None or discovery_report.empty:
        return []

    if "file_path" not in discovery_report.columns:
        return []

    paths = (
        discovery_report["file_path"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    return paths


def format_discovery_candidate_label(
    file_path: str,
    discovery_report: pd.DataFrame,
) -> str:
    label_parts = [Path(file_path).name]

    if discovery_report is None or discovery_report.empty:
        return label_parts[0]

    if "file_path" not in discovery_report.columns:
        return label_parts[0]

    matching_rows = discovery_report[
        discovery_report["file_path"].astype(str) == str(file_path)
    ]

    if matching_rows.empty:
        return label_parts[0]

    row = matching_rows.iloc[0]

    role = safe_row_value(
        row,
        [
            "predicted_role",
            "role",
            "classification",
            "file_type",
        ],
    )
    confidence = safe_row_value(row, ["confidence"])

    expression_score = safe_row_value(
        row,
        [
            "expression_score",
            "expression_matrix_score",
        ],
    )
    metadata_score = safe_row_value(
        row,
        [
            "metadata_score",
        ],
    )

    if role:
        label_parts.append(f"role: {role}")

    if confidence:
        label_parts.append(f"confidence: {confidence}")

    score_parts = []
    if expression_score:
        score_parts.append(f"expr {expression_score}")
    if metadata_score:
        score_parts.append(f"meta {metadata_score}")

    if score_parts:
        label_parts.append(", ".join(score_parts))

    return " | ".join(label_parts)


def preview_intake_candidate_file(file_path: str, label: str) -> None:
    st.markdown(f"**{label}: `{Path(file_path).name}`**")
    st.caption(f"Path: `{file_path}`")

    try:
        preview_df = read_local_table_file(file_path)
    except Exception as error:
        st.error(f"Could not preview this file: {error}")
        return

    preview_columns = preview_df.columns[:10].tolist()

    show_table(
        preview_df.loc[:, preview_columns].head(5),
        height=220,
    )


def use_dataset_intake_files(
    expression_path: str,
    metadata_path: str,
    selection_mode: str,
) -> None:
    st.session_state["use_dataset_intake_files"] = True
    st.session_state["dataset_intake_expression_path"] = str(expression_path)
    st.session_state["dataset_intake_metadata_path"] = str(metadata_path)
    st.session_state["dataset_intake_selection_mode"] = selection_mode
    reset_input_dependent_results()
    st.rerun()


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

with st.expander("Input requirements", expanded=False):
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
            "project paths, Windows drive paths and \\wsl$ paths."
        ),
    )

    if dataset_directory.strip():
        resolved_dataset_directory = normalize_local_folder_path(dataset_directory)
        st.caption(f"Resolved path used by the app: `{resolved_dataset_directory}`")
    else:
        st.info("Enter a local folder path to enable folder scanning.")

    intake_output_directory = "outputs/streamlit_dataset_intake"
    scan_button_disabled = not dataset_directory.strip()

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

            reset_input_dependent_results()
            st.session_state["use_dataset_intake_files"] = False
            st.session_state.pop("dataset_intake_expression_path", None)
            st.session_state.pop("dataset_intake_metadata_path", None)
            st.session_state.pop("dataset_intake_selection_mode", None)
            st.session_state.pop("show_input_review", None)
            st.session_state.pop("input_review_source", None)
            st.session_state.pop("input_review_message", None)

            with st.spinner("Scanning dataset folder with rule-based Dataset Intake..."):
                intake_result = run_dataset_intake(
                    dataset_directory=dataset_directory_path,
                    output_directory=intake_output_directory,
                )

            st.session_state["dataset_intake_result"] = intake_result
            st.success("Dataset Intake scan completed.")

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

        st.subheader("Dataset Intake result")

        if auto_selected_count == 2:
            st.success(
                "The scan found one high-confidence expression matrix and one "
                "high-confidence metadata file."
            )
        else:
            st.warning(
                "Manual selection required. The app could not safely auto-select "
                "both required files."
            )

        st.markdown("#### Candidate selection status")
        show_table(
            build_intake_selection_status_table(selected_files),
            height=170,
        )

        candidate_paths = get_discovery_candidate_paths(discovery_report)

        if auto_selected_count == 2:
            expression_row = selected_files[
                selected_files["role"] == "expression_matrix"
            ].iloc[0]
            metadata_row = selected_files[
                selected_files["role"] == "metadata"
            ].iloc[0]

            expression_path = expression_row["file_path"]
            metadata_path = metadata_row["file_path"]

            with st.expander("Preview selected candidate files", expanded=False):
                preview_intake_candidate_file(
                    expression_path,
                    "Expression matrix candidate",
                )
                preview_intake_candidate_file(
                    metadata_path,
                    "Metadata candidate",
                )

            if st.button("Use selected files"):
                use_dataset_intake_files(
                    expression_path=expression_path,
                    metadata_path=metadata_path,
                    selection_mode="Auto-selected by Dataset Intake",
                )

        elif candidate_paths:
            st.markdown("#### Manual candidate selection")
            st.caption(
                "Choose candidate files from the scan results. Preview is optional; "
                "the Data Cleaner will still validate the selected files before analysis."
            )

            expression_candidate = st.selectbox(
                "Expression matrix candidate",
                options=candidate_paths,
                format_func=lambda value: format_discovery_candidate_label(
                    value,
                    discovery_report,
                ),
                key="manual_intake_expression_candidate",
            )

            metadata_candidate = st.selectbox(
                "Metadata candidate",
                options=candidate_paths,
                format_func=lambda value: format_discovery_candidate_label(
                    value,
                    discovery_report,
                ),
                key="manual_intake_metadata_candidate",
            )

            same_file_selected = expression_candidate == metadata_candidate

            if same_file_selected:
                st.warning(
                    "Expression matrix and metadata candidates should be two "
                    "different files."
                )

            with st.expander("Preview selected candidate files", expanded=False):
                preview_intake_candidate_file(
                    expression_candidate,
                    "Expression matrix candidate",
                )
                preview_intake_candidate_file(
                    metadata_candidate,
                    "Metadata candidate",
                )

            if st.button("Use selected files", disabled=same_file_selected):
                use_dataset_intake_files(
                    expression_path=expression_candidate,
                    metadata_path=metadata_candidate,
                    selection_mode="Manual selection after folder scan",
                )

        else:
            st.info(
                "No supported candidate files were detected. Use manual upload with "
                "prepared expression and metadata files."
            )

        with st.expander("Detailed Dataset Intake discovery report", expanded=False):
            st.caption(
                "Technical discovery report with file scores, preview statistics, "
                "classification reasons and warnings."
            )

            if discovery_report.empty:
                st.info(
                    "No supported tabular files were detected in the selected folder."
                )
            else:
                discovery_display = discovery_report.copy()

                if "file_path" in discovery_display.columns:
                    discovery_display["file_path"] = discovery_display[
                        "file_path"
                    ].apply(lambda value: Path(value).name)

                show_table(
                    discovery_display,
                    height=340,
                )

            output_paths = intake_result.get("output_paths", {})

            if output_paths:
                st.caption(
                    "Saved outputs: "
                    f"{output_paths.get('dataset_intake_report', '')} and "
                    f"{output_paths.get('selected_input_files', '')}"
                )


if (
    st.session_state.get("show_input_review", False)
    and st.session_state.get("input_review_source") == "Data Cleaner"
):
    st.header("Input Review & Repair Guidance")

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
        The selected input files could not be processed by the available
        rule-based cleaning rules. Before uploading corrected files, check that:

        - the expression matrix contains samples and gene expression values,
        - metadata contains at least `sample_id` and `group`,
        - `sample_id` values match between expression data and metadata,
        - expression values are numeric,
        - files are saved as CSV, TSV or XLSX,
        - the expression matrix can be harmonized to sample × gene format.
        """
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
            st.session_state.pop("dataset_intake_selection_mode", None)
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
        current_source = st.session_state.get(
            "dataset_intake_selection_mode",
            "Scan local folder",
        )
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

    st.success("Input files are ready for preview.")

    selection_columns = st.columns(3)
    selection_columns[0].caption("Source")
    selection_columns[0].write(current_source)
    selection_columns[1].caption("Expression matrix")
    selection_columns[1].write(current_expression_name)
    selection_columns[2].caption("Metadata file")
    selection_columns[2].write(current_metadata_name)

    st.caption("Review the preview below, then run Data Cleaner & QC.")

    st.subheader("Input preview")
    st.caption(
        "Preview shows the first rows of raw uploaded files before rule-based "
        "cleaning and harmonization."
    )

    expression_tab, metadata_tab = st.tabs(
        ["Expression matrix", "Metadata"]
    )

    with expression_tab:
        st.caption("Raw expression matrix. Showing the first 5 rows.")
        show_table(
            expression_df.head(5),
            height=240,
        )

    with metadata_tab:
        st.caption("Raw metadata. Showing the first 5 rows.")
        show_table(
            metadata_df.head(5),
            height=220,
        )

    st.header("2. Run Data Cleaner & QC")

    if st.session_state.get("show_input_review", False):
        st.warning(
            "Input Review is active. Review the guidance above, correct the input files, "
            "and then upload the corrected files again."
        )

    if st.button("Run Data Cleaner & QC"):
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
                f"Data Cleaner & QC completed. Final status: {result.final_status}. "
                "Review warnings, then run the Analysis Engine."
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

    st.subheader("Readiness summary")
    show_readiness_summary(result.data_readiness_report)

    with st.expander("QC check details", expanded=False):
        st.caption(
            "Compact summary of QC findings that may affect analysis readiness. "
            "The full data_quality_report.csv is available in Data Cleaner downloads."
        )

        show_qc_decision_summary(result.data_quality_report)
    with st.expander("Harmonization summary"):
        st.caption(
            "This report documents structural changes applied before analysis, "
            "including data orientation and standardized column names."
        )
        show_table(
            result.harmonization_report,
            height=140,
        )

    with st.expander("Audit log of cleaning decisions"):
        st.caption(
            "The audit log records automatic rule-based decisions made by the Data Cleaner, "
            "including detected issues, applied rules, decisions, statuses and reasons."
        )
        st.caption(f"{len(result.audit_log)} audit log entries recorded.")

        st.markdown("#### Decision summary")
        show_audit_decision_summary(result.audit_log)

        st.markdown("#### Full audit log")
        show_table(
            result.audit_log,
            height=320,
            column_order=[
                "status",
                "module",
                "action",
                "target",
                "decision",
                "rule_applied",
                "reason",
                "old_value",
                "new_value",
                "timestamp",
            ],
        )

    with st.expander("Cleaned expression matrix preview"):
        st.caption(
            "Preview of the harmonized expression matrix in sample × gene format. "
            "Showing the first 10 rows and first 10 genes. "
            "The full cleaned matrix is available for download."
        )
        show_table(
            build_expression_preview(result.cleaned_expression_matrix),
            height=260,
        )

    with st.expander("Clean metadata preview"):
        st.caption(
            "Preview of standardized metadata after column harmonization. "
            "Showing the first 10 rows."
        )
        show_table(
            result.clean_metadata.head(10),
            height=240,
        )

    with st.expander("Download Data Cleaner outputs", expanded=False):
        st.caption(
            "Download harmonized data and transparent QC reports generated by the Data Cleaner."
        )

        st.markdown("**Cleaned data**")
        cleaned_data_columns = st.columns(2)
        with cleaned_data_columns[0]:
            show_dataframe_download_button(
                file_name="clean_expression_matrix.csv",
                label="Download clean_expression_matrix.csv",
                dataframe=result.cleaned_expression_matrix,
                key="download_cleaner_clean_expression_matrix.csv",
            )
        with cleaned_data_columns[1]:
            show_dataframe_download_button(
                file_name="clean_metadata.csv",
                label="Download clean_metadata.csv",
                dataframe=result.clean_metadata,
                key="download_cleaner_clean_metadata.csv",
            )

        st.markdown("**QC reports**")
        qc_report_downloads = [
            ("audit_log.csv", "Download audit_log.csv", result.audit_log),
            (
                "harmonization_report.csv",
                "Download harmonization_report.csv",
                result.harmonization_report,
            ),
            (
                "data_quality_report.csv",
                "Download data_quality_report.csv",
                result.data_quality_report,
            ),
            (
                "data_readiness_report.csv",
                "Download data_readiness_report.csv",
                result.data_readiness_report,
            ),
        ]

        qc_report_columns = st.columns(2)

        for index, (file_name, label, dataframe) in enumerate(qc_report_downloads):
            with qc_report_columns[index % 2]:
                show_dataframe_download_button(
                    file_name=file_name,
                    label=label,
                    dataframe=dataframe,
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

    analysis_button_label = (
        "Re-run Analysis Engine"
        if "analysis_result" in st.session_state
        else "Run Analysis Engine"
    )

    if st.button(analysis_button_label, disabled=analysis_blocked):

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
                "Analysis Engine completed. Review exploratory plots below, "
                "then generate the final PDF report."
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
    st.info(
        "These outputs are exploratory and do not represent formal differential "
        "expression analysis."
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

        overview_df = analysis.dataset_overview.summary_dataframe

        overview_summary = pd.DataFrame(
            [
                {
                    "Metric": "Samples",
                    "Value": get_metric_value(
                        overview_df,
                        "sample_count",
                        integer=True,
                    ),
                },
                {
                    "Metric": "Genes",
                    "Value": get_metric_value(
                        overview_df,
                        "gene_count",
                        integer=True,
                    ),
                },
                {
                    "Metric": "Groups",
                    "Value": get_metric_value(
                        overview_df,
                        "group_count",
                        integer=True,
                    ),
                },
                {
                    "Metric": "Mean expression",
                    "Value": get_metric_value(
                        overview_df,
                        "mean_expression",
                    ),
                },
                {
                    "Metric": "Median expression",
                    "Value": get_metric_value(
                        overview_df,
                        "median_expression",
                    ),
                },
                {
                    "Metric": "Expression range",
                    "Value": (
                        f"{get_metric_value(overview_df, 'min_expression')} – "
                        f"{get_metric_value(overview_df, 'max_expression')}"
                    ),
                },
            ]
        )

        show_table(
            overview_summary,
            height=260,
        )
    with class_tab:
        st.subheader("Class Distribution")
        st.caption(
            "Shows the number and percentage of samples in each biological group. "
            "This helps assess class balance before interpreting PCA and clustering."
        )
        show_centered_plot(
            analysis.class_distribution.plot_path,
            size="medium",
        )
        st.caption(
            "Normal and Tumor groups have equal sample counts, while Mucosa has fewer samples."
        )

    with pca_tab:
        st.subheader("PCA")
        st.caption(
            "PCA visualizes sample-level variation in the cleaned expression matrix. "
            "Points represent samples and colors represent metadata groups. "
            "This is an exploratory visualization, not a formal differential expression analysis."
        )
        show_centered_plot(
            analysis.pca_analysis.plot_path,
            size="medium",
        )
        st.caption(
            "Visible separation patterns are exploratory and require further validation."
        )

    with variable_genes_tab:
        st.subheader("Top Variable Genes")
        st.caption(
            "Shows the top 20 genes by variance for readability. Full top 50 and "
            "top 100 rankings are available as downloadable CSV files. This ranking "
            "is exploratory and is not formal differential expression analysis."
        )
        show_centered_plot(
            analysis.variable_gene_analysis.barplot_path,
            size="medium",
        )

    with heatmap_tab:
        st.subheader("Heatmap")
        st.caption(
            "Heatmap of the top 50 most variable genes across samples. "
            "For large datasets, sample labels are hidden to keep the visualization readable."
        )
        show_centered_plot(
            analysis.heatmap.plot_path,
            size="heatmap",
        )

    with clustering_tab:
        st.subheader("Sample Clustering")
        st.caption(
            "Hierarchical clustering visualizes similarity between samples based on the cleaned expression matrix. "
            "For large datasets, sample labels are hidden to avoid an unreadable plot."
        )
        show_centered_plot(
            analysis.sample_clustering.plot_path,
            size="wide",
        )

    with summary_tab:
        st.subheader("Analysis Summary")
        st.caption(
            "Concise summary of exploratory analysis outputs generated from the cleaned dataset."
        )
        show_table(
            analysis.analysis_summary.summary_dataframe,
            height=260,
        )

    with st.expander("Download Analysis Engine outputs", expanded=False):
        st.caption(
            "Download exploratory analysis tables and visualizations generated from the cleaned dataset."
        )

        analysis_output_directory = Path("outputs/streamlit_demo")

        st.markdown("**Tables and summaries**")
        table_downloads = [
            ("top_50_variable_genes.csv", "Download top_50_variable_genes.csv"),
            ("top_100_variable_genes.csv", "Download top_100_variable_genes.csv"),
            ("analysis_summary.csv", "Download analysis_summary.csv"),
            ("analysis_summary.md", "Download analysis_summary.md"),
        ]

        table_download_columns = st.columns(2)

        for index, (file_name, button_label) in enumerate(table_downloads):
            with table_download_columns[index % 2]:
                show_file_download_button(
                    file_path=analysis_output_directory / file_name,
                    label=button_label,
                    key=f"download_analysis_{file_name}",
                )

        st.markdown("**Plots**")
        plot_downloads = [
            ("class_distribution.png", "Download class_distribution.png"),
            ("pca_plot.png", "Download pca_plot.png"),
            (
                "top_variable_genes_barplot.png",
                "Download top_variable_genes_barplot.png",
            ),
            (
                "heatmap_top50_variable_genes.png",
                "Download heatmap_top50_variable_genes.png",
            ),
            (
                "sample_clustering_dendrogram.png",
                "Download sample_clustering_dendrogram.png",
            ),
        ]

        plot_download_columns = st.columns(2)

        for index, (file_name, button_label) in enumerate(plot_downloads):
            with plot_download_columns[index % 2]:
                show_file_download_button(
                    file_path=analysis_output_directory / file_name,
                    label=button_label,
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

            st.success("Final PDF report generated successfully.")

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
