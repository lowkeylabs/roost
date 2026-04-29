# tests/utils.py

from pathlib import Path

from click.testing import CliRunner

from owlroost.cli.cmd_run import cmd_run


def run_cli(runner: CliRunner, case_file: Path, *extra_args):
    """
    Run CLI with single-job constraints for pytest stability.
    """

    return runner.invoke(
        cmd_run,
        [
            str(case_file),
            "--trial-jobs=1",
            "--run-jobs=1",
            *extra_args,
        ],
    )
