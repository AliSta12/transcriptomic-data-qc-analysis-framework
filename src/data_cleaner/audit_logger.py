from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import pandas as pd


AUDIT_LOG_COLUMNS = [
    "timestamp",
    "module",
    "action",
    "target",
    "old_value",
    "new_value",
    "rule_applied",
    "decision",
    "status",
    "reason",
]


VALID_STATUSES = {
    "PASS",
    "WARNING",
    "FAIL",
    "REQUIRES REVIEW",
}


@dataclass
class AuditLogEntry:
    timestamp: str
    module: str
    action: str
    target: str
    old_value: str
    new_value: str
    rule_applied: str
    decision: str
    status: str
    reason: str


class AuditLogger:
    """
    Stores automatic Data Cleaner decisions in a transparent audit log.

    Every entry answers:
    - what was detected or changed
    - what decision was made
    - why the decision was made
    """

    def __init__(self) -> None:
        self.entries: list[AuditLogEntry] = []

    def log(
        self,
        module: str,
        action: str,
        target: str,
        old_value: str,
        new_value: str,
        rule_applied: str,
        decision: str,
        status: str,
        reason: str,
    ) -> None:
        status = status.upper()

        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid audit status: {status}. "
                f"Allowed statuses: {sorted(VALID_STATUSES)}"
            )

        if not reason:
            raise ValueError("Audit log entry must contain a reason.")

        entry = AuditLogEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            module=module,
            action=action,
            target=target,
            old_value=str(old_value),
            new_value=str(new_value),
            rule_applied=rule_applied,
            decision=decision,
            status=status,
            reason=reason,
        )

        self.entries.append(entry)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [asdict(entry) for entry in self.entries],
            columns=AUDIT_LOG_COLUMNS,
        )

    def save(self, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df = self.to_dataframe()
        df.to_csv(output_path, index=False)

        return output_path
