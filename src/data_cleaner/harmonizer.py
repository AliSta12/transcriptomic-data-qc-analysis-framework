import pandas as pd

from src.data_cleaner.structure_detector import DataOrientation


class Harmonizer:
    """
    Converts expression matrices into the internal project format:

    sample x gene

    Required internal format:
    - rows = samples
    - columns = genes
    - first column = sample_id
    """

    @staticmethod
    def harmonize_expression_matrix(
        dataframe: pd.DataFrame,
        orientation: DataOrientation,
    ) -> pd.DataFrame:

        if orientation == DataOrientation.SAMPLE_X_GENE:
            return Harmonizer._harmonize_sample_x_gene(dataframe)

        if orientation == DataOrientation.GENE_X_SAMPLE:
            return Harmonizer._harmonize_gene_x_sample(dataframe)

        raise ValueError(
            "Cannot harmonize expression matrix with unknown orientation."
        )

    @staticmethod
    def _harmonize_sample_x_gene(dataframe: pd.DataFrame) -> pd.DataFrame:
        harmonized = dataframe.copy()
        harmonized = harmonized.rename(columns={harmonized.columns[0]: "sample_id"})
        return harmonized

    @staticmethod
    def _harmonize_gene_x_sample(dataframe: pd.DataFrame) -> pd.DataFrame:
        gene_column = dataframe.columns[0]

        transposed = dataframe.set_index(gene_column).T
        transposed.index.name = "sample_id"

        harmonized = transposed.reset_index()

        return harmonized
