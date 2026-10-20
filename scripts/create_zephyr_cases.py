"""Creates the Zephyr Scale cases defined in framework/zephyr_cases.py under the configured folder (by hand), in
sub-folders that mirror where the tests sit under tests/, e.g. <folder>/Android/Upgraded Consumer Account.

A test run does this by itself when its ZEPHYR_CASES_FOLDER is empty; use this script to add cases to a folder that
already has some (cases with the same name are reused, never duplicated).

    python scripts/create_zephyr_cases.py --dry-run     # print what would be created, send nothing
    ZEPHYR_TOKEN=<token> python scripts/create_zephyr_cases.py

Prints ``test -> key``.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from framework.config_manager import ConfigManager  # noqa: E402
from framework.zephyr_cases import CASES, folder_of  # noqa: E402
from framework.zephyr_client import ZephyrClient  # noqa: E402
from framework.zephyr_reporter import DEFAULT_URL  # noqa: E402


def _leaf(top: str, test: str) -> str:
    """The Zephyr folder of a test: the top folder plus where its file sits under tests/."""
    sub = folder_of(test)
    return f"{top}/{sub}" if sub else top


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print the cases and send nothing")
    args = parser.parse_args()
    cfg = ConfigManager.get_instance()
    folder = cfg.get("zephyr.cases.folder") or "Mobile Automation"

    if args.dry_run:
        for test, case in CASES.items():
            print(f"{test}\n  case:   {case.name}\n  folder: {_leaf(folder, test)}\n  steps:  {len(case.steps)}\n  {case.objective}")
        return 0

    token = os.environ.get("ZEPHYR_TOKEN", "").strip()
    if not token:
        print("Set ZEPHYR_TOKEN first (or use --dry-run).", file=sys.stderr)
        return 1
    client = ZephyrClient(cfg.get("zephyr.base.url") or DEFAULT_URL, token, cfg.require("zephyr.project.key"))
    for test, case in CASES.items():
        leaf = _leaf(folder, test)
        if client.cases_in_folder(leaf) is None:
            client.create_folder(leaf)
        key, created = client.create_case(case.name, leaf, case.objective, case.steps)
        print(f"{test} -> {key} ({'created' if created else 'already existed'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
