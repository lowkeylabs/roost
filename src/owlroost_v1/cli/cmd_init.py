import click
from loguru import logger

from owlroost.core.config_init import init_project_config


@click.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing config.")
def cmd_init(force: bool):
    """
    Initialize an OWL-ROOST ./conf folder
    """
    init_project_config(force=force)
    logger.success("OWL-ROOST configuration initialized in ./conf")
