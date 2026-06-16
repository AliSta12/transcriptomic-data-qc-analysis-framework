from dataclasses import dataclass
import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger


@dataclass
class ExpressionValueCleaningResult:
    cleaned_dataframe: pd.DataFrame
    invalid_value_count: int
    affected_genes: list[str]
    invalid_value_summary: pd.DataFrame


class ExpressionValueCleaner:
    """
    Converts non-numeric expression values to missing values.

    Rule:
    - expression values must be numeric
    - invalid numeric values are converted to NaN
    - every affected gene is reported in the audit log
    """

    def apply_rules(
        self,
        dataframe: pd.DataFrame,
        audit_logger: AuditLogger | None = None,
    ) -> ExpressionValueCleaningResult:
        if "sample_id" not in dataframe.columns:
            raise ValueError("Input dataframe must contain 'sample_id' column.")

        cleaned_df = dataframe.copy()
        gene_columns = [col for col in cleaned_df.columns if col != "sample_id"]

        invalid_value_count = 0
        affected_genes: list[str] = []
        summary_rows = []

        for gene in gene_columns:
            original_values = cleaned_df[gene]
            converted_values = pd.to_numeric(original_values, errors="coerce")

            invalid_mask = original_values.notna() & converted_values.isna()
            gene_invalid_count = int(invalid_mask.sum())

            cleaned_df[gene] = converted_values

            if gene_invalid_count > 0:
                invalid_value_count += gene_invalid_count
                affected_genes.append(gene)

                reason = (
                    "Non-numeric expression values were converted to missing values "
                    "because expression values must be numeric for QC and downstream analysis."
                )

                summary_rows.append(
                    {
                        "gene": gene,
                        "invalid_value_count": gene_invalid_count,
                        "decision": "converted_to_missing",
                        "status": "WARNING",
                        "reason": reason,
                    }
                )

                if audit_logger:
                    audit_logger.log(
                        module="Expression Value Cleaning",
                        action="Convert Non-Numeric Expression Values",
                        target=gene,
                        old_value=f"{gene_invalid_count} non-numeric values",
                        new_value="NaN",
                        rule_applied="convert_non_numeric_expression_values_to_missing",
                        decision="converted_to_missing",
                        status="WARNING",
                        reason=reason,
                    )

        return ExpressionValueCleaningResult(
            cleaned_dataframe=cleaned_df,
            invalid_value_count=invalid_value_count,
            affected_genes=affected_genes,
            invalid_value_summary=pd.DataFrame(summary_rows),
        )
