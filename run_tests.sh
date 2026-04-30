#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if [[ -x ".venv/bin/python" ]]; then
    python_bin=".venv/bin/python"
else
    python_bin="${PYTHON:-python3}"
fi

for test_file in tests/Test*.py; do
    printf 'Running tests in %s\n' "$test_file"
    "$python_bin" -m unittest "$test_file"
done
