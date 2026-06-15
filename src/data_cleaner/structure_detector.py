from dataclasses import dataclass
from enum import Enum

import pandas as pd


class DataOrientation(Enum):
    SAMPLE_X_GENE = "sample_x_gene"
    GENE_X_SAMPLE = "gene_x_sample"
    UNKNOWN = "unknown"


class DetectionConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class StructureDetectionResult:
    orientation: DataOrientation
    confidence: DetectionConfidence
    reason: str


class StructureDetector:
    SAMPLE_IDENTIFIER_COLUMNS = {
        "sample_id",
        "sample",
        "sampleid",
        "sample_name",
    }

    GENE_IDENTIFIER_COLUMNS = {
        "gene",
        "gene_id",
        "gene_symbol",
        "symbol",
        "id_ref",
        "probe_id",
        "probeid",
    }

    @classmethod
    def detect(cls, dataframe: pd.DataFrame) -> StructureDetectionResult:
        if dataframe.empty:
            return StructureDetectionResult(
                orientation=DataOrientation.UNKNOWN,
                confidence=DetectionConfidence.LOW,
                reason="Input dataframe is empty.",
            )

        first_column = cls._normalize_text(dataframe.columns[0])
        expression_part = dataframe.iloc[:, 1:]
        numeric_ratio = cls._calculate_numeric_ratio(expression_part)

        if first_column in cls.SAMPLE_IDENTIFIER_COLUMNS and numeric_ratio >= 0.8:
            return StructureDetectionResult(
                orientation=DataOrientation.SAMPLE_X_GENE,
                confidence=DetectionConfidence.HIGH,
                reason=(
                    "First column matches a sample identifier and most "
                    "remaining values are numeric."
                ),
            )

        if first_column in cls.GENE_IDENTIFIER_COLUMNS and numeric_ratio >= 0.8:
            return StructureDetectionResult(
                orientation=DataOrientation.GENE_X_SAMPLE,
                confidence=DetectionConfidence.HIGH,
                reason=(
                    "First column matches a gene/probe identifier and most "
                    "remaining values are numeric."
                ),
            )

        first_column_values = dataframe.iloc[:, 0].astype(str)

        if numeric_ratio >= 0.8 and cls._looks_like_gene_identifiers(first_column_values):
            return StructureDetectionResult(
                orientation=DataOrientation.GENE_X_SAMPLE,
                confidence=DetectionConfidence.MEDIUM,
                reason=(
                    "First column values look like gene identifiers and most "
                    "remaining values are numeric."
                ),
            )

        if numeric_ratio >= 0.8 and cls._looks_like_sample_identifiers(first_column_values):
            return StructureDetectionResult(
                orientation=DataOrientation.SAMPLE_X_GENE,
                confidence=DetectionConfidence.MEDIUM,
                reason=(
                    "First column values look like sample identifiers and most "
                    "remaining values are numeric."
                ),
            )

        return StructureDetectionResult(
            orientation=DataOrientation.UNKNOWN,
            confidence=DetectionConfidence.LOW,
            reason=(
                "Data orientation could not be detected using predefined "
                "rule-based criteria."
            ),
        )

    @staticmethod
    def _calculate_numeric_ratio(dataframe: pd.DataFrame) -> float:
        if dataframe.empty:
            return 0.0

        non_missing_values = dataframe.notna().sum().sum()

        if non_missing_values == 0:
            return 0.0

        numeric_values = dataframe.apply(
            pd.to_numeric,
            errors="coerce",
        ).notna().sum().sum()

        return numeric_values / non_missing_values

    @staticmethod
    def _normalize_text(value: object) -> str:
        return str(value).strip().lower().replace(" ", "_").replace(".", "_")

    @classmethod
    def _looks_like_gene_identifiers(cls, values: pd.Series) -> bool:
        if values.empty:
            return False

        checked_values = values.dropna().astype(str).head(20)

        if checked_values.empty:
            return False

        gene_like_count = 0

        for value in checked_values:
            normalized = value.strip().upper()

            if normalized.startswith("ENSG"):
                gene_like_count += 1
            elif normalized.startswith("NM_"):
                gene_like_count += 1
            elif normalized.startswith("NR_"):
                gene_like_count += 1
            elif normalized.isalpha() and 2 <= len(normalized) <= 15:
                gene_like_count += 1

        return gene_like_count / len(checked_values) >= 0.6

    @classmethod
    def _looks_like_sample_identifiers(cls, values: pd.Series) -> bool:
        if values.empty:
            return False

        checked_values = values.dropna().astype(str).head(20)

        if checked_values.empty:
            return False

        sample_like_count = 0

        for value in checked_values:
            normalized = value.strip().upper()

            if normalized.startswith("TCGA"):
                sample_like_count += 1
            elif normalized.startswith("GSM"):
                sample_like_count += 1
            elif normalized.startswith("SRR"):
                sample_like_count += 1
            elif normalized.startswith("SAMPLE"):
                sample_like_count += 1
            elif normalized.startswith("S") and any(char.isdigit() for char in normalized):
                sample_like_count += 1

        return sample_like_count / len(checked_values) >= 0.6
