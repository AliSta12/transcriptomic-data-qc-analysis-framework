import pandas as pd


class MetadataHarmonizer:
    """
    Standardizes metadata tables into the internal project format.

    Required internal format:
    - sample_id
    - group
    """

    @staticmethod
    def harmonize_metadata(metadata_df: pd.DataFrame) -> pd.DataFrame:
        harmonized = metadata_df.copy()

        if "sample_id" not in harmonized.columns:
            harmonized = harmonized.rename(
                columns={harmonized.columns[0]: "sample_id"}
            )

        if "group" not in harmonized.columns:
            if "Class" in harmonized.columns:
                harmonized = harmonized.rename(columns={"Class": "group"})

        if "sample_id" not in harmonized.columns:
            raise ValueError("Metadata must contain or allow creation of 'sample_id' column.")

        if "group" not in harmonized.columns:
            raise ValueError("Metadata must contain or allow creation of 'group' column.")

        return harmonized
