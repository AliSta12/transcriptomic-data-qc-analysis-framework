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

SAMPLE_COLUMN_KEYWORDS = {
    "sample_id",
    "sample",
    "samples",
    "id",
    "barcode",
}

GROUP_COLUMN_KEYWORDS = {
    "group",
    "label",
    "labels",
    "class",
    "classes",
    "condition",
    "phenotype",
    "disease",
    "tissue",
}


def discover_dataset_files(dataset_directory: str | Path) -> pd.DataFrame:
    """
    Scan a local dataset directory and classify supported files using
    transparent filename- and preview-based rules.

    This function does not auto-select files yet.
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

        preview_stats = calculate_file_preview_statistics(file_path)

        expression_score, expression_reasons = calculate_expression_score(
            file_path=file_path,
            preview_stats=preview_stats,
        )
        metadata_score, metadata_reasons = calculate_metadata_score(
            file_path=file_path,
            preview_stats=preview_stats,
        )

        predicted_role, confidence = choose_role_from_scores(
            filename_role=predicted_role,
            filename_confidence=confidence,
            expression_score=expression_score,
            metadata_score=metadata_score,
        )

        all_reasons = reasons + expression_reasons + metadata_reasons
        warnings = preview_stats.get("warning", "")

        records.append(
            {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_type": suffix.replace(".", ""),
                "predicted_role": predicted_role,
                "expression_score": expression_score,
                "metadata_score": metadata_score,
                "confidence": confidence,
                "row_count_preview": preview_stats["row_count_preview"],
                "column_count": preview_stats["column_count"],
                "numeric_column_count": preview_stats["numeric_column_count"],
                "numeric_value_ratio": preview_stats["numeric_value_ratio"],
                "has_sample_like_column": preview_stats["has_sample_like_column"],
                "has_group_like_column": preview_stats["has_group_like_column"],
                "selected": "no",
                "reasons": "; ".join(all_reasons),
                "warnings": warnings,
            }
        )

    return pd.DataFrame(
        records,
        columns=[
            "file_path",
            "file_name",
            "file_type",
            "predicted_role",
            "expression_score",
            "metadata_score",
            "confidence",
            "row_count_preview",
            "column_count",
            "numeric_column_count",
            "numeric_value_ratio",
            "has_sample_like_column",
            "has_group_like_column",
            "selected",
            "reasons",
            "warnings",
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


def calculate_file_preview_statistics(
    file_path: str | Path,
    max_rows: int = 100,
) -> dict:
    """
    Read a small preview of a tabular file and calculate simple structure metrics.

    Large files are not fully loaded.
    """
    path = Path(file_path)

    try:
        preview_df = read_table_preview(path, max_rows=max_rows)
    except Exception as error:
        return {
            "row_count_preview": 0,
            "column_count": 0,
            "numeric_column_count": 0,
            "numeric_value_ratio": 0.0,
            "has_sample_like_column": False,
            "has_group_like_column": False,
            "warning": f"preview read failed: {error}",
        }

    if preview_df.empty:
        return {
            "row_count_preview": 0,
            "column_count": len(preview_df.columns),
            "numeric_column_count": 0,
            "numeric_value_ratio": 0.0,
            "has_sample_like_column": False,
            "has_group_like_column": False,
            "warning": "preview is empty",
        }

    numeric_preview = preview_df.apply(pd.to_numeric, errors="coerce")
    numeric_column_count = int(
        numeric_preview.notna().any(axis=0).sum()
    )
    numeric_value_ratio = float(
        numeric_preview.notna().sum().sum()
        / max(preview_df.size, 1)
    )

    normalized_columns = {
        str(column).lower().strip().replace("-", "_").replace(" ", "_")
        for column in preview_df.columns
    }

    has_sample_like_column = bool(
        normalized_columns.intersection(SAMPLE_COLUMN_KEYWORDS)
    )
    has_group_like_column = bool(
        normalized_columns.intersection(GROUP_COLUMN_KEYWORDS)
    )

    return {
        "row_count_preview": int(len(preview_df)),
        "column_count": int(len(preview_df.columns)),
        "numeric_column_count": numeric_column_count,
        "numeric_value_ratio": round(numeric_value_ratio, 3),
        "has_sample_like_column": has_sample_like_column,
        "has_group_like_column": has_group_like_column,
        "warning": "",
    }


def read_table_preview(file_path: str | Path, max_rows: int = 100) -> pd.DataFrame:
    """
    Read a small preview from a supported tabular file.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path, nrows=max_rows)

    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t", nrows=max_rows)

    if suffix == ".txt":
        return pd.read_csv(path, sep=None, engine="python", nrows=max_rows)

    if suffix == ".xlsx":
        return pd.read_excel(path, nrows=max_rows)

    raise ValueError(f"Unsupported file extension: {suffix}")


def calculate_expression_score(
    file_path: str | Path,
    preview_stats: dict,
) -> tuple[int, list[str]]:
    """
    Calculate a transparent expression-matrix score.
    """
    path = Path(file_path)
    filename = path.name.lower()
    score = 0
    reasons = []

    if path.suffix.lower() in SUPPORTED_EXTENSIONS:
        score += 1
        reasons.append("supported tabular extension")

    if _contains_any_keyword(filename, EXPRESSION_FILENAME_KEYWORDS):
        score += 2
        reasons.append("filename supports expression role")

    if preview_stats["column_count"] > 20:
        score += 2
        reasons.append("many columns detected")

    if preview_stats["row_count_preview"] > 50:
        score += 1
        reasons.append("many preview rows detected")

    if preview_stats["numeric_value_ratio"] > 0.70:
        score += 3
        reasons.append("mostly numeric preview values")

    if preview_stats["column_count"] >= 5 and preview_stats["row_count_preview"] >= 5:
        score += 2
        reasons.append("matrix-like shape detected")

    if preview_stats["has_group_like_column"]:
        score -= 2
        reasons.append("group-like column reduces expression score")

    if _contains_any_keyword(filename, IGNORED_FILENAME_KEYWORDS):
        score -= 3
        reasons.append("filename suggests ignored file")

    return score, reasons


def calculate_metadata_score(
    file_path: str | Path,
    preview_stats: dict,
) -> tuple[int, list[str]]:
    """
    Calculate a transparent metadata score.
    """
    path = Path(file_path)
    filename = path.name.lower()
    score = 0
    reasons = []

    if path.suffix.lower() in SUPPORTED_EXTENSIONS:
        score += 1
        reasons.append("supported tabular extension")

    if _contains_any_keyword(filename, METADATA_FILENAME_KEYWORDS):
        score += 2
        reasons.append("filename supports metadata role")

    if preview_stats["has_sample_like_column"]:
        score += 3
        reasons.append("sample-like column detected")

    if preview_stats["has_group_like_column"]:
        score += 3
        reasons.append("group-like column detected")

    if (
        preview_stats["column_count"] <= 20
        and preview_stats["numeric_value_ratio"] < 0.70
    ):
        score += 1
        reasons.append("metadata-like column/value structure")

    if preview_stats["column_count"] > 100:
        score -= 4
        reasons.append("many columns reduce metadata score")

    if preview_stats["numeric_value_ratio"] > 0.90:
        score -= 3
        reasons.append("mostly numeric values reduce metadata score")

    if _contains_any_keyword(filename, IGNORED_FILENAME_KEYWORDS):
        score -= 3
        reasons.append("filename suggests ignored file")

    return score, reasons


def choose_role_from_scores(
    filename_role: str,
    filename_confidence: str,
    expression_score: int,
    metadata_score: int,
) -> tuple[str, str]:
    """
    Combine filename-based classification with content-based scores.
    """
    if filename_role == "ignored":
        return "ignored", "low"

    score_difference = abs(expression_score - metadata_score)
    best_score = max(expression_score, metadata_score)

    if best_score >= 7 and score_difference >= 2:
        if expression_score > metadata_score:
            return "expression_matrix", "high"
        return "metadata", "high"

    if best_score >= 4 and score_difference >= 2:
        if expression_score > metadata_score:
            return "expression_matrix", "medium"
        return "metadata", "medium"

    if filename_role in {"expression_matrix", "metadata"}:
        return filename_role, filename_confidence

    return "unknown", "low"


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
