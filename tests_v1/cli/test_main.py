from click.testing import CliRunner

from owlroost.cli._main import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "ROOST" in result.output
