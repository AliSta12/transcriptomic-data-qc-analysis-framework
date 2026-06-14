from dataclasses import dataclass

import pandas as pd

from src.analysis_engine.analysis_summary_generator import (
    AnalysisSummaryGenerator,
    AnalysisSummaryGeneratorResult,
)
from src.analysis_engine.class_distribution_analysis import (
    ClassDistributionAnalysis,
    ClassDistributionResult,
)
from src.analysis_engine.dataset_overview import (
    DatasetOverview,
    DatasetOverviewResult,
)
from src.analysis_engine.heatmap_generator import (
    HeatmapGenerator,
    HeatmapGeneratorResult,
)
from src.analysis_engine.pca_analysis import (
    PCAAnalysis,
    PCAAnalysisResult,
)
from src.analysis_engine.sample_clustering import (
    SampleClustering,
    SampleClusteringResult,
)
from src.analysis_engine.variable_gene_analysis import (
    VariableGeneAnalysis,
    VariableGeneAnalysisResult,
)


@dataclass
class AnalysisEnginePipelineResult:
    dataset_overview: DatasetOverviewResult
    class_distribution: ClassDistributionResult
    variable_gene_analysis: VariableGeneAnalysisResult
    pca_analysis: PCAAnalysisResult
    heatmap: HeatmapGeneratorResult
    sample_clustering: SampleClusteringResult
    analysis_summary: AnalysisSummaryGeneratorResult


class AnalysisEnginePipeline:
    """
    Runs the complete exploratory transcriptomic analysis workflow.

    This pipeline expects:
    - cleaned expression matrix in sample x gene format
    - first expression column named sample_id
    - cleaned metadata containing sample_id and group columns
    """

    def run(
        self,
        expression_df: pd.DataFrame,
        metadata_df: pd.DataFrame,
        output_directory: str,
    ) -> AnalysisEnginePipelineResult:

        dataset_overview = DatasetOverview().generate(
            expression_df=expression_df,
            metadata_df=metadata_df,
        )

        class_distribution = ClassDistributionAnalysis().generate(
            metadata_df=metadata_df,
            output_directory=output_directory,
        )

        variable_gene_analysis = VariableGeneAnalysis().generate(
            expression_df=expression_df,
            output_directory=output_directory,
        )

        pca_analysis = PCAAnalysis().generate(
            expression_df=expression_df,
            metadata_df=metadata_df,
            output_directory=output_directory,
        )

        heatmap = HeatmapGenerator().generate(
            expression_df=expression_df,
            top_variable_genes_df=variable_gene_analysis.top_50_genes,
            output_directory=output_directory,
        )

        sample_clustering = SampleClustering().generate(
            expression_df=expression_df,
            metadata_df=metadata_df,
            output_directory=output_directory,
        )

        analysis_summary = AnalysisSummaryGenerator().generate(
            summary_dataframes=[
                dataset_overview.summary_dataframe,
                class_distribution.summary_dataframe,
                variable_gene_analysis.summary_dataframe,
                pca_analysis.summary_dataframe,
                heatmap.summary_dataframe,
                sample_clustering.summary_dataframe,
            ],
            output_directory=output_directory,
        )

        return AnalysisEnginePipelineResult(
            dataset_overview=dataset_overview,
            class_distribution=class_distribution,
            variable_gene_analysis=variable_gene_analysis,
            pca_analysis=pca_analysis,
            heatmap=heatmap,
            sample_clustering=sample_clustering,
            analysis_summary=analysis_summary,
        )
