from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class ClassDistributionResult:
    group_distribution: dict[str, int]
    plot_path: str
    summary_dataframe: pd.DataFrame


class ClassDistributionAnalysis:
    """
    Generates class distribution statistics and visualization.
    """

    def generate(
        self,
        metadata_df: pd.DataFrame,
        output_directory: str,
    ) -> ClassDistributionResult:

        self._validate_inputs(metadata_df)

        group_distribution = metadata_df["group"].value_counts().to_dict()

        summary_dataframe = pd.DataFrame(
            [
                {
                    "group": group,
                    "sample_count": count,
                }
                for group, count in group_distribution.items()
            ]
        )

        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        plot_path = output_dir / "class_distribution.png"

        plt.figure(figsize=(8, 5))
        plt.bar(
            group_distribution.keys(),
            group_distribution.values(),
        )
        plt.title("Class Distribution")
        plt.xlabel("Group")
        plt.ylabel("Sample Count")
        plt.tight_layout()
        plt.savefig(plot_path)
        plt.close()

        return ClassDistributionResult(
            group_distribution=group_distribution,
            plot_path=str(plot_path),
            summary_dataframe=summary_dataframe,
        )

    def _validate_inputs(
        self,
        metadata_df: pd.DataFrame,
    ) -> None:

        if "sample_id" not in metadata_df.columns:
            raise ValueError(
                "Metadata dataframe must contain 'sample_id' column."
            )

        if "group" not in metadata_df.columns:
            raise ValueError(
                "Metadata dataframe must contain 'group' column."
            )
