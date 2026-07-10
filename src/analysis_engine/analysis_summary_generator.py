from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class AnalysisSummaryGeneratorResult:
    summary_dataframe: pd.DataFrame
    csv_path: str
    markdown_path: str


class AnalysisSummaryGenerator:
    """
    Generates consolidated analysis summary files.

    This module collects summary tables produced by
    previous analysis modules and exports them as:

    - analysis_summary.csv
    - analysis_summary.md
    """

    def generate(
        self,
        summary_dataframes: list[pd.DataFrame],
        output_directory: str,
    ) -> AnalysisSummaryGeneratorResult:

        self._validate_inputs(summary_dataframes)

        summary_dataframe = self._build_readable_summary(
            summary_dataframes=summary_dataframes,
        )

        output_dir = Path(output_directory)
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        csv_path = output_dir / "analysis_summary.csv"
        markdown_path = output_dir / "analysis_summary.md"

        summary_dataframe.to_csv(
            csv_path,
            index=False,
        )

        markdown_content = self._summary_dataframes_to_markdown(
            summary_dataframes
        )

        markdown_path.write_text(
            markdown_content,
            encoding="utf-8",
        )

        return AnalysisSummaryGeneratorResult(
            summary_dataframe=summary_dataframe,
            csv_path=str(csv_path),
            markdown_path=str(markdown_path),
        )

    def _validate_inputs(
        self,
        summary_dataframes: list[pd.DataFrame],
    ) -> None:

        if not summary_dataframes:
            raise ValueError(
                "At least one summary dataframe is required."
            )

        for dataframe in summary_dataframes:
            if dataframe.empty:
                raise ValueError(
                    "Summary dataframes cannot be empty."
                )

    def _build_readable_summary(
        self,
        summary_dataframes: list[pd.DataFrame],
    ) -> pd.DataFrame:
        
        if len(summary_dataframes) < 6:
            return pd.concat(
                summary_dataframes,
                ignore_index=True,
            )

        dataset_overview = summary_dataframes[0]
        class_distribution = summary_dataframes[1]
        variable_gene_analysis = summary_dataframes[2]
        pca_analysis = summary_dataframes[3]
        heatmap = summary_dataframes[4]
        sample_clustering = summary_dataframes[5]

        overview_values = dict(
            zip(dataset_overview["metric"], dataset_overview["value"])
        )

        variable_values = dict(
            zip(variable_gene_analysis["metric"], variable_gene_analysis["value"])
        )

        pca_values = dict(
            zip(pca_analysis["metric"], pca_analysis["value"])
        )

        heatmap_values = dict(
            zip(heatmap["metric"], heatmap["value"])
        )

        clustering_values = dict(
            zip(sample_clustering["metric"], sample_clustering["value"])
        )

        class_distribution_text = "; ".join(
            f"{row['group']}: {int(row['sample_count'])}"
            for _, row in class_distribution.iterrows()
        )

        return pd.DataFrame(
            [
                {
                    "analysis_step": "Dataset Overview",
                    "result": (
                        f"{int(overview_values['sample_count'])} samples, "
                        f"{int(overview_values['gene_count'])} genes, "
                        f"{int(overview_values['group_count'])} groups"
                    ),
                },
                {
                    "analysis_step": "Class Distribution",
                    "result": class_distribution_text,
                },
                {
                    "analysis_step": "PCA Analysis",
                    "result": (
                        f"PCA plot generated; PC1 explains "
                        f"{float(pca_values['pc1_variance_explained']) * 100:.1f}% "
                        f"and PC2 explains "
                        f"{float(pca_values['pc2_variance_explained']) * 100:.1f}% "
                        "of variance"
                    ),
                },
                {
                    "analysis_step": "Variable Gene Analysis",
                    "result": (
                        f"{int(variable_values['total_genes_analyzed'])} genes analyzed; "
                        "top 50 and top 100 variable genes exported"
                    ),
                },
                
                {
                    "analysis_step": "Heatmap",
                    "result": (
                        f"Heatmap generated for top "
                        f"{int(heatmap_values['gene_count'])} variable genes"
                    ),
                },
                {
                    "analysis_step": "Sample Clustering",
                    "result": (
                        f"Hierarchical clustering generated using "
                        f"{clustering_values['clustering_method']} method"
                    ),
                },
            ]
        )

    def _summary_dataframes_to_markdown(
        self,
        summary_dataframes: list[pd.DataFrame],
    ) -> str:

        section_names = [
            "Dataset Overview",
            "Class Distribution",
            "PCA Analysis",
            "Variable Gene Analysis",
            "Heatmap",
            "Sample Clustering",
        ]

        sections = [
            "# Transcriptomic Analysis Summary",
            "",
        ]

        for index, dataframe in enumerate(summary_dataframes):
            section_name = (
                section_names[index]
                if index < len(section_names)
                else f"Analysis Section {index + 1}"
            )

            clean_dataframe = dataframe.copy()
            clean_dataframe = clean_dataframe.fillna("")

            sections.extend(
                [
                    f"## {section_name}",
                    "",
                ]
            )

            sections.extend(
                self._records_to_markdown_table(
                    self._format_dataframe_columns(clean_dataframe)
                )
            )

            sections.append("")

        sections.extend(
            [
                "## Methodological Note",
                "",
                (
                    "This report summarizes exploratory transcriptomic analysis only. "
                    "The most variable genes, PCA, heatmap and clustering results are "
                    "intended for quality assessment and exploratory visualization. "
                    "They should not be interpreted as formal differential expression results."
                ),
                "",
            ]
        )

        return "\n".join(sections).strip()
    
    def _format_dataframe_columns(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        return dataframe.rename(
            columns={
                "metric": "Metric",
                "value": "Value",
                "group": "Group",
                "sample_count": "Sample Count",
                "gene_count": "Gene Count",
                "clustering_method": "Clustering Method",
            }
        )
    def _records_to_markdown_table(
        self,
        dataframe: pd.DataFrame,
    ) -> list[str]:

        if dataframe.empty:
            return []

        header = "| " + " | ".join(dataframe.columns) + " |"
        separator = "| " + " | ".join(["---"] * len(dataframe.columns)) + " |"

        rows = [
            "| " + " | ".join(str(value) for value in row) + " |"
            for row in dataframe.to_numpy()
        ]

        return [header, separator] + rows
