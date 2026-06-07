import pandas as pd

from src.analysis_engine.variable_gene_analysis import VariableGeneAnalysis


def test_variable_gene_analysis_generates_top_gene_tables(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "GENE_LOW": [1.0, 1.0, 1.0],
            "GENE_MEDIUM": [1.0, 2.0, 3.0],
            "GENE_HIGH": [1.0, 5.0, 9.0],
        }
    )

    result = VariableGeneAnalysis().generate(
        expression_df=expression_df,
        output_directory=str(tmp_path),
    )

    assert result.top_50_genes.iloc[0]["gene"] == "GENE_HIGH"
    assert result.top_100_genes.iloc[0]["gene"] == "GENE_HIGH"
    assert "variance" in result.top_50_genes.columns
    assert result.top_50_path.endswith("top_50_variable_genes.csv")
    assert result.top_100_path.endswith("top_100_variable_genes.csv")

    assert (tmp_path / "top_50_variable_genes.csv").exists()
    assert (tmp_path / "top_100_variable_genes.csv").exists()


def test_variable_gene_analysis_requires_sample_id_column(tmp_path):
    expression_df = pd.DataFrame(
        {
            "GENE1": [1.0, 2.0, 3.0],
            "GENE2": [2.0, 3.0, 4.0],
        }
    )

    try:
        VariableGeneAnalysis().generate(
            expression_df=expression_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "sample_id" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_variable_gene_analysis_requires_gene_columns(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
        }
    )

    try:
        VariableGeneAnalysis().generate(
            expression_df=expression_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "at least one gene column" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")


def test_variable_gene_analysis_requires_numeric_gene_columns(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3"],
            "GENE1": [1.0, 2.0, 3.0],
            "GENE2": ["low", "medium", "high"],
        }
    )

    try:
        VariableGeneAnalysis().generate(
            expression_df=expression_df,
            output_directory=str(tmp_path),
        )
    except ValueError as error:
        assert "Non-numeric columns detected" in str(error)
    else:
        raise AssertionError("Expected ValueError was not raised.")
