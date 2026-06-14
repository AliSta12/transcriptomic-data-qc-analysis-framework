from pathlib import Path

import pytest

from src.dataset_intake.file_discovery import (
    classify_file_by_name,
    discover_dataset_files,
)


def test_classify_expression_file_by_name():
    role, confidence, reasons = classify_file_by_name("expression_matrix.csv")

    assert role == "expression_matrix"
    assert confidence == "medium"
    assert "expression-like keyword" in reasons[0]


def test_classify_metadata_file_by_name():
    role, confidence, reasons = classify_file_by_name("sample_metadata.tsv")

    assert role == "metadata"
    assert confidence == "medium"
    assert "metadata-like keyword" in reasons[0]


def test_classify_ignored_file_by_name():
    role, confidence, reasons = classify_file_by_name("GPL_platform_annotation.txt")

    assert role == "ignored"
    assert confidence == "low"
    assert "documentation" in reasons[0]


def test_classify_unknown_file_by_name():
    role, confidence, reasons = classify_file_by_name("table_1.csv")

    assert role == "unknown"
    assert confidence == "low"
    assert "no strong filename-based evidence" in reasons[0]


def test_discover_dataset_files_lists_supported_files(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    gene_columns = ",".join([f"G{i}" for i in range(1, 31)])
    expression_values = ",".join(str(i) for i in range(1, 31))
    (dataset_dir / "expression_matrix.csv").write_text(
        f"sample_id,{gene_columns}\n"
        f"S1,{expression_values}\n"
        f"S2,{expression_values}\n"
        f"S3,{expression_values}\n"
        f"S4,{expression_values}\n"
        f"S5,{expression_values}\n"
    )
    (dataset_dir / "sample_metadata.tsv").write_text("sample_id\tgroup\nS1\ttumor\n")
    (dataset_dir / "README.md").write_text("documentation")
    (dataset_dir / "image.png").write_text("not tabular")

    result = discover_dataset_files(dataset_dir)

    assert set(result["file_name"]) == {
        "expression_matrix.csv",
        "sample_metadata.tsv",
    }

    roles = dict(zip(result["file_name"], result["predicted_role"]))

    assert roles["expression_matrix.csv"] == "expression_matrix"
    assert roles["sample_metadata.tsv"] == "metadata"


def test_discover_dataset_files_raises_for_missing_directory(tmp_path):
    missing_dir = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        discover_dataset_files(missing_dir)


def test_discover_dataset_files_raises_for_file_instead_of_directory(tmp_path):
    file_path = tmp_path / "dataset.csv"
    file_path.write_text("a,b\n1,2\n")

    with pytest.raises(NotADirectoryError):
        discover_dataset_files(file_path)


def test_discover_dataset_files_adds_preview_statistics(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    expression_file = dataset_dir / "expression_matrix.csv"
    expression_file.write_text(
        "sample_id,G1,G2,G3,G4,G5\n"
        "S1,1,2,3,4,5\n"
        "S2,2,3,4,5,6\n"
        "S3,3,4,5,6,7\n"
        "S4,4,5,6,7,8\n"
        "S5,5,6,7,8,9\n"
    )

    result = discover_dataset_files(dataset_dir)

    row = result.iloc[0]

    assert row["column_count"] == 6
    assert row["row_count_preview"] == 5
    assert row["numeric_column_count"] == 5
    assert row["numeric_value_ratio"] > 0.8
    assert row["expression_score"] > row["metadata_score"]


def test_discover_dataset_files_scores_metadata_content(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    metadata_file = dataset_dir / "labels.csv"
    metadata_file.write_text(
        "sample_id,group,batch\n"
        "S1,tumor,A\n"
        "S2,normal,A\n"
        "S3,tumor,B\n"
    )

    result = discover_dataset_files(dataset_dir)

    row = result.iloc[0]

    assert row["has_sample_like_column"] == True
    assert row["has_group_like_column"] == True
    assert row["metadata_score"] > row["expression_score"]
    assert row["predicted_role"] == "metadata"


def test_discover_dataset_files_records_warning_for_unreadable_file(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    broken_file = dataset_dir / "data.xlsx"
    broken_file.write_text("this is not a valid xlsx file")

    result = discover_dataset_files(dataset_dir)

    row = result.iloc[0]

    assert row["file_name"] == "data.xlsx"
    assert "preview read failed" in row["warnings"]


def test_select_input_files_auto_selects_unique_high_confidence_candidates(tmp_path):
    from src.dataset_intake.file_discovery import select_input_files

    dataset_dir = _create_dataset_with_unique_expression_and_metadata(tmp_path)

    discovery_report = discover_dataset_files(dataset_dir)

    result = select_input_files(discovery_report)

    statuses = dict(zip(result["role"], result["selection_status"]))

    assert statuses["expression_matrix"] == "auto_selected"
    assert statuses["metadata"] == "auto_selected"


def test_select_input_files_requires_review_when_expression_missing(tmp_path):
    from src.dataset_intake.file_discovery import select_input_files

    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    (dataset_dir / "labels.csv").write_text(
        "sample_id,group\n"
        "S1,tumor\n"
        "S2,normal\n"
    )

    discovery_report = discover_dataset_files(dataset_dir)

    result = select_input_files(discovery_report)

    expression_row = result[result["role"] == "expression_matrix"].iloc[0]

    assert expression_row["selection_status"] == "requires_review"
    assert "no high-confidence expression_matrix candidate" in expression_row["reason"]


def test_select_input_files_requires_review_when_multiple_expression_candidates(tmp_path):
    from src.dataset_intake.file_discovery import select_input_files

    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    gene_columns = ",".join([f"G{i}" for i in range(1, 31)])
    expression_values = ",".join(str(i) for i in range(1, 31))

    for file_name in ["expression_matrix.csv", "gene_counts.csv"]:
        (dataset_dir / file_name).write_text(
            f"sample_id,{gene_columns}\n"
            f"S1,{expression_values}\n"
            f"S2,{expression_values}\n"
            f"S3,{expression_values}\n"
            f"S4,{expression_values}\n"
            f"S5,{expression_values}\n"
        )

    (dataset_dir / "metadata.csv").write_text(
        "sample_id,group\n"
        "S1,tumor\n"
        "S2,normal\n"
        "S3,tumor\n"
        "S4,normal\n"
        "S5,tumor\n"
    )

    discovery_report = discover_dataset_files(dataset_dir)

    result = select_input_files(discovery_report)

    expression_row = result[result["role"] == "expression_matrix"].iloc[0]

    assert expression_row["selection_status"] == "requires_review"
    assert "multiple high-confidence expression_matrix candidates" in expression_row["reason"]


def _create_dataset_with_unique_expression_and_metadata(tmp_path):
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    gene_columns = ",".join([f"G{i}" for i in range(1, 31)])
    expression_values = ",".join(str(i) for i in range(1, 31))

    (dataset_dir / "expression_matrix.csv").write_text(
        f"sample_id,{gene_columns}\n"
        f"S1,{expression_values}\n"
        f"S2,{expression_values}\n"
        f"S3,{expression_values}\n"
        f"S4,{expression_values}\n"
        f"S5,{expression_values}\n"
    )

    (dataset_dir / "metadata.csv").write_text(
        "sample_id,group\n"
        "S1,tumor\n"
        "S2,normal\n"
        "S3,tumor\n"
        "S4,normal\n"
        "S5,tumor\n"
    )

    return dataset_dir


def test_save_intake_outputs_writes_expected_csv_files(tmp_path):
    from src.dataset_intake.file_discovery import (
        save_intake_outputs,
        select_input_files,
    )

    dataset_dir = _create_dataset_with_unique_expression_and_metadata(tmp_path)
    discovery_report = discover_dataset_files(dataset_dir)
    selected_files = select_input_files(discovery_report)

    output_dir = tmp_path / "outputs"

    result = save_intake_outputs(
        discovery_report=discovery_report,
        selected_files=selected_files,
        output_directory=output_dir,
    )

    intake_report_path = Path(result["dataset_intake_report"])
    selected_files_path = Path(result["selected_input_files"])

    assert intake_report_path.exists()
    assert selected_files_path.exists()

    assert intake_report_path.name == "dataset_intake_report.csv"
    assert selected_files_path.name == "selected_input_files.csv"

    intake_report_text = intake_report_path.read_text()
    selected_files_text = selected_files_path.read_text()

    assert "expression_score" in intake_report_text
    assert "metadata_score" in intake_report_text
    assert "selection_status" in selected_files_text
    assert "auto_selected" in selected_files_text


def test_run_dataset_intake_runs_complete_workflow(tmp_path):
    from src.dataset_intake.file_discovery import run_dataset_intake

    dataset_dir = _create_dataset_with_unique_expression_and_metadata(tmp_path)
    output_dir = tmp_path / "intake_outputs"

    result = run_dataset_intake(
        dataset_directory=dataset_dir,
        output_directory=output_dir,
    )

    assert "discovery_report" in result
    assert "selected_files" in result
    assert "output_paths" in result

    assert not result["discovery_report"].empty
    assert not result["selected_files"].empty

    assert Path(result["output_paths"]["dataset_intake_report"]).exists()
    assert Path(result["output_paths"]["selected_input_files"]).exists()

    statuses = dict(
        zip(
            result["selected_files"]["role"],
            result["selected_files"]["selection_status"],
        )
    )

    assert statuses["expression_matrix"] == "auto_selected"
    assert statuses["metadata"] == "auto_selected"
