import pytest

from src.data_cleaner.file_loader import FileLoader


def test_missing_file_raises_error():
    with pytest.raises(FileNotFoundError):
        FileLoader.load("does_not_exist.csv")


def test_unsupported_extension_raises_error(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("test")

    with pytest.raises(ValueError):
        FileLoader.load(file_path)
