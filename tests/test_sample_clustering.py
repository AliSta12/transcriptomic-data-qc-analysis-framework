import pandas as pd

from src.analysis_engine.sample_clustering import SampleClustering


def test_sample_clustering_generates_dendrogram(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "GENE1": [1.0, 2.0, 8.0],
            "GENE2": [1.0, 2.0, 8.0],
        }
    )

    result = SampleClustering().generate(
        expression_df=expression_df,
        output_directory=str(tmp_path),
    )

    assert result.plot_path.endswith("sample_clustering_dendrogram.png")
    assert (tmp_path / "sample_clustering_dendrogram.png").exists()
    assert len(result.linkage_matrix) == 2


def test_sample_clustering_requires_sample_id_column(tmp_path):
    expression_df = pd.DataFrame(
        {
            "GENE1": [1.0, 2.0],
            "GENE2": [1.0, 2.0],
        }
    )

    try:
        SampleClustering().generate(
            expression_df=expression_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "sample_id" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_sample_clustering_requires_gene_columns(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
        }
    )

    try:
        SampleClustering().generate(
            expression_df=expression_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "at least one gene column" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_sample_clustering_requires_two_samples(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1"],
            "GENE1": [1.0],
            "GENE2": [2.0],
        }
    )

    try:
        SampleClustering().generate(
            expression_df=expression_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "at least two samples" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_sample_clustering_requires_numeric_gene_columns(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "GENE1": [1.0, 2.0],
            "GENE2": ["low", "high"],
        }
    )

    try:
        SampleClustering().generate(
            expression_df=expression_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "Non-numeric columns detected" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")
