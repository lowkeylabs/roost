import importlib.resources as resources
import shutil
from pathlib import Path

import click


def init_project_config(force: bool = False):
    """
    Initialize ./conf with default configuration files.

    Creates:
      ./conf/config.yaml
      ./conf/logging/default.yaml
    """
    conf_dir = Path.cwd() / "conf"
    logging_dir = conf_dir / "logging"

    if conf_dir.exists() and not force:
        raise click.ClickException("conf/ already exists. Use --force to overwrite.")

    conf_dir.mkdir(parents=True, exist_ok=True)
    logging_dir.mkdir(parents=True, exist_ok=True)

    # Copy config.yaml template
    with resources.path("owlroost.conf", "config.yaml") as src:
        shutil.copy(src, conf_dir / "config.yaml")

    # Copy logging/default.yaml template
    with resources.path("owlroost.conf.logging", "default.yaml") as src:
        shutil.copy(src, logging_dir / "default.yaml")
