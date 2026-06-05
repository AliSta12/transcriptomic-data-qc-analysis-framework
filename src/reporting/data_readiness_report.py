from dataclasses import dataclass
from pathlib import Path
import pandas as pd


DATA_READINESS_REPORT_COLUMNS = [
    "overall_status",
    "pass_count",
    "warning_count",
    "review_count",
    "details",
]


@dataclass
class DataReadinessReportResult:
    report_dataframe: pd.DataFrame
    output_path: Path | None = None


class DataReadinessReport:
    """
    Determines overall dataset readiness status.
    """

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add_summary(
        self,
        pass_count: int,
        warning_count: int,
        review_count: int,
        details: str,
    ) -> None:

        if review_count > 0:
            overall_status = "REQUIRES_REVIEW"

        elif warning_count > 0:
            overall_status = "READY_WITH_WARNINGS"

        else:
            overall_status = "READY_FOR_ANALYSIS"

        self.rows.append(
            {
                "overall_status": overall_status,
                "pass_count": pass_count,
                "warning_count": warning_count,
                "review_count": review_count,
                "details": details,
            }
        )

    def to_dataframe(self) -> pd.DataFrame:

        return pd.DataFrame(
            self.rows,
            columns=DATA_READINESS_REPORT_COLUMNS,
        )

    def save(
        self,
        output_path: str | Path,
    ) -> DataReadinessReportResult:

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

        return DataReadinessReportResult(
            report_dataframe=report_df,
            output_path=output_path,
        )
