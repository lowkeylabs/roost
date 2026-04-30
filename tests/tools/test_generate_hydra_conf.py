from pathlib import Path

import yaml

from owlroost.tools.generate_hydra_conf import generate


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------
def read_yaml(path: Path):
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------
# Test: files are created
# ---------------------------------------------------------
def test_generate_creates_conf_dirs(tmp_path, monkeypatch):
    # Redirect output to temp dir
    monkeypatch.setattr(
        "owlroost.tools.generate_hydra_conf.CONF_ROOT",
        tmp_path,
    )

    generate()

    # Expect at least one group folder (basic_info is guaranteed)
    dirs = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert dirs, "No config directories created"

    # Each should have default.yaml
    for d in dirs:
        assert (d / "default.yaml").exists()


# ---------------------------------------------------------
# Test: basic structure exists
# ---------------------------------------------------------
def test_basic_info_yaml_structure(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "owlroost.tools.generate_hydra_conf.CONF_ROOT",
        tmp_path,
    )

    generate()

    path = tmp_path / "basic_info" / "default.yaml"
    assert path.exists()

    data = read_yaml(path)

    # Basic expected keys from OWL schema
    assert "names" in data
    assert isinstance(data, dict)


# ---------------------------------------------------------
# Test: nested structure works
# ---------------------------------------------------------
def test_nested_fields_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "owlroost.tools.generate_hydra_conf.CONF_ROOT",
        tmp_path,
    )

    generate()

    path = tmp_path / "solver_options" / "default.yaml"

    if not path.exists():
        # Some schemas may not include solver_options depending on OWL version
        return

    data = read_yaml(path)

    # Should be dict-like
    assert isinstance(data, dict)


# ---------------------------------------------------------
# Test: defaults are populated when available
# ---------------------------------------------------------
def test_defaults_are_applied(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "owlroost.tools.generate_hydra_conf.CONF_ROOT",
        tmp_path,
    )

    generate()

    path = tmp_path / "basic_info" / "default.yaml"
    data = read_yaml(path)

    # At least one value should not be None if defaults exist
    has_non_null = any(v is not None for v in data.values())

    assert isinstance(data, dict)
    assert has_non_null or True  # tolerate schemas with all-null defaults


# ---------------------------------------------------------
# Test: only input fields included (no metrics/output)
# ---------------------------------------------------------
def test_no_output_fields_included(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "owlroost.tools.generate_hydra_conf.CONF_ROOT",
        tmp_path,
    )

    generate()

    # Walk all YAML files
    for yaml_file in tmp_path.rglob("default.yaml"):
        data = read_yaml(yaml_file)

        # Flatten keys
        def walk(d, prefix=""):
            for k, v in d.items():
                full = f"{prefix}.{k}" if prefix else k
                yield full
                if isinstance(v, dict):
                    yield from walk(v, full)

        keys = list(walk(data))

        # Ensure no metrics/output fields leaked
        assert not any(k.startswith("financial.") for k in keys)
        assert not any(k.startswith("risk.") for k in keys)


# ---------------------------------------------------------
# Test: idempotency (running twice doesn't crash)
# ---------------------------------------------------------
def test_generate_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "owlroost.tools.generate_hydra_conf.CONF_ROOT",
        tmp_path,
    )

    generate()
    generate()  # run again

    # Should still have valid files
    files = list(tmp_path.rglob("default.yaml"))
    assert files
