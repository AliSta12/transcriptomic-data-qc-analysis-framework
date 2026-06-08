import pandas as pd


class GeoMetadataExtractor:
    """
    Extracts sample metadata from a manually downloaded GEO Series Matrix file.

    This helper does not download data from GEO API.
    It only parses local Series Matrix metadata lines.
    """

    @staticmethod
    def extract(lines: list[str]) -> pd.DataFrame:
        sample_titles = []
        sample_ids = []

        for line in lines:
            if line.startswith("!Sample_title"):
                sample_titles = GeoMetadataExtractor._parse_geo_line(line)

            if line.startswith("!Sample_geo_accession"):
                sample_ids = GeoMetadataExtractor._parse_geo_line(line)

        if not sample_titles:
            raise ValueError("Could not extract GEO sample titles.")

        if not sample_ids:
            raise ValueError("Could not extract GEO sample IDs.")

        if len(sample_titles) != len(sample_ids):
            raise ValueError(
                "GEO sample titles and sample IDs have different lengths."
            )

        groups = [
            GeoMetadataExtractor._infer_group_from_title(title)
            for title in sample_titles
        ]

        return pd.DataFrame(
            {
                "sample_id": sample_ids,
                "group": groups,
                "sample_title": sample_titles,
            }
        )

    @staticmethod
    def _parse_geo_line(line: str) -> list[str]:
        return [
            value.strip().strip('"')
            for value in line.strip().split("\t")[1:]
        ]

    @staticmethod
    def _infer_group_from_title(title: str) -> str:
        normalized_title = title.lower()

        if normalized_title.startswith("normal"):
            return "normal"

        if normalized_title.startswith("cancer"):
            return "tumor"

        raise ValueError(
            f"Could not infer group from GEO sample title: {title}"
        )
