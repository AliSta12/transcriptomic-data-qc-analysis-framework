import pandas as pd

from src.analysis_engine.analysis_engine_pipeline import (
    AnalysisEnginePipeline,
)


def test_analysis_engine_pipeline_runs_complete_workflow(tmp_path):
    expression_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "GENE1": [1.0, 2.0, 8.0, 9.0],
            "GENE2": [1.0, 2.0, 8.0, 9.0],
            "GENE3": [2.0, 3.0, 7.0, 8.0],
        }
    )

    metadata_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2", "S3", "S4"],
            "group": ["A", "A", "B", "B"],
        }
    )

    result = AnalysisEnginePipeline().run(
        expression_df=expression_df,
        metadata_df=metadata_df,
        output_directory=str(tmp_path),
    )

    assert result.dataset_overview.sample_count == 4
    assert result.dataset_overview.gene_count == 3

    assert result.class_distribution.group_distribution == {
        "A": 2,
        "B": 2,
    }

    assert result.variable_gene_analysis.top_50_path.endswith(
        "top_50_variable_genes.csv"
    )

    assert result.pca_analysis.plot_path.endswith(
        "pca_plot.png"
    )

    assert result.heatmap.plot_path.endswith(
        "heatmap_top50_variable_genes.png"
    )

    assert result.sample_clustering.plot_path.endswith(
        "sample_clustering_dendrogram.png"
    )

    assert result.analysis_summary.csv_path.endswith(
        "analysis_summary.csv"
    )

    assert result.analysis_summary.markdown_path.endswith(
        "analysis_summary.md"
    )

    expected_output_files = [
        "class_distribution.png",
        "top_50_variable_genes.csv",
        "top_100_variable_genes.csv",
        "pca_plot.png",
        "heatmap_top50_variable_genes.png",
        "sample_clustering_dendrogram.png",
        "analysis_summary.csv",
        "analysis_summary.md",
    ]

    for filename in expected_output_files:
        assert (tmp_path / filename).exists()
