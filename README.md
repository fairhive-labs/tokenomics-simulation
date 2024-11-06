
# PoLN Tokenomics Simulation

This repository contains a simulation tool for modeling the tokenomics of the PoLN protocol. The simulation helps visualize and understand how different parameters affect the token economy over time.

## Disclaimer

This simulation tool is a work in progress. It is developed to provide insights into the PoLN tokenomics model, but it may contain errors or limitations. The results should be considered estimates and should not be used for critical or high-stakes decisions without further verification.

We appreciate your understanding and patience as we enhance its functionality and accuracy. If you encounter any issues or have suggestions for improvement, please contact us. Your feedback is valuable and will help us improve the tool further. Thank you for using this simulation tool.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Simulation Parameters](#simulation-parameters)
- [Adjustable Parameters](#adjustable-parameters)
- [Analyzing Results](#analyzing-results)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Installation

### Clone the Repository

```bash
git clone https://github.com/fairhive-labs/tokenomics-simulation.git
```

### Navigate to the Directory

```bash
cd tokenomics-simulation
```

### Create a Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python -m venv venv
```

### Activate the Virtual Environment

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

### Install Required Packages

Install the necessary Python packages inside the virtual environment.

```bash
pip install numpy pandas matplotlib
```

## Usage

### Configure Simulation Parameters

Edit the `config.json` file to adjust the simulation parameters.  
See [Simulation Parameters](#simulation-parameters) for details.

### Run the Simulation

```bash
python main.py
```

### View Results

The simulation outputs CSV files and plots in the `results` directory. Analyze the results to understand the tokenomics over time.

## Simulation Parameters

The simulation is controlled by parameters defined in the `config.json` file. Adjusting these parameters allows you to model different scenarios and observe how they affect the token economy.

## Adjustable Parameters

Below is a list of key parameters you can adjust:

- **Total Supply (`total_supply`)**: The total number of tokens in existence.
- **Initial Token Price (`initial_price`)**: The starting price of the token in USD.
- **Project Cost (`project_cost`)**: The average cost of a project or mission in USD.
- **Protocol Fee Rate (`protocol_fee_rate`)**: The percentage fee charged by the protocol per mission.
- **Staking Rate (`staking_rate`)**: The proportion of the protocol fee that must be staked in $POLN.
- **Mission Success Rate (`mission_success_rate`)**: The probability of a mission being successful.
- **Price Elasticity Coefficient (`pec`)**: Determines how sensitive the token price is to changes in net token demand relative to the circulating supply.

### Market Sentiment Indices

- **Bull Market (`msi_bull`)**
- **Bear Market (`msi_bear`)**
- **Normal Market (`msi_normal`)**

### The Effects of Roadmap Execution

- **Roadmap Effect (`roadmap_effect`)**: Factor modifying the MSI.
- **Roadmap Phase(`roadmap_cycle`)**: Major segments of the project in months.

### Market Event Probabilities

- **Bull Market Probability (`bull_market_probability`)**
- **Bear Market Probability (`bear_market_probability`)**
- **Market Event Duration (`market_event_duration`)**: Duration of market events in months.
- **Random Fluctuation (`random_fluctuation`)**: The magnitude of random fluctuations applied to the number of missions.

### Mission Growth Parameters

- **Carrying Capacity (`carrying_capacity`)**: Maximum number of missions achievable in the growth model.
- **Growth Rate (`growth_rate`)**: Controls the speed at which mission numbers grow over time.
- **Inflection Point (`inflection_point`)**: The month when mission growth shifts from accelerating to decelerating.
- **Seasonality (`seasonality`)**: Adjustments based on the month.

### Simulation Duration Parameters

- **Simulation Years (`simulation_years`)**: The durations in years for running the simulation.
- **Months per Year (`months_per_year`)**: The number of months in a year, typically 12.

### Token Distribution Parameters

- **Token Distribution (`token_distribution`)**: Allocation of total supply among groups.

### Builders' Lockup and Vesting

- **Builders' Lockup Period (`builders_lockup_period`)**
- **Builders' Vesting Period (`builders_vesting_period`)**
- **Builders' Selling Percentage (`builders_selling_percentage`)**: Fraction of vested tokens sold monthly.
- **Testnet Distribution Period (`testnet_distribution_period`)**
- **Initiator Selling Percentage (`initiator_selling_percentage`)**

### DAO Parameters

- **DAO Annual Consumption Rate (`dao_annual_consumption_rate`)**
- **DAO Consumption Start Month (`dao_consumption_start_month`)**: When DAO starts consuming its treasury.
- **Fellowship Selling Percentage (`fellowship_selling_percentage`)**

### Private Sales

Private sales details, including tokens sold, price, and vesting period.
Example:

```json
[
    {"tokens_sold": 20000000, "price": 0.10, "vesting_period": 12},
    {"tokens_sold": 15000000, "price": 0.20, "vesting_period": 6},
    {"tokens_sold": 15000000, "price": 1.00, "vesting_period": 0}
]
```

### Initiator Rewards

- **Initial Rewards per Mission**: The initial rewards given for missions.
Example:

```json
{"daily": 8.00, "weekly": 64.00, "monthly": 512.00, "quarterly": 4096.00, "half_yearly": 32768.00}
```

- **Minimum Reward per Mission (`minimum_reward_per_mission`)**: Prevents rewards from becoming negligibly small.

## Analyzing Results

After running the simulation:

- **CSV Outputs**: Found in the `results` directory, containing detailed monthly data.
- **Plots**: Visual representations of key metrics over time.

Key Metrics:

- Token Price
- Circulating Supply
- Total Supply
- Net Token Demand
- Tokens Burnt
- Missions Conducted
- Initiator Rewards Pool
- DAO Treasury
- Tokens Staked
- Tokens Fee Distributed

## Contributing

We welcome contributions to enhance the simulation tool. Please follow these steps:

1. Fork the Repository
2. Create a Feature Branch

    ```bash
    git checkout -b feature/your-feature-name
    ```

3. Commit Your Changes

    ```bash
    git commit -m "Your detailed description of the changes."
    ```

4. Push to Your Branch

    ```bash
    git push origin feature/your-feature-name
    ```

5. Create a Pull Request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

If you have any questions or need assistance, please open an issue in the repository or contact us at <contact@poln.org>.
