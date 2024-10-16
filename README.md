
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
- [Understanding the Parameters](#understanding-the-parameters)
- [Analyzing Results](#analyzing-results)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Installation

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

### Clone the Repository

```bash
git clone https://github.com/fairhive-labs/tokenomics-simulation.git
```

### Navigate to the Directory

```bash
cd tokenomics-simulation
```

### Configure Simulation Parameters

Edit the `config.json` file to adjust the simulation parameters.  
See [Simulation Parameters](#simulation-parameters) for details.

### Run the Simulation

```bash
python main.py
```

### View Results

The simulation outputs CSV files and plots in the `results` directory.  
Analyze the results to understand the tokenomics over time.

## Simulation Parameters

The simulation is controlled by parameters defined in the `config.json` file. Adjusting these parameters allows you to model different scenarios and observe how they affect the token economy.

## Adjustable Parameters

Below is a list of key parameters you can adjust:

- **Total Supply (`total_supply`)**: The total number of tokens in existence.
- **Initial Token Price (`initial_price`)**: The starting price of the token.
- **Project Cost (`project_cost`)**: The average cost of a project or mission in USD.
- **Protocol Fee Rate (`protocol_fee_rate`)**: The percentage fee charged by the protocol per mission.
- **Staking Rate (`staking_rate`)**: The proportion of the protocol fee that must be staked in $POLN.
- **Mission Success Rate (`mission_success_rate`)**: The probability of a mission being successful.
- **Price Elasticity Coefficient (`pec`)**: Determines the sensitivity of token price to net demand changes.

### Market Sentiment Indices

- **Bull Market (`msi_bull`)**
- **Bear Market (`msi_bear`)**
- **Normal Market (`msi_normal`)**

### Market Event Probabilities

- **Bull Market Probability (`bull_market_probability`)**
- **Bear Market Probability (`bear_market_probability`)**
- **Market Event Duration (`market_event_duration`)**: Duration of market events in months.

### Mission Growth Parameters

- **Carrying Capacity (`carrying_capacity`)**
- **Growth Rate (`growth_rate`)**
- **Inflection Point (`inflection_point`)**
- **Seasonality (`seasonality`)**

### Vesting and Lockup Periods

- **Builders' Lockup Period (`builders_lockup_period`)**
- **Builders' Vesting Period (`builders_vesting_period`)**
- **Testnet Distribution Period (`testnet_distribution_period`)**

## Understanding the Parameters

### Total Supply and Token Distribution

- **Total Supply**: The maximum number of tokens that will ever exist.
- **Token Distribution**: Allocation of total supply among different stakeholders.

### Market Sentiment Indices and Probabilities

- **Market Sentiment Indices**: Adjust the price change based on market condition.
- **Price Elasticity Coefficient (`pec`)**: A higher pec value makes the token price more sensitive to changes in net demand.

### Selling Percentages

- **Initiator Selling Percentage**: The fraction of rewards that initiators sell each month.

## Analyzing Results

After running the simulation:

- **CSV Outputs**: Located in the `results` directory, containing detailed monthly data.
- **Plots**: Graphical representations of key metrics over time.

Key Metrics to Observe:

- Token Price
- Circulating Supply
- Total Supply
- Net Token Demand
- Tokens Burnt
- Missions Conducted
- Initiator Rewards Pool

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
