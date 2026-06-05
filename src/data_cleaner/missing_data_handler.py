from dataclasses import dataclass
import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger


@dataclass
class MissingDataResult:
    cleaned_dataframe: pd.DataFrame
    imputed_genes: list[str]
    removed_genes: list[str]
    review_samples: list[str]
    total_missing_values: int
    gene_missing_summary: pd.DataFrame
    sample_missing_summary: pd.DataFrame


class MissingDataHandler:
    """
    Handles missing values according to transparent rule-based cleaning.

    Rules:
    - missing per gene <= 5%: impute by gene median
    - 5% < missing per gene <= 20%: keep unchanged, report WARNING
    - missing per gene > 20%: remove gene from analytical dataset
    - missing per sample > 20%: keep sample, mark as REQUIRES REVIEW
    """

    def __init__(
        self,
        low_missing_threshold: float = 0.05,
        high_missing_threshold: float = 0.20,
        sample_review_threshold: float = 0.20,
    ) -> None:
        self.low_missing_threshold = low_missing_threshold
        self.high_missing_threshold = high_missing_threshold
        self.sample_review_threshold = sample_review_threshold

    def apply_rules(
        self,
        dataframe: pd.DataFrame,
        audit_logger: AuditLogger | None = None,
    ) -> MissingDataResult:
        if "sample_id" not in dataframe.columns:
            raise ValueError("Input dataframe must contain 'sample_id' column.")

        cleaned_df = dataframe.copy()
        original_df = dataframe.copy() 
        gene_columns = [col for col in cleaned_df.columns if col != "sample_id"]

        total_missing_values = int(cleaned_df[gene_columns].isna().sum().sum())

        imputed_genes: list[str] = []
        removed_genes: list[str] = []
        review_samples: list[str] = []

        gene_summary_rows = []
        sample_summary_rows = []

        number_of_samples = len(cleaned_df)

        for gene in gene_columns:
            missing_count = int(cleaned_df[gene].isna().sum())
            missing_fraction = missing_count / number_of_samples if number_of_samples > 0 else 0

            if missing_count == 0:
                decision = "no_action"
                status = "PASS"
                reason = "Gene contains no missing values."

            elif missing_fraction <= self.low_missing_threshold:
                median_value = cleaned_df[gene].median()
                cleaned_df[gene] = cleaned_df[gene].fillna(median_value)
                imputed_genes.append(gene)

                decision = "imputed"
                status = "WARNING"
                reason = "Missing values below or equal to 5% were imputed using gene median."

                if audit_logger:
                    audit_logger.log(
                        module="Missing Data",
                        action="Median Imputation",
                        target=gene,
                        old_value="missing_values",
                        new_value=median_value,
                        rule_applied="impute_low_missing_gene",
                        decision=decision,
                        status=status,
                        reason=reason,
                    )

            elif missing_fraction <= self.high_missing_threshold:
                decision = "kept_with_warning"
                status = "WARNING"
                reason = "Missing values between 5% and 20% were retained without automatic imputation."

                if audit_logger:
                    audit_logger.log(
                        module="Missing Data",
                        action="Keep Gene With Missing Values",
                        target=gene,
                        old_value=f"{missing_count} missing values",
                        new_value="unchanged",
                        rule_applied="keep_moderate_missing_gene",
                        decision=decision,
                        status=status,
                        reason=reason,
                    )

            else:
                cleaned_df = cleaned_df.drop(columns=[gene])
                removed_genes.append(gene)

                decision = "removed"
                status = "WARNING"
                reason = "Gene missing values exceeded 20%; gene was removed from analytical dataset."

                if audit_logger:
                    audit_logger.log(
                        module="Missing Data",
                        action="Remove High-Missing Gene",
                        target=gene,
                        old_value=f"{missing_count} missing values",
                        new_value="removed",
                        rule_applied="remove_high_missing_gene",
                        decision=decision,
                        status=status,
                        reason=reason,
                    )

            gene_summary_rows.append(
                {
                    "gene": gene,
                    "missing_count": missing_count,
                    "missing_fraction": missing_fraction,
                    "decision": decision,
                    "status": status,
                    "reason": reason,
                }
            )

        original_gene_columns = [col for col in original_df.columns if col != "sample_id"]
        number_of_genes = len(original_gene_columns)

        for _, row in original_df.iterrows():
            sample_id = row["sample_id"]

            missing_count = int(row[original_gene_columns].isna().sum())
            missing_fraction = missing_count / number_of_genes if number_of_genes > 0 else 0

            if missing_fraction > self.sample_review_threshold:
                decision = "requires_review"
                status = "REQUIRES REVIEW"
                reason = "Sample missing values exceeded 20%; sample retained but requires user review."
                review_samples.append(sample_id)

                if audit_logger:
                    audit_logger.log(
                        module="Missing Data",
                        action="Mark Sample For Review",
                        target=sample_id,
                        old_value=f"{missing_count} missing values",
                        new_value="retained",
                        rule_applied="review_high_missing_sample",
                        decision=decision,
                        status=status,
                        reason=reason,
                    )
            else:
                decision = "no_action"
                status = "PASS"
                reason = "Sample missing values are within acceptable threshold."

            sample_summary_rows.append(
                {
                    "sample_id": sample_id,
                    "missing_count": missing_count,
                    "missing_fraction": missing_fraction,
                    "decision": decision,
                    "status": status,
                    "reason": reason,
                }
            )

        return MissingDataResult(
            cleaned_dataframe=cleaned_df,
            imputed_genes=imputed_genes,
            removed_genes=removed_genes,
            review_samples=review_samples,
            total_missing_values=total_missing_values,
            gene_missing_summary=pd.DataFrame(gene_summary_rows),
            sample_missing_summary=pd.DataFrame(sample_summary_rows),
        )
