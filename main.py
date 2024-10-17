"""
main.py

This script runs the PoLN tokenomics simulation and outputs the results.
It reads the configuration parameters from 'config.json', runs the simulation,
saves the results to CSV files, and generates plots.

Usage:
    python main.py
"""

import json
import os
import matplotlib.pyplot as plt
from simulation import simulate


def main():
    """
    Main function to execute the tokenomics simulation and handle output.
    """
    # Load configuration
    with open('config.json', 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)

    # Improved directory creation
    os.makedirs('results', exist_ok=True)

    # Run simulations for each specified duration
    for years in config['simulation_years']:
        simulation_months = years * config['months_per_year']
        df = simulate(simulation_months, config)

        # Save results to CSV
        csv_filename = f'results/simulation_{years}yrs.csv'
        df.to_csv(csv_filename, index=False)

        # Plot results
        plt.figure(figsize=(15, 20))

        # Subplot 1: Token Price
        plt.subplot(6, 1, 1)
        plt.plot(df['Month'], df['Token Price'],
                 label='Token Price', color='blue')
        plt.title(f'Token Price Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Token Price ($)')
        plt.grid(True)
        plt.legend()

        # Subplot 2: Circulating Supply and Total Burnt Tokens
        plt.subplot(6, 1, 2)
        plt.plot(df['Month'], df['Circulating Supply'],
                 label='Circulating Supply', color='orange')
        plt.plot(df['Month'], df['Total Burnt Tokens'],
                 label='Total Burnt Tokens', color='green')
        plt.title(f'Circulating Supply and Total Burnt Tokens Over {
                  years} Years')
        plt.xlabel('Month')
        plt.ylabel('Tokens')
        plt.grid(True)
        plt.legend()

        # Subplot 3: Market Sentiment Index (MSI)
        plt.subplot(6, 1, 3)
        plt.plot(df['Month'], df['Market Sentiment Index'],
                 label='Market Sentiment Index', color='purple')
        plt.title(f'Market Sentiment Index Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('MSI')
        plt.grid(True)
        plt.legend()

        # Subplot 4: Missions Conducted
        plt.subplot(6, 1, 4)
        plt.plot(df['Month'], df['Missions'],
                 label='Missions Conducted', color='red')
        plt.title(f'Missions Conducted Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Number of Missions')
        plt.grid(True)
        plt.legend()

        # Subplot 5: DAO Treasury
        plt.subplot(6, 1, 5)
        plt.plot(df['Month'], df['DAO Treasury'],
                 label='DAO Treasury', color='cyan')
        plt.title(f'DAO Treasury Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Tokens')
        plt.grid(True)
        plt.legend()

        # Subplot 6: Initiator Rewards Pool
        plt.subplot(6, 1, 6)
        plt.plot(df['Month'], df['Initiator Rewards Pool'],
                 label='Initiator Rewards Pool', color='brown')
        plt.title(f'Initiator Rewards Pool Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Tokens')
        plt.grid(True)
        plt.legend()

        # Adjust layout
        plt.tight_layout()

        # Save plot
        plot_filename = f'results/simulation_{years}yrs.png'
        plt.savefig(plot_filename)
        plt.close()

        # Interpretation of Results
        print(f"\nSimulation Results for {years} Years:")
        print(f"Final Token Price: ${df['Token Price'].iloc[-1]:.2f}")
        print(f"Final Circulating Supply: {
              df['Circulating Supply'].iloc[-1]:,.0f} tokens")
        print(f"Total Burnt Tokens: {
              df['Total Burnt Tokens'].iloc[-1]:,.0f} tokens")
        print(f"Final DAO Treasury: {df['DAO Treasury'].iloc[-1]:,.0f} tokens")
        print(f"Final Initiator Rewards Pool: {
              df['Initiator Rewards Pool'].iloc[-1]:,.0f} tokens")
        print(f"Total Missions Conducted: {df['Missions'].sum():,.0f}")
        print(f"Total Net Token Demand: {
              df['Net Token Demand'].sum():,.0f} tokens")


if __name__ == '__main__':
    main()
