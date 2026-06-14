DEFAULT_GROUP_COLORS = {
    "BRCA": "#8ecae6",  # pastel blue
    "COAD": "#ffb703",  # warm pastel orange
    "KIRC": "#90be6d",  # pastel green
    "LUAD": "#f28482",  # pastel coral
    "PRAD": "#b197fc",  # pastel purple
}

FALLBACK_PASTEL_COLORS = [
    "#8ecae6",
    "#ffb703",
    "#90be6d",
    "#f28482",
    "#b197fc",
    "#a8dadc",
    "#ffd6a5",
    "#caffbf",
    "#ffc6ff",
    "#bde0fe",
]


def get_group_color_map(groups: list[str]) -> dict[str, str]:
    """
    Returns a stable pastel color map for biological groups.

    Known PANCAN groups receive predefined colors.
    Unknown groups receive fallback pastel colors in sorted order.
    """

    unique_groups = sorted(set(groups))

    group_color_map = {}

    fallback_index = 0

    for group in unique_groups:
        if group in DEFAULT_GROUP_COLORS:
            group_color_map[group] = DEFAULT_GROUP_COLORS[group]
        else:
            group_color_map[group] = FALLBACK_PASTEL_COLORS[
                fallback_index % len(FALLBACK_PASTEL_COLORS)
            ]
            fallback_index += 1

    return group_color_map
