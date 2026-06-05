from dataclasses import dataclass
import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger


@dataclass
class DuplicateDetectionResult:
    cleaned_dataframe: pd.DataFrame
    aggregated_genes: list[str]
    duplicate_samples: list[str]
    gene_duplicate_summary: pd.DataFrame
    sample_duplicate_summary: pd.DataFrame


class DuplicateDetector:
    """
    Detects duplicate genes and duplicate samples.

    Rules:

    Duplicate genes:
    - detect duplicates
    - aggregate using mean expression values
    - WARNING

    Duplicate samples:
    - detect duplicates
    - do not remove automatically
    - REQUIRES REVIEW
    """

    def apply_rules(
        self,
        dataframe: pd.DataFrame,
        audit_logger: AuditLogger | None = None,
    ) -> DuplicateDetectionResult:

        if "sample_id" not in dataframe.columns:
            raise ValueError("Input dataframe must contain 'sample_id' column.")

        cleaned_df = dataframe.copy()

        aggregated_genes: list[str] = []
        duplicate_samples: list[str] = []

        gene_summary_rows = []
        sample_summary_rows = []

        # --------------------------------------------------
        # Duplicate samples
        # --------------------------------------------------

        duplicated_sample_mask = cleaned_df["sample_id"].duplicated(keep=False)

        if duplicated_sample_mask.any():

            duplicated_samples = (
                cleaned_df.loc[duplicated_sample_mask, "sample_id"]
                .astype(str)
                .unique()
                .tolist()
            )

            for sample_id in duplicated_samples:

                duplicate_samples.append(sample_id)

                reason = (
                    "Duplicate sample detected. "
                    "Samples are not removed automatically."
                )

                sample_summary_rows.append(
                    {
                        "sample_id": sample_id,
                        "decision": "requires_review",
                        "status": "REQUIRES REVIEW",
                        "reason": reason,
                    }
                )

                if audit_logger:
                    audit_logger.log(
                        module="Duplicate Detection",
                        action="Duplicate Sample Detection",
                        target=sample_id,
                        old_value="duplicate_sample",
                        new_value="unchanged",
                        rule_applied="review_duplicate_sample",
                        decision="requires_review",
                        status="REQUIRES REVIEW",
                        reason=reason,
                    )

        # --------------------------------------------------
        # Duplicate genes
        # --------------------------------------------------

        gene_columns = [col for col in cleaned_df.columns if col != "sample_id"]

        duplicate_gene_names = [
            gene
            for gene in set(gene_columns)
            if gene_columns.count(gene) > 1
        ]

        if duplicate_gene_names:

            sample_ids = cleaned_df["sample_id"].copy()

            expression_df = cleaned_df.drop(columns=["sample_id"])

            aggregated_expression = (
                expression_df.T
                .groupby(level=0)
                .mean()
                .T
            )

            cleaned_df = pd.concat(
                [sample_ids, aggregated_expression],
                axis=1,
            )

            for gene in duplicate_gene_names:

                aggregated_genes.append(gene)

                reason = (
                    "Duplicate gene aggregated using mean expression values."
                )

                gene_summary_rows.append(
                    {
                        "gene": gene,
                        "decision": "aggregated",
                        "status": "WARNING",
                        "reason": reason,
                    }
                )

                if audit_logger:
                    audit_logger.log(
                        module="Duplicate Detection",
                        action="Duplicate Gene Aggregation",
                        target=gene,
                        old_value="duplicate_gene",
                        new_value="aggregated_mean",
                        rule_applied="aggregate_duplicate_gene",
                        decision="aggregated",
                        status="WARNING",
                        reason=reason,
                    )

        return DuplicateDetectionResult(
            cleaned_dataframe=cleaned_df,
            aggregated_genes=aggregated_genes,
            duplicate_samples=duplicate_samples,
            gene_duplicate_summary=pd.DataFrame(gene_summary_rows),
            sample_duplicate_summary=pd.DataFrame(sample_summary_rows),
        )
