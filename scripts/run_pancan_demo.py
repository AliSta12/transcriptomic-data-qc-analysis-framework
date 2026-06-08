from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.data_cleaner.data_cleaner_pipeline import DataCleanerPipeline
from src.data_cleaner.metadata_harmonizer import MetadataHarmonizer
from src.analysis_engine.analysis_engine_pipeline import AnalysisEnginePipeline


RAW_DATA_DIR = Path("data/raw/pancan/TCGA-PANCAN-HiSeq-801x20531")
OUTPUT_DIR = Path("outputs/pancan_demo")


def main() -> None:
    expression_df = pd.read_csv(RAW_DATA_DIR / "data.csv")
    metadata_df = pd.read_csv(RAW_DATA_DIR / "labels.csv")

    metadata_df = MetadataHarmonizer.harmonize_metadata(metadata_df)

    cleaner_result = DataCleanerPipeline().run(
        expression_df=expression_df,
        metadata_df=metadata_df,
    )

    analysis_result = AnalysisEnginePipeline().run(
        expression_df=cleaner_result.cleaned_expression_matrix,
        metadata_df=cleaner_result.clean_metadata,
        output_directory=str(OUTPUT_DIR),
    )

    print("PANCAN demo completed.")
    print(f"Final cleaner status: {cleaner_result.final_status}")
    print(f"Samples: {analysis_result.dataset_overview.sample_count}")
    print(f"Genes: {analysis_result.dataset_overview.gene_count}")
    print(f"Groups: {analysis_result.dataset_overview.group_count}")
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
