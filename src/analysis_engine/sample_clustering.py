from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch
from scipy.cluster.hierarchy import dendrogram, linkage

from src.analysis_engine.group_colors import get_group_color_map

MAX_SAMPLE_LABELS_FOR_DENDROGRAM = 50


@dataclass
class SampleClusteringResult:
    linkage_matrix: list
    plot_path: str
    summary_dataframe: pd.DataFrame


class SampleClustering:
    """
    Performs hierarchical clustering of samples and generates a dendrogram.

    This module expects:
    - expression matrix in sample x gene format
    - first column named sample_id

    Optional metadata can be used to color leaf-tip markers
    according to biological groups from the metadata.
    """

    def generate(
        self,
        expression_df: pd.DataFrame,
        output_directory: str,
        metadata_df: pd.DataFrame | None = None,
    ) -> SampleClusteringResult:

        self._validate_inputs(expression_df)

        gene_columns = [
            column
            for column in expression_df.columns
            if column != "sample_id"
        ]

        expression_values = expression_df[gene_columns]

        linkage_matrix = linkage(
            expression_values,
            method="ward",
        )

        output_dir = Path(output_directory)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        plot_path = output_dir / "sample_clustering_dendrogram.png"

        sample_count = len(expression_df)
        show_sample_labels = (
            sample_count <= MAX_SAMPLE_LABELS_FOR_DENDROGRAM
        )

        group_annotation = self._build_group_annotation(
            expression_df=expression_df,
            metadata_df=metadata_df,
        )

        group_annotation_available = group_annotation is not None

        figure, dendrogram_axis = plt.subplots(
            figsize=(18, 8),
        )

        dendrogram_result = dendrogram(
            linkage_matrix,
            labels=expression_df["sample_id"].tolist(),
            no_labels=not show_sample_labels,
            leaf_rotation=90,
            color_threshold=0,
            above_threshold_color="#6e6e6e",
            ax=dendrogram_axis,
        )

        for line_collection in dendrogram_axis.collections:
            line_collection.set_color("#6e6e6e")
            line_collection.set_linewidth(0.55)
            line_collection.set_alpha(0.85)

        dendrogram_axis.set_title(
            f"Hierarchical Clustering of Samples by Expression Profile "
            f"(n={sample_count})"
        )

        dendrogram_axis.set_xlabel(
            "Samples"
        )

        dendrogram_axis.set_ylabel(
            "Ward linkage distance"
        )

        if group_annotation_available:
            self._draw_colored_leaf_tip_markers(
                dendrogram_axis=dendrogram_axis,
                dendrogram_result=dendrogram_result,
                group_annotation=group_annotation,
                linkage_matrix=linkage_matrix,
            )

            legend_handles = [
                Patch(
                    facecolor=group_data["color"],
                    edgecolor="none",
                    label=group_name,
                )
                for group_name, group_data in group_annotation[
                    "group_to_color"
                ].items()
            ]

            dendrogram_axis.legend(
                handles=legend_handles,
                title="Group",
                loc="upper left",
                bbox_to_anchor=(1.01, 1.0),
                frameon=True,
            )

            figure.subplots_adjust(
                right=0.84,
                bottom=0.12,
            )
        else:
            figure.tight_layout()

        figure.savefig(
            plot_path,
            dpi=300,
            bbox_inches="tight",
        )
        plt.close(figure)

        summary_dataframe = pd.DataFrame(
            [
                {
                    "metric": "sample_count",
                    "value": len(expression_df),
                },
                {
                    "metric": "gene_count",
                    "value": len(gene_columns),
                },
                {
                    "metric": "clustering_method",
                    "value": "ward",
                },
                {
                    "metric": "group_annotation_available",
                    "value": group_annotation_available,
                },
            ]
        )

        return SampleClusteringResult(
            linkage_matrix=linkage_matrix.tolist(),
            plot_path=str(plot_path),
            summary_dataframe=summary_dataframe,
        )

    def _build_group_annotation(
        self,
        expression_df: pd.DataFrame,
        metadata_df: pd.DataFrame | None,
    ) -> dict | None:

        if metadata_df is None:
            return None

        required_columns = {
            "sample_id",
            "group",
        }

        if not required_columns.issubset(metadata_df.columns):
            return None

        metadata_subset = metadata_df[
            [
                "sample_id",
                "group",
            ]
        ].dropna()

        sample_to_group = dict(
            zip(
                metadata_subset["sample_id"],
                metadata_subset["group"],
            )
        )

        sample_ids = expression_df["sample_id"].tolist()

        if not all(sample_id in sample_to_group for sample_id in sample_ids):
            return None

        groups = [
            sample_to_group[sample_id]
            for sample_id in sample_ids
        ]

        group_color_map = get_group_color_map(groups)

        group_to_color = {
            group: {
                "color": color,
            }
            for group, color in group_color_map.items()
        }

        sample_to_color = {
            sample_id: group_to_color[sample_to_group[sample_id]]["color"]
            for sample_id in sample_ids
        }

        return {
            "sample_ids": sample_ids,
            "sample_to_group": sample_to_group,
            "sample_to_color": sample_to_color,
            "group_to_color": group_to_color,
        }

    def _draw_colored_leaf_tip_markers(
        self,
        dendrogram_axis,
        dendrogram_result: dict,
        group_annotation: dict,
        linkage_matrix,
    ) -> None:

        sample_ids = group_annotation["sample_ids"]
        ordered_sample_ids = [
            sample_ids[index]
            for index in dendrogram_result["leaves"]
        ]

        ordered_colors = [
            group_annotation["sample_to_color"][sample_id]
            for sample_id in ordered_sample_ids
        ]

        leaf_x_positions = [
            5 + 10 * index
            for index in range(len(ordered_sample_ids))
        ]

        max_distance = float(linkage_matrix[:, 2].max())
        marker_height = max_distance * 0.045

        dendrogram_axis.vlines(
            x=leaf_x_positions,
            ymin=-marker_height,
            ymax=0,
            colors=ordered_colors,
            linewidth=2.2,
            alpha=0.95,
            clip_on=False,
        )

        dendrogram_axis.set_ylim(
            -marker_height * 1.25,
            max_distance * 1.05,
        )

    def _validate_inputs(
        self,
        expression_df: pd.DataFrame,
    ) -> None:

        if "sample_id" not in expression_df.columns:
            raise ValueError(
                "Expression dataframe must contain 'sample_id' column."
            )

        gene_columns = [
            column
            for column in expression_df.columns
            if column != "sample_id"
        ]

        if not gene_columns:
            raise ValueError(
                "Expression dataframe must contain at least one gene column."
            )

        if len(expression_df) < 2:
            raise ValueError(
                "Sample clustering requires at least two samples."
            )

        non_numeric_columns = [
            column
            for column in gene_columns
            if not pd.api.types.is_numeric_dtype(expression_df[column])
        ]

        if non_numeric_columns:
            raise ValueError(
                "All gene expression columns must be numeric. "
                f"Non-numeric columns detected: {non_numeric_columns}"
            )
