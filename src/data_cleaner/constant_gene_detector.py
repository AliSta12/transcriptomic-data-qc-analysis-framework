from dataclasses import dataclass
import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger


@dataclass
class ConstantGeneDetectionResult:
    cleaned_dataframe: pd.DataFrame
    removed_genes: list[str]
    removed_gene_count: int
    summary_dataframe: pd.DataFrame


class ConstantGeneDetector:
    """
    Detects and removes genes with constant expression
    across all samples.

    Rule:
    - constant genes are removed from analytical dataset
    - status: WARNING
    """

    def apply_rules(
        self,
        dataframe: pd.DataFrame,
        audit_logger: AuditLogger | None = None,
    ) -> ConstantGeneDetectionResult:

        if "sample_id" not in dataframe.columns:
            raise ValueError("Input dataframe must contain 'sample_id' column.")

        cleaned_df = dataframe.copy()
        gene_columns = [col for col in cleaned_df.columns if col != "sample_id"]

        removed_genes: list[str] = []
        summary_rows = []

        for gene in gene_columns:
            unique_values_count = cleaned_df[gene].nunique(dropna=False)

            if unique_values_count == 1:
                removed_genes.append(gene)

                reason = (
                    "Gene has constant expression across all samples "
                    "and is not informative for exploratory analysis."
                )

                summary_rows.append(
                    {
                        "gene": gene,
                        "unique_values_count": unique_values_count,
                        "decision": "removed",
                        "status": "WARNING",
                        "reason": reason,
                    }
                )

                if audit_logger:
                    audit_logger.log(
                        module="Constant Gene Detection",
                        action="Remove Constant Gene",
                        target=gene,
                        old_value="constant_expression",
                        new_value="removed",
                        rule_applied="remove_constant_genes",
                        decision="removed",
                        status="WARNING",
                        reason=reason,
                    )

        if removed_genes:
            cleaned_df = cleaned_df.drop(columns=removed_genes)

        return ConstantGeneDetectionResult(
            cleaned_dataframe=cleaned_df,
            removed_genes=removed_genes,
            removed_gene_count=len(removed_genes),
            summary_dataframe=pd.DataFrame(summary_rows),
        )
