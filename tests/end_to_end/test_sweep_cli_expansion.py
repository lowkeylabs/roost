from __future__ import annotations

from owlroost.schema.sweeps import (
    expand_cli_overrides,
)


def test_ss_age_pair_single_pair():
    overrides = [
        "roost_sweeps.ss_age_pair=69-67",
    ]

    expanded = expand_cli_overrides(
        overrides,
    )

    assert expanded == overrides


def test_ss_age_pair_range_first():
    """
    Range on first spouse expands
    into Hydra choices.
    """

    overrides = [
        ("roost_sweeps.ss_age_pair=range(62,64)-67"),
    ]

    expanded = expand_cli_overrides(
        overrides,
    )

    assert expanded == [
        ("roost_sweeps.ss_age_person0=62,63,64"),
        ("roost_sweeps.ss_age_person1=67"),
    ]


def test_ss_age_pair_range_second():
    """
    Range on second spouse expands
    into Hydra choices.
    """

    overrides = [
        ("roost_sweeps.ss_age_pair=67-range(62,64)"),
    ]

    expanded = expand_cli_overrides(
        overrides,
    )

    assert expanded == [
        ("roost_sweeps.ss_age_person0=67"),
        ("roost_sweeps.ss_age_person1=62,63,64"),
    ]


def test_ss_age_pair_cartesian():
    """
    Two ranges become two independent
    Hydra sweep dimensions.
    """

    overrides = [
        ("roost_sweeps.ss_age_pair=range(62,63)-range(65,66)"),
    ]

    expanded = expand_cli_overrides(
        overrides,
    )

    assert expanded == [
        ("roost_sweeps.ss_age_person0=62,63"),
        ("roost_sweeps.ss_age_person1=65,66"),
    ]


def test_non_sweep_override_passthrough():
    """
    Non-sweep overrides should not
    be modified.
    """

    overrides = [
        "solver_options.bequest=100",
    ]

    expanded = expand_cli_overrides(
        overrides,
    )

    assert expanded == overrides


def test_ss_age_pair_monthly():
    """
    Monthly range expands into
    explicit Hydra choices.
    """

    overrides = [
        ("roost_sweeps.ss_age_pair=range(62,62.25,1/12)-67"),
    ]

    expanded = expand_cli_overrides(
        overrides,
    )

    assert expanded == [
        ("roost_sweeps.ss_age_person0=62,62.083333,62.166667,62.25"),
        ("roost_sweeps.ss_age_person1=67"),
    ]


def test_ss_age_pair_both_monthly():
    """
    Monthly ranges for both spouses
    become independent sweep axes.
    """

    overrides = [
        ("roost_sweeps.ss_age_pair=range(62,62.25,1/12)-range(67,67.25,1/12)"),
    ]

    expanded = expand_cli_overrides(
        overrides,
    )

    assert expanded == [
        ("roost_sweeps.ss_age_person0=62,62.083333,62.166667,62.25"),
        ("roost_sweeps.ss_age_person1=67,67.083333,67.166667,67.25"),
    ]


def test_ss_age_pair_multiple_pairs_passthrough():
    overrides = [
        ("roost_sweeps.ss_age_pair=64-64,67-67,70-70"),
    ]

    expanded = expand_cli_overrides(
        overrides,
    )

    assert expanded == overrides
