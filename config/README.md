# Configuration

Each region configuration owns its geographic bounds, expected grid, Drive source,
step-type filenames/variables, storage locations and analysis thresholds. Copy a
configuration for a new region rather than inserting regional constants in `src/`.

`storage.data_root_env` names the optional environment-variable override. Relative
default paths are resolved from the repository root.
