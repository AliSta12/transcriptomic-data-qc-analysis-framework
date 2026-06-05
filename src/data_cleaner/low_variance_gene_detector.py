from dataclasses import dataclass
import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger


@dataclass
class LowVarianceGeneDetectionResult:
    cleaned_dataframe: pd.DataFrame
    removed_genes: list[str]
    removed_gene_count: int
    variance_threshold: float
    summary_dataframe: pd.DataFrame


class LowVarianceGeneDetector:
    """
    Detects and removes genes with very low expression variance.

    MVP rule:
    - variance < 0.01 -> remove
    - status: WARNING
    """

    def __init__(self, variance_threshold: float = 0.01) -> None:
        self.variance_threshold = variance_threshold

    def apply_rules(
        self,
        dataframe: pd.DataFrame,
        audit_logger: AuditLogger | None = None,
    ) -> LowVarianceGeneDetectionResult:

        if "sample_id" not in dataframe.columns:
            raise ValueError("Input dataframe must contain 'sample_id' column.")

        cleaned_df = dataframe.copy()
        gene_columns = [col for col in cleaned_df.columns if col != "sample_id"]

        removed_genes: list[str] = []
        summary_rows = []

        for gene in gene_columns:
            variance = cleaned_df[gene].var()

            if variance < self.variance_threshold:
                removed_genes.append(gene)

                reason = (
                    "Gene variance is below the MVP threshold "
                    "and is considered low-informative for exploratory analysis."
                )

                summary_rows.append(
                    {
                        "gene": gene,
                        "variance": variance,
                        "variance_threshold": self.variance_threshold,
                        "decision": "removed",
                        "status": "WARNING",
                        "reason": reason,
                    }
                )

                if audit_logger:
                    audit_logger.log(
                        module="Low Variance Gene Detection",
                        action="Remove Low Variance Gene",
                        target=gene,
                        old_value=f"variance={variance}",
                        new_value="removed",
                        rule_applied="remove_low_variance_genes",
                        decision="removed",
                        status="WARNING",
                        reason=reason,
                    )

        if removed_genes:
            cleaned_df = cleaned_df.drop(columns=removed_genes)

        return LowVarianceGeneDetectionResult(
            cleaned_dataframe=cleaned_df,
            removed_genes=removed_genes,
            removed_gene_count=len(removed_genes),
            variance_threshold=self.variance_threshold,
            summary_dataframe=pd.DataFrame(summary_rows),
        )
