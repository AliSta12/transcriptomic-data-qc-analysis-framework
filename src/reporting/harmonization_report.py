from dataclasses import dataclass
from pathlib import Path
import pandas as pd


HARMONIZATION_REPORT_COLUMNS = [
    "original_element",
    "standardized_element",
    "element_type",
    "transformation",
    "reason",
]


@dataclass
class HarmonizationReportResult:
    report_dataframe: pd.DataFrame
    output_path: Path | None = None


class HarmonizationReport:
    """
    Generates a harmonization report.

    This module does not transform data.
    It only documents structural changes performed earlier
    by the Data Cleaner.
    """

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add_entry(
        self,
        original_element: str,
        standardized_element: str,
        element_type: str,
        transformation: str,
        reason: str,
    ) -> None:
        if not reason:
            raise ValueError("Harmonization report entry must contain a reason.")

        self.rows.append(
            {
                "original_element": original_element,
                "standardized_element": standardized_element,
                "element_type": element_type,
                "transformation": transformation,
                "reason": reason,
            }
        )

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            self.rows,
            columns=HARMONIZATION_REPORT_COLUMNS,
        )

    def save(self, output_path: str | Path) -> HarmonizationReportResult:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_df = self.to_dataframe()
        report_df.to_csv(output_path, index=False)

        return HarmonizationReportResult(
            report_dataframe=report_df,
            output_path=output_path,
        )
