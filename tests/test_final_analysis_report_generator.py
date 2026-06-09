from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import pandas as pd

from src.reporting.final_analysis_report_generator import (
    FinalAnalysisReportGenerator,
)


def _create_dummy_png(path: Path) -> str:
    plt.figure(figsize=(2, 2))
    plt.plot([1, 2, 3], [1, 2, 3])
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return str(path)


def test_final_analysis_report_generator_creates_pdf(tmp_path):

    image_paths = [
        _create_dummy_png(tmp_path / "missing_data_plot.png"),
        _create_dummy_png(tmp_path / "qc_status_summary_plot.png"),
        _create_dummy_png(tmp_path / "class_distribution.png"),
        _create_dummy_png(tmp_path / "pca_plot.png"),
        _create_dummy_png(tmp_path / "top_variable_genes_barplot.png"),
        _create_dummy_png(tmp_path / "heatmap_top50_variable_genes.png"),
        _create_dummy_png(tmp_path / "sample_clustering_dendrogram.png"),
    ]

    cleaner_result = SimpleNamespace(
        data_quality_report=pd.DataFrame(
            {
                "check": ["Missing Data", "Duplicate Genes"],
                "status": ["PASS", "WARNING"],
                "metric": ["0", "2"],
                "threshold": ["gene <=5%", "0 duplicate genes"],
                "details": ["No missing data.", "Duplicate genes aggregated."],
            }
        ),
        harmonization_report=pd.DataFrame(
            {
                "original_element": ["gene x sample"],
                "standardized_element": ["sample x gene"],
                "element_type": ["data_orientation"],
                "transformation": ["transposed"],
                "reason": ["Analysis engine requires standardized format."],
            }
        ),
        data_readiness_report=pd.DataFrame(
            {
                "overall_status": ["READY_WITH_WARNINGS"],
                "pass_count": [1],
                "warning_count": [1],
                "review_count": [0],
                "recommendation": ["Dataset can be analyzed with warnings."],
            }
        ),
        final_status="READY_WITH_WARNINGS",
        missing_data_plot_path=image_paths[0],
        qc_status_summary_plot_path=image_paths[1],
    )

    analysis_result = SimpleNamespace(
        dataset_overview=SimpleNamespace(
            summary_dataframe=pd.DataFrame(
                {
                    "metric": ["sample_count", "gene_count"],
                    "value": [4, 3],
                }
            )
        ),
        analysis_summary=SimpleNamespace(
            summary_dataframe=pd.DataFrame(
                {
                    "metric": ["pc1_variance_explained"],
                    "value": [0.62],
                }
            )
        ),
        class_distribution=SimpleNamespace(plot_path=image_paths[2]),
        pca_analysis=SimpleNamespace(plot_path=image_paths[3]),
        variable_gene_analysis=SimpleNamespace(barplot_path=image_paths[4]),
        heatmap=SimpleNamespace(plot_path=image_paths[5]),
        sample_clustering=SimpleNamespace(plot_path=image_paths[6]),
    )

    result = FinalAnalysisReportGenerator().generate(
        cleaner_result=cleaner_result,
        analysis_result=analysis_result,
        dataset_name="Test dataset",
        output_directory=str(tmp_path),
    )

    assert Path(result.pdf_path).exists()
    assert result.pdf_path.endswith("final_report.pdf")
    assert Path(result.pdf_path).stat().st_size > 0
