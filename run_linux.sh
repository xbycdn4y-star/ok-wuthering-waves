#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"

if [[ -x ".venv/bin/python" ]]; then
    python_bin=".venv/bin/python"
else
    python_bin="${PYTHON:-python3}"
fi

exec "$python_bin" main.py -name ok-ww-linux "$@"
