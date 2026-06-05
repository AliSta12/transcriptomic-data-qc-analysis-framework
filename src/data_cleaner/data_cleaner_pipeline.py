from dataclasses import dataclass
import pandas as pd

from src.data_cleaner.audit_logger import AuditLogger
from src.data_cleaner.structure_detector import StructureDetector
from src.data_cleaner.harmonizer import Harmonizer
from src.data_cleaner.missing_data_handler import MissingDataHandler
from src.data_cleaner.duplicate_detector import DuplicateDetector
from src.data_cleaner.metadata_consistency_checker import MetadataConsistencyChecker
from src.data_cleaner.constant_gene_detector import ConstantGeneDetector
from src.data_cleaner.low_variance_gene_detector import LowVarianceGeneDetector
from src.reporting.harmonization_report import HarmonizationReport
from src.reporting.data_quality_report import DataQualityReport
from src.reporting.data_readiness_report import DataReadinessReport


@dataclass
class DataCleanerPipelineResult:
    cleaned_expression_matrix: pd.DataFrame
    clean_metadata: pd.DataFrame
    audit_log: pd.DataFrame
    harmonization_report: pd.DataFrame
    data_quality_report: pd.DataFrame
    data_readiness_report: pd.DataFrame
    final_status: str


class DataCleanerPipeline:
    """
    Orchestrates the complete Data Cleaner workflow.

    Input:
    - expression dataframe
    - metadata dataframe

    Output:
    - cleaned expression matrix
    - clean metadata
    - audit log
    - harmonization report
    - data quality report
    - data readiness report
    """

    def __init__(self) -> None:
        self.audit_logger = AuditLogger()

    def run(
        self,
        expression_df: pd.DataFrame,
        metadata_df: pd.DataFrame,
    ) -> DataCleanerPipelineResult:

        # 1. Detect expression matrix orientation
        detector = StructureDetector()
        detection_result = detector.detect(expression_df)

        # 2. Harmonize expression matrix
        harmonizer = Harmonizer()

        harmonized_df = harmonizer.harmonize_expression_matrix(
        expression_df,
        detection_result.orientation,
        )

        # 3. Harmonization report
        harmonization_report = HarmonizationReport()
        harmonization_report.add_entry(
            original_element=detection_result.orientation.value,
            standardized_element="sample x gene",
            element_type="data_orientation",
            transformation=(
                "transposed"
                if detection_result.orientation.value == "gene x sample"
                else "preserved"
            ),
            reason="Analysis engine requires standardized sample x gene format.",
        )

        # 4. Missing data handling
        missing_handler = MissingDataHandler()
        missing_result = missing_handler.apply_rules(
            harmonized_df,
            self.audit_logger,
        )

        current_df = missing_result.cleaned_dataframe

        # 5. Duplicate detection
        duplicate_detector = DuplicateDetector()
        duplicate_result = duplicate_detector.apply_rules(
            current_df,
            self.audit_logger,
        )

        current_df = duplicate_result.cleaned_dataframe

        # 6. Metadata consistency check
        metadata_checker = MetadataConsistencyChecker()
        metadata_result = metadata_checker.check(
            current_df,
            metadata_df,
            self.audit_logger,
        )

        # 7. Constant gene detection
        constant_detector = ConstantGeneDetector()
        constant_result = constant_detector.apply_rules(
            current_df,
            self.audit_logger,
        )

        current_df = constant_result.cleaned_dataframe

        # 8. Low variance gene detection
        low_variance_detector = LowVarianceGeneDetector()
        low_variance_result = low_variance_detector.apply_rules(
            current_df,
            self.audit_logger,
        )

        current_df = low_variance_result.cleaned_dataframe

        # 9. Data quality report
        quality_report = DataQualityReport()

        quality_report.add_check(
            check="Missing Data",
            status=(
                "WARNING"
                if missing_result.total_missing_values > 0
                else "PASS"
            ),
            metric=str(missing_result.total_missing_values),
            threshold="gene <=5% impute; gene >20% remove; sample >20% review",
            details="Missing data rules were applied.",
        )

        quality_report.add_check(
            check="Duplicate Samples",
            status=(
                "REQUIRES REVIEW"
                if duplicate_result.duplicate_samples
                else "PASS"
            ),
            metric=str(len(duplicate_result.duplicate_samples)),
            threshold="0 duplicate samples",
            details="Duplicate samples are not removed automatically.",
        )

        quality_report.add_check(
            check="Duplicate Genes",
            status=(
                "WARNING"
                if duplicate_result.aggregated_genes
                else "PASS"
            ),
            metric=str(len(duplicate_result.aggregated_genes)),
            threshold="0 duplicate genes",
            details="Duplicate genes are aggregated using mean expression values.",
        )

        quality_report.add_check(
            check="Metadata Consistency",
            status=metadata_result.status,
            metric=str(len(metadata_result.summary_dataframe)),
            threshold="0 issues",
            details="Expression samples and metadata samples were compared.",
        )

        quality_report.add_check(
            check="Constant Genes",
            status=(
                "WARNING"
                if constant_result.removed_gene_count > 0
                else "PASS"
            ),
            metric=str(constant_result.removed_gene_count),
            threshold="0 constant genes",
            details="Constant genes were removed from analytical dataset.",
        )

        quality_report.add_check(
            check="Low Variance Genes",
            status=(
                "WARNING"
                if low_variance_result.removed_gene_count > 0
                else "PASS"
            ),
            metric=str(low_variance_result.removed_gene_count),
            threshold=f"variance < {low_variance_result.variance_threshold}",
            details="Low variance genes were removed from analytical dataset.",
        )

        quality_df = quality_report.to_dataframe()

        # 10. Data readiness report
        pass_count = int((quality_df["status"] == "PASS").sum())
        warning_count = int((quality_df["status"] == "WARNING").sum())
        review_count = int((quality_df["status"] == "REQUIRES REVIEW").sum())

        readiness_report = DataReadinessReport()
        readiness_report.add_summary(
            pass_count=pass_count,
            warning_count=warning_count,
            review_count=review_count,
            details="Dataset readiness was assessed based on QC statuses.",
        )

        readiness_df = readiness_report.to_dataframe()
        final_status = readiness_df.loc[0, "overall_status"]

        return DataCleanerPipelineResult(
            cleaned_expression_matrix=current_df,
            clean_metadata=metadata_df.copy(),
            audit_log=self.audit_logger.to_dataframe(),
            harmonization_report=harmonization_report.to_dataframe(),
            data_quality_report=quality_df,
            data_readiness_report=readiness_df,
            final_status=final_status,
        )
