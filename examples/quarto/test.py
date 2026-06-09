from io import StringIO
from pathlib import Path

import owlplanner as owl
import toml

input_file = "case_alex+jamie.toml"


trial_dir = Path.cwd()
trial_toml = trial_dir / input_file
if not trial_toml.exists():
    raise RuntimeError(f"Missing {input_file} in {trial_dir}")


toml_dict = toml.load(trial_toml)
toml_str = toml.dumps(toml_dict)
buf = StringIO(toml_str)

plan = owl.readConfig(
    buf,
    logstreams="loguru",
    loadHFP=False,
)

plan.solve(
    plan.objective,
    plan.solverOptions,
)

print(plan.summaryString())

print(f"OWL version: {owl.__version__}")
