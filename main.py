"""
main.py

Run the PoLN tokenomics simulation and emit its outputs.

Reads parameters from ``config.json``, runs the simulation for each configured
horizon, writes per-horizon CSV data and a 6-panel plot into ``results/``, and
prints a short summary for each run.

Usage:
    python main.py                       # defaults from config.json
    python main.py --years 5 --seed 7    # override horizons / seed
    python main.py --help                # all options
"""

import argparse
import json
import os
import sys

import matplotlib

# Use a non-interactive backend so plotting works headless (CI, servers). The
# backend must be selected before pyplot is imported, hence the deferred imports.
matplotlib.use("Agg")
# pylint: disable=wrong-import-position
import matplotlib.pyplot as plt  # noqa: E402
from simulation import _validate_config, simulate  # noqa: E402
# pylint: enable=wrong-import-position

DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_RESULTS_DIR = "results"
DEFAULT_YEARS = (3, 5, 10)

# Subplot layout: (column, title, y-axis label, [(series, colour), ...]).
PLOT_PANELS = (
    ("Token Price", "Token Price ($)", [("Token Price", "blue")]),
    (
        "Circulating Supply and Total Burnt Tokens",
        "Tokens",
        [("Circulating Supply", "orange"), ("Total Burnt Tokens", "green")],
    ),
    ("Market Sentiment Index", "MSI", [("Market Sentiment Index", "purple")]),
    ("Missions Conducted", "Number of Missions", [("Missions", "red")]),
    ("DAO Treasury", "Tokens", [("DAO Treasury", "cyan")]),
    ("Initiator Rewards Pool", "Tokens", [("Initiator Rewards Pool", "brown")]),
)


def load_config(path=DEFAULT_CONFIG_PATH):
    """Load and parse the JSON configuration file.

    Raises a :class:`SystemExit` with a helpful message if the file is missing
    or contains invalid JSON.
    """
    try:
        with open(path, "r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except FileNotFoundError as exc:
        raise SystemExit(f"Configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def plot_results(df, years, results_dir=DEFAULT_RESULTS_DIR):
    """Render the 6-panel figure for a run and save it as a PNG.

    Returns the path of the written file.
    """
    plt.figure(figsize=(20, 10))  # Landscape orientation.
    for index, (title, ylabel, series) in enumerate(PLOT_PANELS, start=1):
        plt.subplot(2, 3, index)
        for column, colour in series:
            plt.plot(df["Month"], df[column], label=column, color=colour)
        plt.title(f"{title} Over {years} Years" if index in (1, 3) else title)
        plt.xlabel("Month")
        plt.ylabel(ylabel)
        plt.grid(True)
        plt.legend()

    plt.tight_layout()
    plot_filename = os.path.join(results_dir, f"simulation_{years}yrs.png")
    plt.savefig(plot_filename)
    plt.close()
    return plot_filename


def summarize(df, years):
    """Return a summary mapping of final-month metrics for a run."""
    last = df.iloc[-1]
    return {
        "years": years,
        "final_price": last["Token Price"],
        "final_total_supply": last["Total Supply"],
        "final_circulating_supply": last["Circulating Supply"],
        "total_burnt": last["Total Burnt Tokens"],
        "dao_balance": last["DAO Treasury"],
    }


def _print_summary(summary):
    """Print a human-readable summary block for a single run."""
    years = summary["years"]
    title = f"Interpretation after {years} years"
    if sys.stdout.isatty():
        title = f"\033[7;32m{title}\033[0m"
    print(f"\n--- {title} ---")
    print(f"Final Token Price: ${summary['final_price']:.2f}")
    print(f"Final Total Supply: {summary['final_total_supply']:,.2f} tokens")
    print(f"Final Circulating Supply: {summary['final_circulating_supply']:,.2f} tokens")
    print(f"Total Tokens Burnt: {summary['total_burnt']:,.2f} tokens")
    print(f"DAO Treasury Balance: {summary['dao_balance']:,.2f} tokens")
    print("----------------------------------------")


def run_all(config, results_dir=DEFAULT_RESULTS_DIR, plot=True):
    """Run every configured horizon, writing CSV (+ plots), and return summaries."""
    os.makedirs(results_dir, exist_ok=True)
    summaries = []
    months_per_year = config.get("months_per_year", 12)
    for years in config.get("simulation_years", DEFAULT_YEARS):
        df = simulate(years * months_per_year, config)

        csv_filename = os.path.join(results_dir, f"simulation_data_{years}yrs.csv")
        df.to_csv(csv_filename, index=False)
        if plot:
            plot_results(df, years, results_dir)

        if df.empty:
            continue
        summaries.append(summarize(df, years))
    return summaries


def parse_args(argv=None):
    """Parse command-line options (all optional; defaults come from the config)."""
    parser = argparse.ArgumentParser(
        description="Run the $POLN tokenomics simulation.",
    )
    parser.add_argument(
        "-c", "--config", default=DEFAULT_CONFIG_PATH,
        help=f"path to the JSON config file (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "-y", "--years", type=int, nargs="+", metavar="N",
        help="horizon(s) to simulate in years, e.g. --years 3 5 10 "
             "(default: simulation_years from the config)",
    )
    parser.add_argument(
        "-s", "--seed", type=int,
        help="random seed for a reproducible run (default: random_seed from the config)",
    )
    parser.add_argument(
        "-o", "--output", default=DEFAULT_RESULTS_DIR,
        help=f"directory for CSV and PNG results (default: {DEFAULT_RESULTS_DIR})",
    )
    parser.add_argument(
        "--no-plot", action="store_true",
        help="skip PNG charts (write CSV data and print the summary only)",
    )
    args = parser.parse_args(argv)
    if args.years and any(years < 1 for years in args.years):
        parser.error("--years values must be positive integers")
    return args


def main(argv=None):
    """Execute the tokenomics simulation and handle output."""
    args = parse_args(argv)
    config = load_config(args.config)
    if args.years:
        config["simulation_years"] = args.years
    if args.seed is not None:
        config["random_seed"] = args.seed
    try:
        _validate_config(config)
    except ValueError as exc:
        raise SystemExit(f"Invalid configuration in {args.config}: {exc}") from exc

    for summary in run_all(config, args.output, plot=not args.no_plot):
        _print_summary(summary)
    print(f"\nResults written to {os.path.abspath(args.output)}")


if __name__ == "__main__":
    sys.exit(main())
