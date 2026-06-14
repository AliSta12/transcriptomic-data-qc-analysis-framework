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

    (dataset_dir / "expression_matrix.csv").write_text("sample_id,G1,G2\nS1,1,2\n")
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
