from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".txt", ".xlsx"}

IGNORED_FILENAME_KEYWORDS = {
    "readme",
    "license",
    "gpl",
    "platform",
    "annotation",
    "supplementary",
    "manifest",
}

EXPRESSION_FILENAME_KEYWORDS = {
    "expression",
    "expr",
    "counts",
    "count",
    "matrix",
    "data",
    "gene",
}

METADATA_FILENAME_KEYWORDS = {
    "metadata",
    "meta",
    "labels",
    "label",
    "phenotype",
    "pheno",
    "clinical",
    "samples",
    "sample",
    "classes",
    "annotation",
}


def discover_dataset_files(dataset_directory: str | Path) -> pd.DataFrame:
    """
    Scan a local dataset directory and classify supported files using simple,
    transparent filename-based rules.

    This is Phase 1 of the Dataset Intake Module.
    It does not auto-select files yet.
    """
    dataset_path = Path(dataset_directory)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_path}")

    if not dataset_path.is_dir():
        raise NotADirectoryError(f"Expected a directory: {dataset_path}")

    records = []

    for file_path in sorted(dataset_path.rglob("*")):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        predicted_role, confidence, reasons = classify_file_by_name(file_path)

        records.append(
            {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": suffix.replace(".", ""),
                "predicted_role": predicted_role,
                "confidence": confidence,
                "reasons": "; ".join(reasons),
            }
        )

    return pd.DataFrame(
        records,
        columns=[
            "file_path",
            "file_name",
            "file_type",
            "predicted_role",
            "confidence",
            "reasons",
        ],
    )


def classify_file_by_name(file_path: str | Path) -> tuple[str, str, list[str]]:
    """
    Classify a file using conservative filename-based rules.

    Returns:
        predicted_role, confidence, reasons
    """
    path = Path(file_path)
    filename = path.name.lower()
    suffix = path.suffix.lower()

    reasons = []

    if suffix not in SUPPORTED_EXTENSIONS:
        return (
            "ignored",
            "low",
            [f"unsupported file extension: {suffix}"],
        )

    if _contains_any_keyword(filename, IGNORED_FILENAME_KEYWORDS):
        reasons.append("filename suggests documentation, annotation or platform file")
        return "ignored", "low", reasons

    expression_keyword_found = _contains_any_keyword(
        filename,
        EXPRESSION_FILENAME_KEYWORDS,
    )
    metadata_keyword_found = _contains_any_keyword(
        filename,
        METADATA_FILENAME_KEYWORDS,
    )

    if expression_keyword_found and not metadata_keyword_found:
        reasons.append("filename contains expression-like keyword")
        return "expression_matrix", "medium", reasons

    if metadata_keyword_found and not expression_keyword_found:
        reasons.append("filename contains metadata-like keyword")
        return "metadata", "medium", reasons

    if expression_keyword_found and metadata_keyword_found:
        reasons.append(
            "filename contains both expression-like and metadata-like keywords"
        )
        return "unknown", "low", reasons

    reasons.append("no strong filename-based evidence")
    return "unknown", "low", reasons


def _contains_any_keyword(filename: str, keywords: set[str]) -> bool:
    normalized_filename = (
        filename.lower()
        .replace("-", "_")
        .replace(".", "_")
    )
    filename_parts = {
        part
        for part in normalized_filename.split("_")
        if part
    }

    return any(keyword in filename_parts for keyword in keywords)
