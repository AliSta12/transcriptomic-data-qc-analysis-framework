"""
Shared plot color palette for report and Streamlit visualizations.

Palette: Sunny Garden + Sky Mint variable-gene gradient.

The palette separates:
- QC status semantics,
- biological group colors,
- continuous expression/variance scales.
"""

QC_STATUS_COLORS = {
    "PASS": "#52D273",
    "WARNING": "#FFCF5C",
    "FAIL": "#FF7070",
    "REQUIRES REVIEW": "#A987E8",
}

GROUP_DISPLAY_ORDER = [
    "Normal",
    "Tumor",
    "Mucosa",
    "BRCA",
    "COAD",
    "KIRC",
    "LUAD",
    "PRAD",
]

GROUP_COLORS = {
    # GEO-style biological groups
    "Normal": "#4ED8B1",
    "Tumor": "#FF936A",
    "Mucosa": "#6C9CFF",

    # PANCAN cancer-type groups
    "BRCA": "#6C9CFF",
    "COAD": "#FFCF5C",
    "KIRC": "#52D273",
    "LUAD": "#FF936A",
    "PRAD": "#A987E8",
}

FALLBACK_GROUP_COLORS = [
    "#4ED8B1",
    "#FF936A",
    "#6C9CFF",
    "#A987E8",
    "#FFCF5C",
    "#FF7070",
    "#9ADCFB",
    "#34BFA3",
]

MISSING_DATA_COLOR = QC_STATUS_COLORS["WARNING"]

VARIABLE_GENE_GRADIENT = [
    "#ECF8FF",
    "#9ADCFB",
    "#3AB7BF",
]

VARIABLE_GENE_SINGLE_COLOR = "#3AB7BF"

HEATMAP_COLORS = [
    "#73C8FF",
    "#FFFBEF",
    "#FF936A",
]

DENDROGRAM_LINE_COLOR = "#8E8E8E"
