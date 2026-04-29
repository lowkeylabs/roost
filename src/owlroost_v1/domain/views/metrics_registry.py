from owlroost.domain.registry import register_view

register_view(
    "trials",
    ["status", "elapsed", "spending", "bequest", "risk"],
)

register_view(
    "runs",
    [
        "trial_count",
        "success_pct",
        "elapsed_mean",
        "bequest_mean",
        "bequest_median",
    ],
)
