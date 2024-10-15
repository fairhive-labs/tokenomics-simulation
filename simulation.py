"""
simulation.py

This module contains the simulation logic for the $POLN tokenomics model.
It defines the 'simulate' function, which runs the simulation based on the
configuration parameters provided.

Functions:
    simulate(simulation_months, config) -> pd.DataFrame
"""

import random
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
    TOTAL_SUPPLY = config['TOTAL_SUPPLY']
    INITIAL_PRICE = config['INITIAL_PRICE']
    PROJECT_COST = config['PROJECT_COST']
    PROTOCOL_FEE_RATE = config['PROTOCOL_FEE_RATE']
    STAKING_RATE = config['STAKING_RATE']
    MISSION_SUCCESS_RATE = config['MISSION_SUCCESS_RATE']
    PEC = config['PEC']
    MSI_MIN = config['MSI_MIN']
    MSI_MAX = config['MSI_MAX']
    GROWTH_RATIO = config['GROWTH_RATIO']
    MAX_MISSIONS = config['MAX_MISSIONS']
    RANDOM_FLUCTUATION = config['RANDOM_FLUCTUATION']
    initial_missions = config['initial_missions']
    mission_duration = config['mission_duration']
    token_distribution = config['token_distribution']
    builders_lockup_period = config['builders_lockup_period']
    builders_vesting_period = config['builders_vesting_period']
    private_sales = config['private_sales']

    # Initialize state variables
    total_supply = TOTAL_SUPPLY

    # Tokens allocated
    builders_tokens = TOTAL_SUPPLY * token_distribution['Builders']
    dao_treasury = TOTAL_SUPPLY * token_distribution['DAO Treasury']
    airdrops_giveaways_tokens = TOTAL_SUPPLY * token_distribution['Airdrops & Giveaways']
    initiator_rewards_tokens = TOTAL_SUPPLY * token_distribution['Initiator Rewards']
    testnet_development_tokens = TOTAL_SUPPLY * token_distribution['Testnet Development & Partners']

    # Calculate private sale tokens under vesting
    private_sale_vesting_tokens = sum(
        sale['tokens_sold'] for sale in private_sales if sale['vesting_period'] > 0
    )

    # Circulating supply excludes tokens not immediately available
    circulating_supply = TOTAL_SUPPLY - (
        builders_tokens +
        dao_treasury +
        airdrops_giveaways_tokens +
        private_sale_vesting_tokens +
        initiator_rewards_tokens +
        testnet_development_tokens
    )

    # Initialize private sales vesting schedules
    private_sales_vesting_schedules = []
    for sale in private_sales:
        vesting_period = sale['vesting_period']
        tokens_sold = sale['tokens_sold']
        vesting_amount_per_month = tokens_sold / vesting_period if vesting_period > 0 else 0
        private_sales_vesting_schedules.append({
            'remaining_tokens': tokens_sold,
            'vesting_period': vesting_period,
            'vesting_amount_per_month': vesting_amount_per_month,
            'current_month': 0,
        })
        if vesting_period == 0:
            # Tokens with no vesting are added to circulating supply immediately
            circulating_supply += tokens_sold

    total_burnt_tokens = 0
    token_price = INITIAL_PRICE

    # Data storage for simulation results
    results = []

    # Builders' tokens vesting per month after lockup
    builders_vesting_per_month = builders_tokens / builders_vesting_period if builders_vesting_period > 0 else 0

    # Initiator rewards vesting schedule (assuming similar to builders)
    initiator_vesting_period = builders_vesting_period  # Assuming same vesting period
    initiator_vesting_per_month = initiator_rewards_tokens / initiator_vesting_period if initiator_vesting_period > 0 else 0

    # Testnet development tokens vesting schedule (assuming immediate release)
    circulating_supply += testnet_development_tokens  # Add to circulating supply

    # Initialize mission counts
    new_missions = initial_missions
    ongoing_missions_history = []  # List to keep track of new missions each month for duration

    # Main simulation loop
    for month in range(1, simulation_months + 1):
        # Market Sentiment Index (fluctuates between MSI_MIN and MSI_MAX)
        MSI = random.uniform(MSI_MIN, MSI_MAX)

        # Vesting for builders after lockup period
        if month > builders_lockup_period and builders_tokens > 0:
            vesting_amount = min(builders_vesting_per_month, builders_tokens)
            builders_tokens -= vesting_amount
            circulating_supply += vesting_amount

        # Vesting for initiator rewards (assuming similar lockup and vesting)
        if month > builders_lockup_period and initiator_rewards_tokens > 0:
            vesting_amount = min(initiator_vesting_per_month, initiator_rewards_tokens)
            initiator_rewards_tokens -= vesting_amount
            circulating_supply += vesting_amount

        # Vesting for private sales
        for schedule in private_sales_vesting_schedules:
            if schedule['vesting_period'] > 0 and schedule['remaining_tokens'] > 0:
                schedule['current_month'] += 1
                if schedule['current_month'] <= schedule['vesting_period']:
                    vesting_amount = schedule['vesting_amount_per_month']
                    schedule['remaining_tokens'] -= vesting_amount
                    circulating_supply += vesting_amount

        # Ensure circulating supply does not exceed total supply
        if circulating_supply > total_supply:
            circulating_supply = total_supply

        # Adjust number of new missions
        # Apply growth ratio
        new_missions *= GROWTH_RATIO

        # Apply random fluctuation (±20% or as specified)
        fluctuation = random.uniform(-RANDOM_FLUCTUATION, RANDOM_FLUCTUATION)
        new_missions *= (1 + fluctuation)

        # Ensure new_missions is within realistic bounds
        new_missions = int(min(new_missions, MAX_MISSIONS))

        # Add current new missions to ongoing missions history
        ongoing_missions_history.append(new_missions)

        # Calculate number of ending missions
        if len(ongoing_missions_history) > mission_duration:
            ending_missions = ongoing_missions_history.pop(0)
        else:
            ending_missions = 0  # No missions ending yet if mission_duration not reached

        # Calculate number of ongoing missions
        ongoing_missions = sum(ongoing_missions_history)

        # Initialize monthly metrics
        tokens_staked = 0
        tokens_burnt = 0
        tokens_fee_distributed = 0
        tokens_fee_to_dao = 0
        net_token_demand = 0

        # Process ending missions
        if ending_missions > 0:
            # Determine the number of successful and failed missions
            num_successful = int(ending_missions * MISSION_SUCCESS_RATE)
            num_failed = ending_missions - num_successful

            # Calculate protocol fee in $POLN
            protocol_fee_usd = PROJECT_COST * PROTOCOL_FEE_RATE
            protocol_fee_poln = protocol_fee_usd / token_price

            # Ensure protocol_fee_poln doesn't become too small
            if protocol_fee_poln < 1e-6:
                protocol_fee_poln = 1e-6

            # Calculate staking amount
            staking_amount = protocol_fee_poln * STAKING_RATE

            # Aggregate tokenomics calculations
            tokens_staked = staking_amount * ending_missions
            tokens_burnt = staking_amount * num_failed
            total_burnt_tokens += tokens_burnt
            total_supply -= tokens_burnt

            tokens_fee_distributed = protocol_fee_poln * num_successful
            tokens_fee_to_dao = protocol_fee_poln * num_failed
            dao_treasury += tokens_fee_to_dao

            net_token_demand = (protocol_fee_poln * ending_missions) - tokens_burnt

            # Update circulating supply
            circulating_supply -= tokens_burnt

            # Ensure circulating supply does not go negative
            if circulating_supply < 0:
                circulating_supply = 0

        # Adjust token price based on net demand (refined model)
        if circulating_supply > 0 and net_token_demand != 0:
            demand_supply_ratio = net_token_demand / circulating_supply
            price_change_percentage = PEC * demand_supply_ratio * MSI
            # Cap price change percentage to prevent extreme fluctuations
            price_change_percentage = max(min(price_change_percentage, 0.1), -0.1)
            token_price *= (1 + price_change_percentage)
        else:
            # Avoid division by zero
            demand_supply_ratio = 0
            price_change_percentage = 0

        # Store monthly results
        results.append({
            'Month': month,
            'Circulating Supply': circulating_supply,
            'Total Supply': total_supply,
            'Token Price': token_price,
            'Tokens Staked': tokens_staked,
            'Tokens Burnt': tokens_burnt,
            'Tokens Fee Distributed': tokens_fee_distributed,
            'Tokens Fee to DAO': tokens_fee_to_dao,
            'DAO Treasury': dao_treasury,
            'Total Burnt Tokens': total_burnt_tokens,
            'Market Sentiment Index': MSI,
            'Net Token Demand': net_token_demand,
            'New Missions': new_missions,
            'Ongoing Missions': ongoing_missions,
            'Ending Missions': ending_missions,
        })

    # Convert results to a pandas DataFrame
    df = pd.DataFrame(results)
    return df
