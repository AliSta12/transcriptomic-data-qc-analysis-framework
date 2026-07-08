from src.shared.plot_style import (
    FALLBACK_GROUP_COLORS,
    GROUP_COLORS,
    GROUP_DISPLAY_ORDER,
)


def get_ordered_groups(groups: list[str]) -> list[str]:
    """
    Returns biological groups in a stable, presentation-friendly order.

    Known groups follow GROUP_DISPLAY_ORDER.
    Unknown groups are appended alphabetically.
    """

    unique_groups = sorted(set(groups), key=lambda group: str(group).lower())

    order_map = {
        group.lower(): index
        for index, group in enumerate(GROUP_DISPLAY_ORDER)
    }

    return sorted(
        unique_groups,
        key=lambda group: (
            order_map.get(str(group).lower(), len(order_map)),
            str(group).lower(),
        ),
    )


def get_group_color_map(groups: list[str]) -> dict[str, str]:
    """
    Returns a stable color map for biological groups.

    Known groups receive predefined project colors.
    Unknown groups receive fallback colors in stable order.
    """

    ordered_groups = get_ordered_groups(groups)

    group_color_map = {}
    fallback_index = 0

    for group in ordered_groups:
        group_label = str(group)

        matching_group = next(
            (
                known_group
                for known_group in GROUP_COLORS
                if known_group.lower() == group_label.lower()
            ),
            None,
        )

        if matching_group is not None:
            group_color_map[group] = GROUP_COLORS[matching_group]
        else:
            group_color_map[group] = FALLBACK_GROUP_COLORS[
                fallback_index % len(FALLBACK_GROUP_COLORS)
            ]
            fallback_index += 1

    return group_color_map
