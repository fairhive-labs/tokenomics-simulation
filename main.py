"""
main.py

This is the main script that runs the $POLN tokenomics simulation.
It reads the configuration from 'config.json' and uses the 'simulation.py' module
to perform the simulation. The results are then plotted and interpreted.

Usage:
    python main.py [config_file]

If no configuration file is specified, 'config.json' is used by default.
"""

import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from simulation import simulate

# Set random seed for reproducibility
np.random.seed(42)

def main():
    # Use the configuration file specified in the command-line arguments
    config_file_name = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    with open(config_file_name, 'r') as config_file:
        config = json.load(config_file)

    # Extract simulation periods
    SIMULATION_YEARS = config['SIMULATION_YEARS']
    MONTHS_PER_YEAR = config['MONTHS_PER_YEAR']

    # Run simulations for each period
    for years in SIMULATION_YEARS:
        simulation_months = years * MONTHS_PER_YEAR
        print(f"\nSimulating {years} years ({simulation_months} months)...")
        df = simulate(simulation_months, config)

        # Plotting the results
        plt.figure(figsize=(14, 14))

        # Plot Circulating Supply and Total Burnt Tokens
        plt.subplot(4, 1, 1)
        plt.plot(df['Month'], df['Circulating Supply'], label='Circulating Supply')
        plt.plot(df['Month'], df['Total Burnt Tokens'], label='Total Burnt Tokens')
        plt.title(f'$POLN Token Circulation over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Tokens')
        plt.legend()

        # Plot Token Price
        plt.subplot(4, 1, 2)
        plt.plot(df['Month'], df['Token Price'], color='green')
        plt.title(f'$POLN Token Price over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Token Price in USD')

        # Plot DAO Treasury Balance
        plt.subplot(4, 1, 3)
        plt.plot(df['Month'], df['DAO Treasury'], color='purple')
        plt.title(f'DAO Treasury Balance over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Tokens in DAO Treasury')

        # Plot Number of Missions
        plt.subplot(4, 1, 4)
        plt.plot(df['Month'], df['Number of Missions'], color='orange')
        plt.title(f'Number of Missions over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Number of Missions')

        plt.tight_layout()
        plt.show()

        # Interpretation of Results
        print(f"--- Interpretation after {years} years ---")
        final_price = df['Token Price'].iloc[-1]
        final_supply = df['Circulating Supply'].iloc[-1]
        total_burnt = df['Total Burnt Tokens'].iloc[-1]
        dao_balance = df['DAO Treasury'].iloc[-1]
        print(f"Final Token Price: ${final_price:.2f}")
        print(f"Final Circulating Supply: {final_supply:.2f} tokens")
        print(f"Total Tokens Burnt: {total_burnt:.2f} tokens")
        print(f"DAO Treasury Balance: {dao_balance:.2f} tokens")
        print("----------------------------------------")

if __name__ == "__main__":
    main()
