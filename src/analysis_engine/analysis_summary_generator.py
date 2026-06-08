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

        markdown_content = self._dataframe_to_markdown(
            summary_dataframe
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
    
    def _dataframe_to_markdown(
        self,
        dataframe: pd.DataFrame,
    ) -> str:

        clean_dataframe = dataframe.copy()

        clean_dataframe = clean_dataframe.dropna(
            axis=1,
            how="all",
        )

        clean_dataframe = clean_dataframe.fillna("")

        header = "| " + " | ".join(clean_dataframe.columns) + " |"
        separator = "| " + " | ".join(["---"] * len(clean_dataframe.columns)) + " |"

        rows = [
            "| " + " | ".join(str(value) for value in row) + " |"
            for row in clean_dataframe.to_numpy()
        ]

        return "\n".join([header, separator] + rows)
