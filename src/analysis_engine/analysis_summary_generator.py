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

        summary_dataframe = pd.concat(
            summary_dataframes,
            ignore_index=True,
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
    
    def _summary_dataframes_to_markdown(
        self,
        summary_dataframes: list[pd.DataFrame],
    ) -> str:

        section_names = [
            "Dataset Overview",
            "Class Distribution",
            "Variable Gene Analysis",
            "PCA Analysis",
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
