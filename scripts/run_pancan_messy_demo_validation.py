from pathlib import Path

import pandas as pd

from src.analysis_engine.analysis_engine_pipeline import AnalysisEnginePipeline
from src.data_cleaner.data_cleaner_pipeline import DataCleanerPipeline


EXPRESSION_PATH = Path("data/demo/pancan_messy/expression_matrix.tsv")
METADATA_PATH = Path("data/demo/pancan_messy/metadata.tsv")

OUTPUT_DIR = Path("outputs/validation/pancan_messy_demo")
CLEANER_OUTPUT_DIR = OUTPUT_DIR / "data_cleaner"
ANALYSIS_OUTPUT_DIR = OUTPUT_DIR / "analysis_engine"


def main() -> None:
    CLEANER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    expression = pd.read_csv(EXPRESSION_PATH, sep="\t", dtype=str)
    metadata = pd.read_csv(METADATA_PATH, sep="\t", dtype=str)

    cleaner = DataCleanerPipeline()
    cleaner_result = cleaner.run(
        expression_df=expression,
        metadata_df=metadata,
        output_directory=str(CLEANER_OUTPUT_DIR),
    )

    cleaner_result.cleaned_expression_matrix.to_csv(
        CLEANER_OUTPUT_DIR / "clean_expression_matrix.csv",
        index=False,
    )
    cleaner_result.clean_metadata.to_csv(
        CLEANER_OUTPUT_DIR / "clean_metadata.csv",
        index=False,
    )
    cleaner_result.audit_log.to_csv(
        CLEANER_OUTPUT_DIR / "audit_log.csv",
        index=False,
    )
    cleaner_result.harmonization_report.to_csv(
        CLEANER_OUTPUT_DIR / "harmonization_report.csv",
        index=False,
    )
    cleaner_result.data_quality_report.to_csv(
        CLEANER_OUTPUT_DIR / "data_quality_report.csv",
        index=False,
    )
    cleaner_result.data_readiness_report.to_csv(
        CLEANER_OUTPUT_DIR / "data_readiness_report.csv",
        index=False,
    )

    expression_values = cleaner_result.cleaned_expression_matrix.drop(
        columns=["sample_id"],
        errors="ignore",
    )
    remaining_missing_values = int(expression_values.isna().sum().sum())

    print("Data Cleaner completed.")
    print(f"Cleaner final status: {cleaner_result.final_status}")
    print(f"Clean expression shape: {cleaner_result.cleaned_expression_matrix.shape}")
    print(f"Clean metadata shape: {cleaner_result.clean_metadata.shape}")
    print(f"Remaining missing expression values: {remaining_missing_values}")

    if cleaner_result.final_status == "REQUIRES_REVIEW":
        raise RuntimeError("Analysis blocked: Data Cleaner returned REQUIRES_REVIEW.")

    if remaining_missing_values > 0:
        raise RuntimeError("Analysis blocked: cleaned expression matrix still contains missing values.")

    analysis = AnalysisEnginePipeline()
    analysis_result = analysis.run(
        expression_df=cleaner_result.cleaned_expression_matrix,
        metadata_df=cleaner_result.clean_metadata,
        output_directory=str(ANALYSIS_OUTPUT_DIR),
    )

    print("\nAnalysis Engine completed.")
    print(f"Analysis output directory: {ANALYSIS_OUTPUT_DIR}")

    print("\nGenerated Data Cleaner files:")
    for path in sorted(CLEANER_OUTPUT_DIR.glob("*")):
        print(f"- {path}")

    print("\nGenerated Analysis Engine files:")
    for path in sorted(ANALYSIS_OUTPUT_DIR.glob("*")):
        print(f"- {path}")


if __name__ == "__main__":
    main()
