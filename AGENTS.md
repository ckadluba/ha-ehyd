# Project instructions

- After every change in this project, run Ruff's formatter check against the
  source files and fix all reported issues before continuing:

  ```sh
  ruff format custom_components/ehyd --check
  ruff check custom_components/ehyd
  ```

- Test code is excluded from this Ruff check; do not use the test directory as
  the target for this required validation.

- After every code change, compare the implementation with `README.md` and
  update the README when the documented behavior, configuration, sensor
  metadata, or other user-visible behavior has changed.
