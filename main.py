import json
import os
import matplotlib.pyplot as plt
import pandas as pd
from simulation import simulate


def main():
    # Load configuration
    with open('config.json', 'r') as config_file:
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
        plt.plot(df['Month'], df['Token Price'], label='Token Price')
        plt.title(f'Token Price Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Token Price ($)')
        plt.grid(True)
        plt.legend()

        # Subplot 2: Circulating Supply
        plt.subplot(6, 1, 2)
        plt.plot(df['Month'], df['Circulating Supply'],
                 label='Circulating Supply', color='orange')
        plt.title(f'Circulating Supply Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Circulating Supply')
        plt.grid(True)
        plt.legend()

        # Subplot 3: Total Burnt Tokens
        plt.subplot(6, 1, 3)
        plt.plot(df['Month'], df['Total Burnt Tokens'],
                 label='Total Burnt Tokens', color='green')
        plt.title(f'Total Burnt Tokens Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Total Burnt Tokens')
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

        # Subplot 5: Net Token Demand
        plt.subplot(6, 1, 5)
        plt.plot(df['Month'], df['Net Token Demand'],
                 label='Net Token Demand', color='purple')
        plt.title(f'Net Token Demand Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Net Token Demand')
        plt.grid(True)
        plt.legend()

        # Subplot 6: Initiator Rewards Pool
        plt.subplot(6, 1, 6)
        plt.plot(df['Month'], df['Initiator Rewards Pool'],
                 label='Initiator Rewards Pool', color='brown')
        plt.title(f'Initiator Rewards Pool Over {years} Years')
        plt.xlabel('Month')
        plt.ylabel('Initiator Rewards Pool')
        plt.grid(True)
        plt.legend()

        # Adjust layout
        plt.tight_layout()

        # Save plot
        plot_filename = f'results/simulation_{years}yrs.png'
        plt.savefig(plot_filename)
        plt.close()


if __name__ == '__main__':
    main()
