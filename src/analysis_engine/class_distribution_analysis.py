from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.analysis_engine.group_colors import get_group_color_map


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

        groups = list(group_distribution.keys())
        counts = list(group_distribution.values())
        total_samples = sum(counts)

        group_color_map = get_group_color_map(groups)
        bar_colors = [
            group_color_map[group]
            for group in groups
        ]

        plt.figure(figsize=(9, 6))

        bars = plt.bar(
            groups,
            counts,
            color=bar_colors,
            edgecolor="white",
            linewidth=1.0,
        )

        plt.title(
            f"Class Distribution (n={total_samples})"
        )
        plt.xlabel("Group")
        plt.ylabel("Sample Count")

        for bar, count in zip(bars, counts):
            percentage = (
                count / total_samples * 100
                if total_samples > 0
                else 0
            )

            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{count}\n({percentage:.1f}%)",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        max_count = max(counts) if counts else 0
        upper_limit = max_count * 1.15 if max_count > 0 else 1
        plt.ylim(0, upper_limit)

        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        plt.savefig(
            plot_path,
            dpi=300,
            bbox_inches="tight",
        )
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
