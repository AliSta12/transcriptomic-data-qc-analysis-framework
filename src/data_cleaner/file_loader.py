from dataclasses import dataclass
from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".xlsx"}


@dataclass
class FileLoadResult:
    dataframe: pd.DataFrame
    filename: str
    file_type: str
    rows: int
    columns: int


class FileLoader:
    """
    Loader for transcriptomic expression matrices and metadata files.

    Supported formats:
    - CSV
    - TSV
    - XLSX
    """

    @staticmethod
    def load(file_path: str | Path) -> FileLoadResult:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        extension = path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        if extension == ".csv":
            dataframe = pd.read_csv(path)
        elif extension == ".tsv":
            dataframe = pd.read_csv(path, sep="\t")
        elif extension == ".xlsx":
            dataframe = pd.read_excel(path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

        return FileLoadResult(
            dataframe=dataframe,
            filename=path.name,
            file_type=extension,
            rows=dataframe.shape[0],
            columns=dataframe.shape[1],
        )
