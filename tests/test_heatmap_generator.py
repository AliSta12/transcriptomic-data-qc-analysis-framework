import pandas as pd

from src.analysis_engine.heatmap_generator import HeatmapGenerator


def test_heatmap_generator_creates_heatmap_plot(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "GENE1": [1.0, 2.0, 3.0],
            "GENE2": [4.0, 5.0, 6.0],
            "GENE3": [7.0, 8.0, 9.0],
        }
    )

    top_variable_genes_df = pd.DataFrame(
        {
            "gene": ["GENE3", "GENE2"],
            "variance": [1.0, 0.5],
        }
    )

    result = HeatmapGenerator().generate(
        expression_df=expression_df,
        top_variable_genes_df=top_variable_genes_df,
        output_directory=str(tmp_path),
    )

    assert result.plot_path.endswith("heatmap_top50_variable_genes.png")
    assert (tmp_path / "heatmap_top50_variable_genes.png").exists()
    assert list(result.heatmap_dataframe.columns) == [
        "sample_id",
        "GENE3",
        "GENE2",
    ]


def test_heatmap_generator_requires_sample_id_column(tmp_path):
    expression_df = pd.DataFrame(
        {
            "GENE1": [1.0, 2.0, 3.0],
            "GENE2": [4.0, 5.0, 6.0],
        }
    )

    top_variable_genes_df = pd.DataFrame(
        {
            "gene": ["GENE1"],
        }
    )

    try:
        HeatmapGenerator().generate(
            expression_df=expression_df,
            top_variable_genes_df=top_variable_genes_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "sample_id" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_heatmap_generator_requires_gene_column_in_top_genes(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "GENE1": [1.0, 2.0],
        }
    )

    top_variable_genes_df = pd.DataFrame(
        {
            "symbol": ["GENE1"],
        }
    )

    try:
        HeatmapGenerator().generate(
            expression_df=expression_df,
            top_variable_genes_df=top_variable_genes_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "gene" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_heatmap_generator_requires_existing_genes(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "GENE1": [1.0, 2.0],
        }
    )

    top_variable_genes_df = pd.DataFrame(
        {
            "gene": ["GENE_MISSING"],
        }
    )

    try:
        HeatmapGenerator().generate(
            expression_df=expression_df,
            top_variable_genes_df=top_variable_genes_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "Genes not found" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")
