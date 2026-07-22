"""Unit tests for the tokenomics simulation engine."""

import numpy as np
import pandas as pd
import pytest

import simulation
from simulation import (
    RESULT_COLUMNS,
    _build_params,
    _init_state,
    _init_vesting_schedules,
    _validate_config,
    _vest_testnet,
    simulate,
)

MONTHS_PER_YEAR = 12


# --------------------------------------------------------------------------- #
# Structure & determinism
# --------------------------------------------------------------------------- #
def test_returns_dataframe_with_expected_columns(base_config):
    df = simulate(24, base_config)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == list(RESULT_COLUMNS)


def test_row_count_matches_months(base_config):
    df = simulate(30, base_config)
    assert len(df) == 30
    assert list(df["Month"]) == list(range(1, 31))


def test_zero_months_returns_empty_frame(base_config):
    df = simulate(0, base_config)
    assert df.empty
    assert list(df.columns) == list(RESULT_COLUMNS)


def test_determinism_same_seed(make_config):
    config = make_config(random_seed=7)
    first = simulate(36, config)
    second = simulate(36, config)
    pd.testing.assert_frame_equal(first, second)


def test_different_seed_changes_output(make_config):
    a = simulate(36, make_config(random_seed=1))
    b = simulate(36, make_config(random_seed=2))
    assert not a["Token Price"].equals(b["Token Price"])


def test_explicit_rng_overrides_seed(base_config):
    rng = np.random.default_rng(999)
    df_explicit = simulate(12, base_config, rng=rng)
    df_seeded = simulate(12, {**base_config, "random_seed": 999})
    pd.testing.assert_frame_equal(df_explicit, df_seeded)


# --------------------------------------------------------------------------- #
# Economic invariants
# --------------------------------------------------------------------------- #
def test_total_supply_constant(base_config):
    df = simulate(60, base_config)
    assert (df["Total Supply"] == base_config["total_supply"]).all()


def test_circulating_supply_bounds(base_config):
    df = simulate(120, base_config)
    assert (df["Circulating Supply"] >= 0).all()
    assert (df["Circulating Supply"] <= base_config["total_supply"]).all()


def test_burnt_tokens_monotonic_non_decreasing(base_config):
    df = simulate(120, base_config)
    assert (df["Total Burnt Tokens"].diff().dropna() >= -1e-9).all()


def test_price_change_within_cap(base_config):
    df = simulate(120, base_config)
    ratios = df["Token Price"].to_numpy()[1:] / df["Token Price"].to_numpy()[:-1]
    assert np.all(ratios <= 1.2 + 1e-9)
    assert np.all(ratios >= 0.8 - 1e-9)


def test_halving_index_non_decreasing_and_bounded(base_config):
    df = simulate(120, base_config)
    halving = df["Halving Index"]
    assert (halving.diff().dropna() >= 0).all()
    params = _build_params(base_config)
    assert halving.max() <= params.max_halvings


def test_dao_consumption_starts_at_configured_month(base_config):
    start = base_config["dao_consumption_start_month"]
    initial_dao = base_config["total_supply"] * (
        base_config["token_distribution"]["DAO Treasury"]
    )
    df = simulate(120, base_config)
    # Before consumption the treasury only receives fees, never spends.
    before = df[df["Month"] < start]
    assert (before["DAO Treasury"] >= initial_dao - 1e-6).all()


# --------------------------------------------------------------------------- #
# Market sentiment branches
# --------------------------------------------------------------------------- #
def test_forced_bull_market(make_config):
    config = make_config(
        bull_market_probability=1.0,
        bear_market_probability=0.0,
        market_event_duration=1,
    )
    df = simulate(1, config)
    assert df["Market Sentiment Index"].iloc[0] == config["msi_bull"]


def test_forced_bear_market(make_config):
    config = make_config(
        bull_market_probability=0.0,
        bear_market_probability=1.0,
        market_event_duration=1,
    )
    df = simulate(1, config)
    assert df["Market Sentiment Index"].iloc[0] == config["msi_bear"]


def test_roadmap_effect_applied_on_cycle(make_config):
    config = make_config(
        bull_market_probability=0.0,
        bear_market_probability=0.0,
        roadmap_cycle=6,
    )
    df = simulate(6, config)
    expected = config["msi_normal"] * config["roadmap_effect"]
    assert df["Market Sentiment Index"].iloc[5] == pytest.approx(expected)


# --------------------------------------------------------------------------- #
# Missions & processing branches
# --------------------------------------------------------------------------- #
def test_zero_missions_keeps_price_flat(make_config):
    config = make_config(carrying_capacity=0)
    df = simulate(24, config)
    assert (df["Missions"] == 0).all()
    assert (df["Token Price"] == config["initial_price"]).all()
    assert (df["Tokens Burnt"] == 0).all()


def test_missions_produce_burn_and_fees(base_config):
    df = simulate(120, base_config)
    assert df["Missions"].max() > 0
    assert df["Tokens Burnt"].sum() > 0
    assert df["Tokens Fee to DAO"].sum() > 0


# --------------------------------------------------------------------------- #
# Vesting helpers (including the fixed testnet distribution)
# --------------------------------------------------------------------------- #
def test_init_vesting_schedules_splits_immediate_and_vesting():
    private_sales = [
        {"tokens_sold": 100, "price": 0.1, "vesting_period": 10},
        {"tokens_sold": 50, "price": 1.0, "vesting_period": 0},
    ]
    schedules, immediate, vesting_total = _init_vesting_schedules(private_sales)
    assert immediate == 50
    assert vesting_total == 100
    assert len(schedules) == 1
    assert schedules[0]["vesting_amount_per_month"] == 10


def test_immediate_private_sale_is_liquid_at_genesis(base_config):
    params = _build_params(base_config)
    state = _init_state(base_config, params)
    immediate = sum(
        s["tokens_sold"] for s in base_config["private_sales"] if s["vesting_period"] == 0
    )
    assert state.circulating_supply >= immediate > 0


def test_testnet_tokens_fully_distribute(base_config):
    """Regression: testnet tokens vest linearly and fully deplete."""
    params = _build_params(base_config)
    state = _init_state(base_config, params)
    testnet_months = base_config["testnet_distribution_period"] * 12
    for _ in range(testnet_months):
        _vest_testnet(state, params)
    assert state.testnet_development_tokens == pytest.approx(0.0, abs=1e-6)


# --------------------------------------------------------------------------- #
# Configuration validation
# --------------------------------------------------------------------------- #
def test_validate_config_accepts_valid(base_config):
    # Should not raise.
    _validate_config(base_config)


def test_validate_config_rejects_non_mapping():
    with pytest.raises(ValueError, match="mapping"):
        _validate_config(["not", "a", "dict"])


def test_validate_config_rejects_missing_keys(base_config):
    broken = dict(base_config)
    del broken["total_supply"]
    with pytest.raises(ValueError, match="missing required keys"):
        _validate_config(broken)


def test_validate_config_rejects_nonpositive_supply(make_config):
    with pytest.raises(ValueError, match="total_supply"):
        _validate_config(make_config(total_supply=0))


def test_validate_config_rejects_bad_distribution(make_config):
    bad = make_config()
    bad["token_distribution"] = dict(bad["token_distribution"])
    bad["token_distribution"]["Builders"] = 0.9  # Breaks the sum-to-1 invariant.
    with pytest.raises(ValueError, match="sum to 1.0"):
        _validate_config(bad)


def test_simulate_rejects_invalid_config(make_config):
    with pytest.raises(ValueError):
        simulate(12, make_config(total_supply=-1))


def test_make_rng_without_seed_is_generator():
    rng = simulation._make_rng({}, None)
    assert isinstance(rng, np.random.Generator)
