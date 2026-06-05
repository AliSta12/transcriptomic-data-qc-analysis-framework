from dataclasses import dataclass
import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger


@dataclass
class MetadataConsistencyResult:
    missing_metadata_samples: list[str]
    extra_metadata_samples: list[str]
    duplicated_metadata_samples: list[str]
    samples_without_group: list[str]
    status: str
    summary_dataframe: pd.DataFrame


class MetadataConsistencyChecker:
    """
    Checks consistency between expression matrix
    and metadata file.

    Rules:
    - expression samples without metadata -> REQUIRES REVIEW
    - metadata samples not present in expression matrix -> WARNING
    - duplicated sample_id in metadata -> REQUIRES REVIEW
    - missing group values -> REQUIRES REVIEW
    """

    def check(
        self,
        expression_df: pd.DataFrame,
        metadata_df: pd.DataFrame,
        audit_logger: AuditLogger | None = None,
    ) -> MetadataConsistencyResult:

        if "sample_id" not in expression_df.columns:
            raise ValueError(
                "Expression matrix must contain 'sample_id' column."
            )

        if "sample_id" not in metadata_df.columns:
            raise ValueError(
                "Metadata must contain 'sample_id' column."
            )

        if "group" not in metadata_df.columns:
            raise ValueError(
                "Metadata must contain 'group' column."
            )

        expression_samples = set(
            expression_df["sample_id"].astype(str)
        )

        metadata_samples = set(
            metadata_df["sample_id"].astype(str)
        )

        missing_metadata_samples = sorted(
            expression_samples - metadata_samples
        )

        extra_metadata_samples = sorted(
            metadata_samples - expression_samples
        )

        duplicated_metadata_samples = (
            metadata_df.loc[
                metadata_df["sample_id"].duplicated(keep=False),
                "sample_id"
            ]
            .astype(str)
            .unique()
            .tolist()
        )

        samples_without_group = (
            metadata_df.loc[
                metadata_df["group"].isna(),
                "sample_id"
            ]
            .astype(str)
            .tolist()
        )

        summary_rows = []

        # Missing metadata samples

        for sample in missing_metadata_samples:

            reason = (
                "Sample exists in expression matrix "
                "but has no metadata."
            )

            summary_rows.append(
                {
                    "target": sample,
                    "check": "missing_metadata",
                    "status": "REQUIRES REVIEW",
                    "reason": reason,
                }
            )

            if audit_logger:
                audit_logger.log(
                    module="Metadata Consistency",
                    action="Missing Metadata",
                    target=sample,
                    old_value="missing",
                    new_value="unchanged",
                    rule_applied="detect_missing_metadata",
                    decision="requires_review",
                    status="REQUIRES REVIEW",
                    reason=reason,
                )

        # Extra metadata samples

        for sample in extra_metadata_samples:

            reason = (
                "Metadata contains sample not found "
                "in expression matrix."
            )

            summary_rows.append(
                {
                    "target": sample,
                    "check": "extra_metadata",
                    "status": "WARNING",
                    "reason": reason,
                }
            )

            if audit_logger:
                audit_logger.log(
                    module="Metadata Consistency",
                    action="Extra Metadata Sample",
                    target=sample,
                    old_value="present",
                    new_value="unchanged",
                    rule_applied="detect_extra_metadata",
                    decision="warning",
                    status="WARNING",
                    reason=reason,
                )

        # Duplicate metadata samples

        for sample in duplicated_metadata_samples:

            reason = (
                "Duplicate sample_id detected in metadata."
            )

            summary_rows.append(
                {
                    "target": sample,
                    "check": "duplicate_metadata",
                    "status": "REQUIRES REVIEW",
                    "reason": reason,
                }
            )

            if audit_logger:
                audit_logger.log(
                    module="Metadata Consistency",
                    action="Duplicate Metadata Sample",
                    target=sample,
                    old_value="duplicate",
                    new_value="unchanged",
                    rule_applied="detect_duplicate_metadata",
                    decision="requires_review",
                    status="REQUIRES REVIEW",
                    reason=reason,
                )

        # Missing group

        for sample in samples_without_group:

            reason = (
                "Sample does not have assigned group."
            )

            summary_rows.append(
                {
                    "target": sample,
                    "check": "missing_group",
                    "status": "REQUIRES REVIEW",
                    "reason": reason,
                }
            )

            if audit_logger:
                audit_logger.log(
                    module="Metadata Consistency",
                    action="Missing Group",
                    target=sample,
                    old_value="missing",
                    new_value="unchanged",
                    rule_applied="detect_missing_group",
                    decision="requires_review",
                    status="REQUIRES REVIEW",
                    reason=reason,
                )

        if any(
            [
                missing_metadata_samples,
                duplicated_metadata_samples,
                samples_without_group,
            ]
        ):
            status = "REQUIRES REVIEW"

        elif extra_metadata_samples:
            status = "WARNING"

        else:
            status = "PASS"

        return MetadataConsistencyResult(
            missing_metadata_samples=missing_metadata_samples,
            extra_metadata_samples=extra_metadata_samples,
            duplicated_metadata_samples=duplicated_metadata_samples,
            samples_without_group=samples_without_group,
            status=status,
            summary_dataframe=pd.DataFrame(summary_rows),
        )
