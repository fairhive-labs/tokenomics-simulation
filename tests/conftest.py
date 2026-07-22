"""Shared pytest fixtures for the tokenomics simulation test-suite."""

import copy
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.json"


@pytest.fixture
def base_config():
    """The real project configuration, loaded fresh (already carries a seed)."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


@pytest.fixture
def make_config(base_config):
    """Return a factory yielding deep-copied configs with overrides applied."""

    def _factory(**overrides):
        config = copy.deepcopy(base_config)
        config.update(overrides)
        config.setdefault("random_seed", 12345)
        return config

    return _factory
