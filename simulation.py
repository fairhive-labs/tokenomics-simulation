"""
simulation.py

This module contains the simulation logic for the $POLN tokenomics model.
It defines the 'simulate' function, which runs the simulation based on the
configuration parameters provided.

Functions:
    simulate(simulation_months, config) -> pd.DataFrame
"""

import random
import numpy as np
import pandas as pd


def simulate(simulation_months, config):
    """
    Run the tokenomics simulation for a specified number of months.

    Parameters:
    - simulation_months: int, total number of months to simulate.
    - config: dict, configuration parameters loaded from 'config.json'.

    Returns:
    - df: pandas DataFrame containing the simulation results.
    """

    # Extract parameters from the configuration
    total_supply = config['total_supply']
    initial_price = config['initial_price']
    project_cost = config['project_cost']
    protocol_fee_rate = config['protocol_fee_rate']
    staking_rate = config['staking_rate']
    mission_success_rate = config['mission_success_rate']
    pec = config['pec']  # Price Elasticity Coefficient
    msi_bull = config['msi_bull']
    msi_bear = config['msi_bear']
    msi_normal = config['msi_normal']
    bull_market_probability = config['bull_market_probability']
    bear_market_probability = config['bear_market_probability']
    market_event_duration = config['market_event_duration']
    random_fluctuation = config['random_fluctuation']
    carrying_capacity = config['carrying_capacity']
    growth_rate = config['growth_rate']
    inflection_point = config['inflection_point']
    seasonality = config['seasonality']
    token_distribution = config['token_distribution']
    initiator_selling_percentage = config['initiator_selling_percentage']
    dao_annual_consumption_rate = config['dao_annual_consumption_rate']
    dao_consumption_start_month = config['dao_consumption_start_month']
    fellowship_selling_percentage = config['fellowship_selling_percentage']
    # Extracted
    builders_selling_percentage = config['builders_selling_percentage']
    private_sales = config['private_sales']
    initial_rewards = config['initiator_rewards_initial']
    minimum_reward_per_mission = config['minimum_reward_per_mission']
    testnet_distribution_period = config['testnet_distribution_period']
    builders_lockup_period = config['builders_lockup_period']
    builders_vesting_period = config['builders_vesting_period']

    # Initialize state variables
    total_supply_current = total_supply

    # Tokens allocated
    builders_tokens = total_supply * token_distribution['Builders']
    dao_treasury = total_supply * token_distribution['DAO Treasury']
    airdrops_giveaways_tokens = total_supply * \
        token_distribution['Airdrops & Giveaways']
    # Initiator rewards pool calculated from token distribution
    initiator_rewards_pool = total_supply * \
        token_distribution['Initiator Rewards']
    testnet_development_tokens = (
        total_supply * token_distribution['Testnet Development & Partners']
    )

    # Calculate private sale tokens under vesting
    private_sale_vesting_tokens = sum(
        sale['tokens_sold'] for sale in private_sales if sale['vesting_period'] > 0
    )

    # Circulating supply excludes tokens not immediately available
    circulating_supply = total_supply - (
        builders_tokens +
        dao_treasury +
        airdrops_giveaways_tokens +
        private_sale_vesting_tokens +
        initiator_rewards_pool +
        testnet_development_tokens
    )

    # Initialize private sales vesting schedules
    private_sales_vesting_schedules = []
    for sale in private_sales:
        vesting_period = sale['vesting_period']
        tokens_sold = sale['tokens_sold']
        vesting_amount_per_month = tokens_sold / \
            vesting_period if vesting_period > 0 else 0
        private_sales_vesting_schedules.append({
            'remaining_tokens': tokens_sold,
            'vesting_period': vesting_period,
            'vesting_amount_per_month': vesting_amount_per_month,
            'current_month': 0,
        })
        if vesting_period == 0:
            # Tokens with no vesting are added to circulating supply immediately
            circulating_supply += tokens_sold

    # Adjust total supply for tokens already added to circulating supply
    total_supply_current -= (airdrops_giveaways_tokens +
                             private_sales[2]['tokens_sold'])

    total_burnt_tokens = 0
    token_price = initial_price

    # Data storage for simulation results
    results = []

    # Builders' tokens vesting per month after lockup
    builders_vesting_per_month = builders_tokens / \
        builders_vesting_period if builders_vesting_period > 0 else 0

    # DAO consumption tracking
    dao_consumption_monthly_rate = dao_annual_consumption_rate / \
        12  # Convert annual rate to monthly

    # Initiator rewards
    # Start with monthly reward
    reward_per_mission = initial_rewards['monthly']
    initial_initiator_rewards_pool = initiator_rewards_pool
    current_halving_index = 0

    # Compute the maximum number of halvings
    max_halvings = int(
        np.floor(np.log2(initial_initiator_rewards_pool /
                 minimum_reward_per_mission))
    )

    # Market event tracking
    market_event_counter = 0  # Tracks duration of current market event
    current_msi = msi_normal  # Start with normal market sentiment

    # Main simulation loop
    for month in range(1, simulation_months + 1):
        # Market Sentiment Index (MSI)
        if market_event_counter > 0:
            market_event_counter -= 1  # Continue current market event
        else:
            # Decide if a new market event occurs
            rand_event = random.random()
            if rand_event < bull_market_probability:
                current_msi = msi_bull
                market_event_counter = market_event_duration - 1
            elif rand_event < bull_market_probability + bear_market_probability:
                current_msi = msi_bear
                market_event_counter = market_event_duration - 1
            else:
                current_msi = msi_normal

        # Vesting for builders after lockup period
        if month > builders_lockup_period and builders_tokens > 0:
            vesting_amount = min(builders_vesting_per_month, builders_tokens)
            builders_tokens -= vesting_amount
            circulating_supply += vesting_amount

            # Builders' tokens are now in circulation
            # Builders sell a percentage of their tokens
            builders_sold = vesting_amount * builders_selling_percentage
        else:
            builders_sold = 0

        # Vesting for private sales
        for schedule in private_sales_vesting_schedules:
            if schedule['vesting_period'] > 0 and schedule['remaining_tokens'] > 0:
                schedule['current_month'] += 1
                if schedule['current_month'] <= schedule['vesting_period']:
                    vesting_amount = schedule['vesting_amount_per_month']
                    schedule['remaining_tokens'] -= vesting_amount
                    circulating_supply += vesting_amount
                    # Tokens are now in circulation

        # Distribute testnet tokens
        if testnet_development_tokens > 0:
            testnet_vesting_per_month = testnet_development_tokens / (
                testnet_distribution_period * 12
            )
            vesting_amount = min(testnet_vesting_per_month,
                                 testnet_development_tokens)
            testnet_development_tokens -= vesting_amount
            circulating_supply += vesting_amount
            # Tokens are now in circulation

        # DAO consumes a percentage of its treasury annually, starting after a delay
        if month >= dao_consumption_start_month and dao_treasury > 0:
            dao_consumed = dao_treasury * dao_consumption_monthly_rate
            dao_treasury -= dao_consumed
            circulating_supply += dao_consumed
            # Tokens are now in circulation

        # Ensure circulating supply does not exceed total supply
        if circulating_supply > total_supply_current:
            circulating_supply = total_supply_current

        # Calculate baseline number of missions using logistic growth
        exponent = growth_rate * (month - inflection_point)
        baseline_missions = carrying_capacity / (1 + np.exp(-exponent))

        # Apply seasonal adjustments
        month_of_year = (month - 1) % 12 + 1  # Month in [1,12]
        seasonal_factor = seasonality.get(str(month_of_year), 1.0)
        adjusted_missions = baseline_missions * seasonal_factor

        # Apply random fluctuations
        fluctuation = random.uniform(-random_fluctuation, random_fluctuation)
        final_missions = adjusted_missions * (1 + fluctuation)

        # Convert final_missions to integer
        num_missions = int(final_missions)

        # Initialize monthly metrics
        tokens_staked = 0
        tokens_burnt = 0
        tokens_fee_distributed = 0
        tokens_fee_to_dao = 0
        net_token_demand = 0
        initiator_sold = 0
        fellowship_sold = 0

        # Process missions in aggregate
        if num_missions > 0:
            # Determine the number of successful and failed missions
            num_successful = int(num_missions * mission_success_rate)
            num_failed = num_missions - num_successful

            # Calculate protocol fee in $POLN
            protocol_fee_usd = project_cost * protocol_fee_rate
            protocol_fee_poln = protocol_fee_usd / token_price

            # Ensure protocol_fee_poln doesn't become too small
            if protocol_fee_poln < 1e-18:
                protocol_fee_poln = 1e-18

            # Calculate staking amount
            staking_amount = protocol_fee_poln * staking_rate

            # Aggregate tokenomics calculations
            tokens_staked = staking_amount * num_missions
            tokens_burnt = staking_amount * num_failed

            # Update total burnt tokens and reduce total supply
            total_burnt_tokens += tokens_burnt
            total_supply_current -= tokens_burnt

            # Update circulating supply by removing burnt tokens
            circulating_supply -= tokens_burnt

            # Tokens fee distributed to fellowship members
            tokens_fee_distributed = protocol_fee_poln * num_successful
            # Tokens fee to DAO treasury from failed missions
            tokens_fee_to_dao = protocol_fee_poln * num_failed
            dao_treasury += tokens_fee_to_dao

            # Fellowship members receive tokens (from staking rewards)
            fellowship_tokens = tokens_fee_distributed
            fellowship_sold = fellowship_tokens * fellowship_selling_percentage

            # Add fellowship tokens to circulating supply (no lockup or vesting)
            circulating_supply += fellowship_tokens

            # Initiator receives rewards
            initiator_rewards_this_month = reward_per_mission * num_successful

            # Reduce the initiator rewards pool
            initiator_rewards_pool -= initiator_rewards_this_month
            if initiator_rewards_pool < 0:
                # Adjust rewards if pool is depleted
                initiator_rewards_this_month += initiator_rewards_pool  # Negative value adjustment
                initiator_rewards_pool = 0

            # Add initiator rewards to circulating supply (no lockup or vesting)
            circulating_supply += initiator_rewards_this_month

            # Initiator sells a percentage of rewards
            initiator_sold = initiator_rewards_this_month * initiator_selling_percentage

            # Calculate net token demand
            net_token_demand = (
                (protocol_fee_poln * num_missions)
                - tokens_burnt
                - initiator_sold
                - fellowship_sold
                - builders_sold  # Include builders sold tokens
            )

            # Check for halving
            halving_threshold = initial_initiator_rewards_pool / \
                (2 ** (current_halving_index + 1))
            if (
                current_halving_index < max_halvings and
                initiator_rewards_pool <= halving_threshold and
                reward_per_mission > minimum_reward_per_mission
            ):
                # Halving occurs
                reward_per_mission /= 2
                current_halving_index += 1
                # Ensure reward_per_mission does not go below minimum_reward_per_mission
                if reward_per_mission < minimum_reward_per_mission:
                    reward_per_mission = minimum_reward_per_mission

        # Adjust token price based on net demand and market sentiment
        if circulating_supply > 0 and net_token_demand != 0:
            demand_supply_ratio = net_token_demand / circulating_supply
            price_change_percentage = pec * demand_supply_ratio * current_msi
            # Cap price change percentage to prevent extreme fluctuations
            price_change_percentage = max(
                min(price_change_percentage, 0.2), -0.2)
            token_price *= (1 + price_change_percentage)
        else:
            # Avoid division by zero
            demand_supply_ratio = 0
            price_change_percentage = 0

        # Store monthly results
        results.append({
            'Month': month,
            'Circulating Supply': circulating_supply,
            'Total Supply': total_supply_current,
            'Token Price': token_price,
            'Tokens Staked': tokens_staked,
            'Tokens Burnt': tokens_burnt,
            'Tokens Fee Distributed': tokens_fee_distributed,
            'Tokens Fee to DAO': tokens_fee_to_dao,
            'DAO Treasury': dao_treasury,
            'Total Burnt Tokens': total_burnt_tokens,
            'Market Sentiment Index': current_msi,
            'Net Token Demand': net_token_demand,
            'Missions': num_missions,
            'Initiator Rewards Pool': initiator_rewards_pool,
            'Reward per Mission': reward_per_mission,
            'Halving Index': current_halving_index,
            'Builders Sold': builders_sold,
            'Fellowship Sold': fellowship_sold,
        })

    # Convert results to a pandas DataFrame
    df = pd.DataFrame(results)
    return df
