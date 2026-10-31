#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
mkdir -p work
test_dir="$(mktemp -d "$project_dir/work/test.XXXXXXXX")"
trap 'rm -rf -- "$test_dir"' EXIT
python3 tools/build_data.py --check
python3 -m unittest discover -s tests -p 'test_*.py'
while IFS= read -r -d '' lua_file; do luac -p "$lua_file"; done < <(find rime/lua -type f -name '*.lua' -print0)
./install.sh --rime-dir "$test_dir/rime" --state-dir "$test_dir/state"
g++ -std=c++17 -Wall -Wextra -O2 tests/test_engine.cpp -o "$test_dir/test-engine" -lrime
"$test_dir/test-engine" "$test_dir/rime" /usr/share/rime-data
./uninstall.sh --rime-dir "$test_dir/rime" --state-dir "$test_dir/state"
