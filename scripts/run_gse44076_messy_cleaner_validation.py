from pathlib import Path

import pandas as pd

from src.data_cleaner.data_cleaner_pipeline import DataCleanerPipeline


EXPRESSION_PATH = Path("data/processed/geo_gse44076_messy/expression_matrix.tsv")
METADATA_PATH = Path("data/processed/geo_gse44076_messy/metadata.tsv")
OUTPUT_DIR = Path("outputs/validation/geo_gse44076_messy")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    expression = pd.read_csv(EXPRESSION_PATH, sep="\t", dtype=str)
    metadata = pd.read_csv(METADATA_PATH, sep="\t", dtype=str)

    pipeline = DataCleanerPipeline()
    result = pipeline.run(
        expression_df=expression,
        metadata_df=metadata,
        output_directory=str(OUTPUT_DIR),
    )

    result.cleaned_expression_matrix.to_csv(
        OUTPUT_DIR / "clean_expression_matrix.csv",
        index=False,
    )
    result.clean_metadata.to_csv(
        OUTPUT_DIR / "clean_metadata.csv",
        index=False,
    )
    result.audit_log.to_csv(
        OUTPUT_DIR / "audit_log.csv",
        index=False,
    )
    result.harmonization_report.to_csv(
        OUTPUT_DIR / "harmonization_report.csv",
        index=False,
    )
    result.data_quality_report.to_csv(
        OUTPUT_DIR / "data_quality_report.csv",
        index=False,
    )
    result.data_readiness_report.to_csv(
        OUTPUT_DIR / "data_readiness_report.csv",
        index=False,
    )

    print("Data Cleaner validation completed.")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Clean expression shape: {result.cleaned_expression_matrix.shape}")
    print(f"Clean metadata shape: {result.clean_metadata.shape}")
    print(f"Final status: {result.final_status}")
    print(f"Missing data plot: {result.missing_data_plot_path}")
    print(f"QC status plot: {result.qc_status_summary_plot_path}")

    print("\nGenerated files:")
    for path in sorted(OUTPUT_DIR.glob("*")):
        print(f"- {path}")


if __name__ == "__main__":
    main()
