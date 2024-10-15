"""
main.py

This script runs the $POLN tokenomics simulation.
It reads the configuration from 'config.json' and uses the 'simulation.py' module
to perform the simulation. The results are then plotted and interpreted.

Usage:
    python main.py [config_file]

If no configuration file is specified, 'config.json' is used by default.
"""

import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from simulation import simulate

# Set random seed for reproducibility
np.random.seed(42)

def main():
    """
    Main function to run the simulation and plot results.
    """
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

        # Save simulation data to CSV
        df.to_csv(f'simulation_data_{years}years.csv', index=False)

        # Plotting the results
        plt.figure(figsize=(16, 12))  # Adjusted figure size for better layout

        # Use a 3x2 grid layout for subplots
        # Subplot 1: Circulating Supply and Total Burnt Tokens
        plt.subplot(3, 2, 1)
        plt.plot(df['Month'], df['Circulating Supply'], label='Circulating Supply')
        plt.plot(df['Month'], df['Total Burnt Tokens'], label='Total Burnt Tokens')
        plt.title(f'$POLN Token Supply over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Tokens')
        plt.legend()

        # Subplot 2: Token Price
        plt.subplot(3, 2, 2)
        plt.plot(df['Month'], df['Token Price'], color='green')
        plt.title(f'$POLN Token Price over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Token Price in USD')

        # Subplot 3: DAO Treasury Balance
        plt.subplot(3, 2, 3)
        plt.plot(df['Month'], df['DAO Treasury'], color='purple')
        plt.title(f'DAO Treasury Balance over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Tokens in DAO Treasury')

        # Subplot 4: Number of Missions
        plt.subplot(3, 2, 4)
        plt.plot(df['Month'], df['New Missions'], label='New Missions')
        plt.plot(df['Month'], df['Ongoing Missions'], label='Ongoing Missions')
        plt.plot(df['Month'], df['Ending Missions'], label='Ending Missions')
        plt.title(f'Missions over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Number of Missions')
        plt.legend()

        # Subplot 5: Market Sentiment Index
        plt.subplot(3, 2, 5)
        plt.plot(df['Month'], df['Market Sentiment Index'], color='blue')
        plt.title(f'Market Sentiment Index over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('MSI')

        # Hide the empty subplot (6th position in 3x2 grid)
        plt.subplot(3, 2, 6)
        plt.axis('off')

        plt.tight_layout()

        # Save the figure to a PNG file
        plt.savefig(f'simulation-{years}years.png', dpi=300)

        # Clear the current figure to avoid overlap in the next iteration
        plt.clf()

        # Interpretation of Results
        print(f"--- Interpretation after {years} years ---")
        final_price = df['Token Price'].iloc[-1]
        final_supply = df['Circulating Supply'].iloc[-1]
        final_total_supply = df['Total Supply'].iloc[-1]
        total_burnt = df['Total Burnt Tokens'].iloc[-1]
        dao_balance = df['DAO Treasury'].iloc[-1]
        print(f"Final Token Price: ${final_price:.2f}")
        print(f"Final Total Supply: {final_total_supply:.2f} tokens")
        print(f"Final Circulating Supply: {final_supply:.2f} tokens")
        print(f"Total Tokens Burnt: {total_burnt:.2f} tokens")
        print(f"DAO Treasury Balance: {dao_balance:.2f} tokens")
        print("----------------------------------------")

if __name__ == "__main__":
    main()
