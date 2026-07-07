import pandas as pd

from src.dataset_intake.file_discovery import run_dataset_intake


def test_run_dataset_intake_marks_auto_selected_files_in_discovery_report(tmp_path):
    dataset_dir = tmp_path / "dataset"
    output_dir = tmp_path / "outputs"
    dataset_dir.mkdir()

    expression_data = {
        "sample_id": [f"S{i}" for i in range(60)],
    }

    for gene_index in range(25):
        expression_data[f"GENE_{gene_index}"] = [
            float(sample_index + gene_index)
            for sample_index in range(60)
        ]

    expression_df = pd.DataFrame(expression_data)
    expression_df.to_csv(dataset_dir / "data.csv", index=False)

    metadata_df = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(60)],
            "group": ["Tumor" if i % 2 else "Normal" for i in range(60)],
        }
    )
    metadata_df.to_csv(dataset_dir / "labels.csv", index=False)

    result = run_dataset_intake(
        dataset_directory=dataset_dir,
        output_directory=output_dir,
    )

    selected_files = result["selected_files"]
    discovery_report = result["discovery_report"]

    assert set(selected_files["selection_status"]) == {"auto_selected"}

    selected_names = set(
        discovery_report.loc[
            discovery_report["selected"] == "yes",
            "file_name",
        ]
    )

    assert selected_names == {"data.csv", "labels.csv"}
