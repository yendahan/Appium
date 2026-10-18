"""Loads test data from testdata/<env>.json.

String values of the form ``${env:NAME}`` are replaced by the environment variable NAME when a
node is requested, so credentials are never stored in the repository.
"""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Optional

from framework.config_manager import ConfigManager
from framework.exceptions import FrameworkException

TESTDATA_DIR = Path(__file__).resolve().parent.parent / "testdata"
_PLACEHOLDER = re.compile(r"\$\{env:([A-Za-z0-9_]+)\}")

EnvLookup = Callable[[str], Optional[str]]


def _substitute(text: str, env_lookup: EnvLookup) -> str:
    def repl(m: "re.Match[str]") -> str:
        value = env_lookup(m.group(1))
        if not value:
            # Name only the variable, never a value.
            raise FrameworkException(f"Environment variable '{m.group(1)}' required by test data is not set")
        return value

    # A function replacement keeps '\' and '$' in the value from being read as regex syntax.
    return _PLACEHOLDER.sub(repl, text)


def _resolve(node: Any, env_lookup: EnvLookup) -> Any:
    if isinstance(node, str):
        return _substitute(node, env_lookup)
    if isinstance(node, dict):
        return {k: _resolve(v, env_lookup) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve(v, env_lookup) for v in node]
    return node


class TestDataLoader:
    __test__ = False  # not a pytest test class despite the name

    def __init__(self, env: str) -> None:
        path = TESTDATA_DIR / f"{env}.json"
        if not path.is_file():
            raise FrameworkException(f"Test data file 'testdata/{env}.json' not found")
        try:
            self._root = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise FrameworkException(f"Unable to parse test data file 'testdata/{env}.json'") from e

    @classmethod
    def for_current_env(cls) -> "TestDataLoader":
        return cls(ConfigManager.get_instance().env)

    def node(self, key: str, env_lookup: Optional[EnvLookup] = None) -> Any:
        """Copy of the top-level node with placeholders resolved (secrets never cached in the tree)."""
        if key not in self._root:
            raise FrameworkException(f"Test data key '{key}' not found")
        return _resolve(copy.deepcopy(self._root[key]), env_lookup or os.environ.get)
