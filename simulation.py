"""
simulation.py

Monte Carlo engine for the ``$POLN`` tokenomics model.

The public entry point is :func:`simulate`, which runs the month-by-month
simulation described by a configuration mapping (see ``config.json``) and returns
a :class:`pandas.DataFrame` with one row per simulated month.

The engine is deterministic when a random seed is supplied (via the
``random_seed`` config key or an explicit ``rng`` argument), which keeps the
model reproducible and unit-testable. It relies on :class:`numpy.random.Generator`
rather than the global :mod:`random` module (faster, seedable, and free of the
insecure-PRNG warning raised by static-analysis tools).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Keys that must be present in a configuration mapping for :func:`simulate`.
REQUIRED_KEYS = (
    "total_supply",
    "initial_price",
    "project_cost",
    "protocol_fee_rate",
    "staking_rate",
    "mission_success_rate",
    "pec",
    "msi_bull",
    "msi_bear",
    "msi_normal",
    "roadmap_effect",
    "roadmap_cycle",
    "bull_market_probability",
    "bear_market_probability",
    "market_event_duration",
    "random_fluctuation",
    "carrying_capacity",
    "growth_rate",
    "inflection_point",
    "seasonality",
    "token_distribution",
    "initiator_selling_percentage",
    "dao_annual_consumption_rate",
    "dao_consumption_start_month",
    "fellowship_selling_percentage",
    "builders_selling_percentage",
    "private_sales",
    "initiator_rewards_initial",
    "minimum_reward_per_mission",
    "testnet_distribution_period",
    "builders_lockup_period",
    "builders_vesting_period",
)

# Maximum monthly price move, in either direction (±20%).
MAX_PRICE_CHANGE = 0.2

# Ordered column names of the DataFrame returned by :func:`simulate`.
RESULT_COLUMNS = (
    "Month",
    "Circulating Supply",
    "Total Supply",
    "Token Price",
    "Tokens Staked",
    "Tokens Burnt",
    "Tokens Fee Distributed",
    "Tokens Fee to DAO",
    "DAO Treasury",
    "Total Burnt Tokens",
    "Market Sentiment Index",
    "Net Token Demand",
    "Missions",
    "Initiator Rewards Pool",
    "Reward per Mission",
    "Halving Index",
    "Builders Sold",
    "Fellowship Sold",
)


def _validate_config(config):
    """Validate the configuration mapping, raising :class:`ValueError` on error.

    Checks for required keys, a strictly positive total supply, and a token
    distribution whose weights sum to approximately 1.0.
    """
    if not isinstance(config, dict):
        raise ValueError("config must be a mapping")

    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise ValueError(f"config is missing required keys: {sorted(missing)}")

    if config["total_supply"] <= 0:
        raise ValueError("total_supply must be strictly positive")

    distribution_total = sum(config["token_distribution"].values())
    if not np.isclose(distribution_total, 1.0, atol=1e-6):
        raise ValueError(
            f"token_distribution must sum to 1.0 (got {distribution_total})"
        )


def _make_rng(config, rng):
    """Return a :class:`numpy.random.Generator`.

    An explicit ``rng`` takes precedence; otherwise a generator is seeded from
    the optional ``random_seed`` config key (``None`` yields a nondeterministic
    generator).
    """
    if rng is not None:
        return rng
    return np.random.default_rng(config.get("random_seed"))


@dataclass
class _RunParams:  # pylint: disable=too-many-instance-attributes
    """Per-run constants derived once from the configuration."""

    total_supply: float
    initial_price: float
    project_cost: float
    protocol_fee_rate: float
    staking_rate: float
    mission_success_rate: float
    pec: float
    msi_bull: float
    msi_bear: float
    msi_normal: float
    roadmap_effect: float
    roadmap_cycle: int
    bull_market_probability: float
    bear_market_probability: float
    market_event_duration: int
    random_fluctuation: float
    carrying_capacity: float
    growth_rate: float
    inflection_point: float
    seasonality: dict
    initiator_selling_percentage: float
    fellowship_selling_percentage: float
    builders_selling_percentage: float
    dao_consumption_monthly_rate: float
    dao_consumption_start_month: int
    minimum_reward_per_mission: float
    builders_lockup_period: int
    builders_vesting_per_month: float
    testnet_vesting_per_month: float
    initial_initiator_rewards_pool: float
    max_halvings: int


@dataclass
class _State:  # pylint: disable=too-many-instance-attributes
    """Mutable running state advanced each simulated month."""

    circulating_supply: float
    total_supply: float
    token_price: float
    dao_treasury: float
    builders_tokens_remaining: float
    testnet_development_tokens: float
    initiator_rewards_pool: float
    private_sale_vesting_tokens_remaining: float
    total_burnt_tokens: float = 0.0
    reward_per_mission: float = 0.0
    current_halving_index: int = 0
    current_msi: float = 1.0
    market_event_counter: int = 0
    vesting_schedules: list = field(default_factory=list)


def _build_params(config):
    """Compute the :class:`_RunParams` constants for a run."""
    total_supply = config["total_supply"]
    distribution = config["token_distribution"]

    builders_tokens_total = total_supply * distribution["Builders"]
    builders_vesting_period = config["builders_vesting_period"]
    builders_vesting_per_month = (
        builders_tokens_total / builders_vesting_period
        if builders_vesting_period > 0
        else 0.0
    )

    # Testnet tokens vest linearly over the whole distribution window. The rate
    # is computed once from the *initial* allocation so the allocation fully
    # distributes over ``testnet_distribution_period`` years.
    testnet_total = total_supply * distribution["Testnet Development & Partners"]
    testnet_months = config["testnet_distribution_period"] * 12
    testnet_vesting_per_month = (
        testnet_total / testnet_months if testnet_months > 0 else 0.0
    )

    initial_initiator_rewards_pool = total_supply * distribution["Initiator Rewards"]
    minimum_reward = config["minimum_reward_per_mission"]
    max_halvings = int(
        np.floor(np.log2(initial_initiator_rewards_pool / minimum_reward))
    )

    return _RunParams(
        total_supply=total_supply,
        initial_price=config["initial_price"],
        project_cost=config["project_cost"],
        protocol_fee_rate=config["protocol_fee_rate"],
        staking_rate=config["staking_rate"],
        mission_success_rate=config["mission_success_rate"],
        pec=config["pec"],
        msi_bull=config["msi_bull"],
        msi_bear=config["msi_bear"],
        msi_normal=config["msi_normal"],
        roadmap_effect=config["roadmap_effect"],
        roadmap_cycle=config["roadmap_cycle"],
        bull_market_probability=config["bull_market_probability"],
        bear_market_probability=config["bear_market_probability"],
        market_event_duration=config["market_event_duration"],
        random_fluctuation=config["random_fluctuation"],
        carrying_capacity=config["carrying_capacity"],
        growth_rate=config["growth_rate"],
        inflection_point=config["inflection_point"],
        seasonality=config["seasonality"],
        initiator_selling_percentage=config["initiator_selling_percentage"],
        fellowship_selling_percentage=config["fellowship_selling_percentage"],
        builders_selling_percentage=config["builders_selling_percentage"],
        dao_consumption_monthly_rate=config["dao_annual_consumption_rate"] / 12,
        dao_consumption_start_month=config["dao_consumption_start_month"],
        minimum_reward_per_mission=minimum_reward,
        builders_lockup_period=config["builders_lockup_period"],
        builders_vesting_per_month=builders_vesting_per_month,
        testnet_vesting_per_month=testnet_vesting_per_month,
        initial_initiator_rewards_pool=initial_initiator_rewards_pool,
        max_halvings=max_halvings,
    )


def _init_vesting_schedules(private_sales):
    """Split private sales into vesting schedules and immediately liquid tokens.

    Returns ``(schedules, immediate_tokens, vesting_total)`` where ``schedules``
    only contains rounds with a positive vesting period. Rounds with a zero
    vesting period are liquid at genesis and counted in ``immediate_tokens``.
    """
    schedules = []
    immediate_tokens = 0.0
    vesting_total = 0.0
    for sale in private_sales:
        vesting_period = sale["vesting_period"]
        tokens_sold = sale["tokens_sold"]
        if vesting_period > 0:
            schedules.append(
                {
                    "remaining_tokens": tokens_sold,
                    "vesting_period": vesting_period,
                    "vesting_amount_per_month": tokens_sold / vesting_period,
                    "current_month": 0,
                }
            )
            vesting_total += tokens_sold
        else:
            immediate_tokens += tokens_sold
    return schedules, immediate_tokens, vesting_total


def _init_state(config, params):
    """Build the initial :class:`_State` from the configuration."""
    total_supply = params.total_supply
    distribution = config["token_distribution"]

    builders_tokens_remaining = total_supply * distribution["Builders"]
    dao_treasury = total_supply * distribution["DAO Treasury"]
    airdrops_giveaways_tokens = total_supply * distribution["Airdrops & Giveaways"]
    initiator_rewards_pool = total_supply * distribution["Initiator Rewards"]
    testnet_development_tokens = (
        total_supply * distribution["Testnet Development & Partners"]
    )

    schedules, immediate_tokens, vesting_total = _init_vesting_schedules(
        config["private_sales"]
    )

    # Circulating supply excludes tokens that are not immediately available.
    circulating_supply = total_supply - (
        builders_tokens_remaining
        + dao_treasury
        + airdrops_giveaways_tokens
        + initiator_rewards_pool
        + testnet_development_tokens
        + vesting_total
    )
    # Private-sale rounds with no vesting are liquid from genesis.
    circulating_supply += immediate_tokens

    return _State(
        circulating_supply=circulating_supply,
        total_supply=total_supply,
        token_price=params.initial_price,
        dao_treasury=dao_treasury,
        builders_tokens_remaining=builders_tokens_remaining,
        testnet_development_tokens=testnet_development_tokens,
        initiator_rewards_pool=initiator_rewards_pool,
        private_sale_vesting_tokens_remaining=vesting_total,
        reward_per_mission=config["initiator_rewards_initial"]["monthly"],
        current_msi=params.msi_normal,
        vesting_schedules=schedules,
    )


def _update_market_sentiment(state, params, rng, month):
    """Advance the Market Sentiment Index for the given month."""
    if state.market_event_counter > 0:
        state.market_event_counter -= 1  # Continue the current market event.
    else:
        rand_event = rng.random()
        if rand_event < params.bull_market_probability:
            state.current_msi = params.msi_bull
            state.market_event_counter = params.market_event_duration - 1
        elif rand_event < params.bull_market_probability + params.bear_market_probability:
            state.current_msi = params.msi_bear
            state.market_event_counter = params.market_event_duration - 1
        else:
            state.current_msi = params.msi_normal

    if month % params.roadmap_cycle == 0:
        state.current_msi *= params.roadmap_effect


def _vest_builders(state, params, month):
    """Vest builders' tokens after lockup and return the amount they sell."""
    if month <= params.builders_lockup_period or state.builders_tokens_remaining <= 0:
        return 0.0
    vesting_amount = min(
        params.builders_vesting_per_month, state.builders_tokens_remaining
    )
    state.builders_tokens_remaining -= vesting_amount
    state.circulating_supply += vesting_amount
    return vesting_amount * params.builders_selling_percentage


def _vest_private_sales(state):
    """Release private-sale tokens according to their vesting schedules."""
    for schedule in state.vesting_schedules:
        if schedule["remaining_tokens"] <= 0:
            continue
        schedule["current_month"] += 1
        if schedule["current_month"] <= schedule["vesting_period"]:
            vesting_amount = min(
                schedule["vesting_amount_per_month"], schedule["remaining_tokens"]
            )
            schedule["remaining_tokens"] -= vesting_amount
            state.private_sale_vesting_tokens_remaining -= vesting_amount
            state.circulating_supply += vesting_amount


def _vest_testnet(state, params):
    """Release the monthly linear tranche of testnet tokens."""
    if state.testnet_development_tokens <= 0:
        return
    vesting_amount = min(
        params.testnet_vesting_per_month, state.testnet_development_tokens
    )
    state.testnet_development_tokens -= vesting_amount
    state.circulating_supply += vesting_amount


def _consume_dao(state, params, month):
    """Move the monthly DAO treasury drawdown into circulation."""
    if month < params.dao_consumption_start_month or state.dao_treasury <= 0:
        return
    dao_consumed = min(
        state.dao_treasury * params.dao_consumption_monthly_rate, state.dao_treasury
    )
    state.dao_treasury -= dao_consumed
    state.circulating_supply += dao_consumed


def _clamp_supply(state, params):
    """Keep circulating supply within [0, total_supply]."""
    total_allocated = (
        state.circulating_supply
        + state.builders_tokens_remaining
        + state.dao_treasury
        + state.testnet_development_tokens
        + state.initiator_rewards_pool
        + state.private_sale_vesting_tokens_remaining
    )
    if total_allocated > params.total_supply:
        state.circulating_supply -= total_allocated - params.total_supply
    state.circulating_supply = max(state.circulating_supply, 0.0)


def _mission_count(params, rng, month):
    """Return the integer number of missions for the month.

    Baseline missions follow logistic growth, adjusted by a seasonal factor and
    a uniform random fluctuation.
    """
    exponent = params.growth_rate * (month - params.inflection_point)
    baseline_missions = params.carrying_capacity / (1 + np.exp(-exponent))

    month_of_year = (month - 1) % 12 + 1
    seasonal_factor = params.seasonality.get(str(month_of_year), 1.0)
    adjusted_missions = baseline_missions * seasonal_factor

    fluctuation = rng.uniform(-params.random_fluctuation, params.random_fluctuation)
    return int(adjusted_missions * (1 + fluctuation))


def _process_missions(state, params, num_missions, builders_sold):
    """Process a month's missions, mutating ``state`` and returning metrics."""
    metrics = {
        "Tokens Staked": 0.0,
        "Tokens Burnt": 0.0,
        "Tokens Fee Distributed": 0.0,
        "Tokens Fee to DAO": 0.0,
        "Net Token Demand": 0.0,
        "Fellowship Sold": 0.0,
    }
    if num_missions <= 0:
        return metrics

    num_successful = int(num_missions * params.mission_success_rate)
    num_failed = num_missions - num_successful

    protocol_fee_usd = params.project_cost * params.protocol_fee_rate
    protocol_fee_poln = max(protocol_fee_usd / state.token_price, 1e-18)
    staking_amount = protocol_fee_poln * params.staking_rate

    tokens_staked = staking_amount * num_missions
    tokens_burnt = staking_amount * num_failed
    state.total_burnt_tokens += tokens_burnt
    state.circulating_supply = max(state.circulating_supply - tokens_burnt, 0.0)

    tokens_fee_distributed = protocol_fee_poln * num_successful
    tokens_fee_to_dao = protocol_fee_poln * num_failed
    state.dao_treasury += tokens_fee_to_dao

    fellowship_sold = tokens_fee_distributed * params.fellowship_selling_percentage
    state.circulating_supply += tokens_fee_distributed

    initiator_rewards_this_month = min(
        state.reward_per_mission * num_successful, state.initiator_rewards_pool
    )
    state.initiator_rewards_pool -= initiator_rewards_this_month
    state.circulating_supply += initiator_rewards_this_month
    initiator_sold = initiator_rewards_this_month * params.initiator_selling_percentage

    net_token_demand = (
        (protocol_fee_poln * num_missions)
        - tokens_burnt
        - initiator_sold
        - fellowship_sold
        - builders_sold
    )

    metrics.update(
        {
            "Tokens Staked": tokens_staked,
            "Tokens Burnt": tokens_burnt,
            "Tokens Fee Distributed": tokens_fee_distributed,
            "Tokens Fee to DAO": tokens_fee_to_dao,
            "Net Token Demand": net_token_demand,
            "Fellowship Sold": fellowship_sold,
        }
    )
    return metrics


def _maybe_halve(state, params):
    """Halve the per-mission reward once the pool crosses the next threshold."""
    halving_threshold = params.initial_initiator_rewards_pool / (
        2 ** (state.current_halving_index + 1)
    )
    if (
        state.current_halving_index < params.max_halvings
        and state.initiator_rewards_pool <= halving_threshold
        and state.reward_per_mission > params.minimum_reward_per_mission
    ):
        state.reward_per_mission /= 2
        state.current_halving_index += 1
        state.reward_per_mission = max(
            state.reward_per_mission, params.minimum_reward_per_mission
        )


def _apply_price_change(state, params, net_token_demand):
    """Adjust the token price from net demand and market sentiment."""
    if state.circulating_supply > 0 and net_token_demand != 0:
        demand_supply_ratio = net_token_demand / state.circulating_supply
        price_change = params.pec * demand_supply_ratio * state.current_msi
        price_change = max(min(price_change, MAX_PRICE_CHANGE), -MAX_PRICE_CHANGE)
        state.token_price *= 1 + price_change


def _record_row(month, state, num_missions, builders_sold, metrics):
    """Assemble one result row from the current state and monthly metrics."""
    return {
        "Month": month,
        "Circulating Supply": state.circulating_supply,
        "Total Supply": state.total_supply,
        "Token Price": state.token_price,
        "Tokens Staked": metrics["Tokens Staked"],
        "Tokens Burnt": metrics["Tokens Burnt"],
        "Tokens Fee Distributed": metrics["Tokens Fee Distributed"],
        "Tokens Fee to DAO": metrics["Tokens Fee to DAO"],
        "DAO Treasury": state.dao_treasury,
        "Total Burnt Tokens": state.total_burnt_tokens,
        "Market Sentiment Index": state.current_msi,
        "Net Token Demand": metrics["Net Token Demand"],
        "Missions": num_missions,
        "Initiator Rewards Pool": state.initiator_rewards_pool,
        "Reward per Mission": state.reward_per_mission,
        "Halving Index": state.current_halving_index,
        "Builders Sold": builders_sold,
        "Fellowship Sold": metrics["Fellowship Sold"],
    }


def simulate(simulation_months, config, rng=None):
    """Run the tokenomics simulation for a number of months.

    Parameters
    ----------
    simulation_months:
        Total number of months to simulate.
    config:
        Configuration mapping (see ``config.json``). Validated on entry.
    rng:
        Optional :class:`numpy.random.Generator`. When omitted, one is created
        from the ``random_seed`` config key (``None`` for a nondeterministic run).

    Returns
    -------
    pandas.DataFrame
        One row per simulated month, with the columns in :data:`RESULT_COLUMNS`.
    """
    _validate_config(config)
    rng = _make_rng(config, rng)

    params = _build_params(config)
    state = _init_state(config, params)

    results = []
    for month in range(1, simulation_months + 1):
        _update_market_sentiment(state, params, rng, month)

        builders_sold = _vest_builders(state, params, month)
        _vest_private_sales(state)
        _vest_testnet(state, params)
        _consume_dao(state, params, month)
        _clamp_supply(state, params)

        num_missions = _mission_count(params, rng, month)
        metrics = _process_missions(state, params, num_missions, builders_sold)
        _maybe_halve(state, params)
        _clamp_supply(state, params)
        _apply_price_change(state, params, metrics["Net Token Demand"])

        results.append(
            _record_row(month, state, num_missions, builders_sold, metrics)
        )

    return pd.DataFrame(results, columns=list(RESULT_COLUMNS))
