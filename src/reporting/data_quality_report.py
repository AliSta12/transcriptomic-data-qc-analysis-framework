from dataclasses import dataclass
from pathlib import Path
import pandas as pd


DATA_QUALITY_REPORT_COLUMNS = [
    "check",
    "status",
    "metric",
    "threshold",
    "details",
]


@dataclass
class DataQualityReportResult:
    report_dataframe: pd.DataFrame
    output_path: Path | None = None


class DataQualityReport:
    """
    Aggregates QC results from Data Cleaner modules.
    """

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add_check(
        self,
        check: str,
        status: str,
        metric: str,
        threshold: str,
        details: str,
    ) -> None:

        self.rows.append(
            {
                "check": check,
                "status": status,
                "metric": metric,
                "threshold": threshold,
                "details": details,
            }
        )

    def to_dataframe(self) -> pd.DataFrame:

        return pd.DataFrame(
            self.rows,
            columns=DATA_QUALITY_REPORT_COLUMNS,
        )

    def save(
        self,
        output_path: str | Path,
    ) -> DataQualityReportResult:

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_df = self.to_dataframe()

        report_df.to_csv(
            output_path,
            index=False,
        )

        return DataQualityReportResult(
            report_dataframe=report_df,
            output_path=output_path,
        )
