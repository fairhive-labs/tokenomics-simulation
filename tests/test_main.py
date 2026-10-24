"""Unit tests for the CLI / orchestration layer (main.py)."""

import json
import shutil
from pathlib import Path

import pytest

import main
from conftest import CONFIG_PATH


# --------------------------------------------------------------------------- #
# load_config
# --------------------------------------------------------------------------- #
def test_load_config_success(tmp_path):
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps({"total_supply": 1}), encoding="utf-8")
    assert main.load_config(str(path)) == {"total_supply": 1}


def test_load_config_missing_file(tmp_path):
    missing = tmp_path / "nope.json"
    with pytest.raises(SystemExit, match="not found"):
        main.load_config(str(missing))


def test_load_config_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(SystemExit, match="Invalid JSON"):
        main.load_config(str(path))


# --------------------------------------------------------------------------- #
# summarize / _print_summary
# --------------------------------------------------------------------------- #
def test_summarize_reports_final_row(base_config):
    df = main.simulate(12, base_config)
    summary = main.summarize(df, years=1)
    last = df.iloc[-1]
    assert summary["years"] == 1
    assert summary["final_price"] == last["Token Price"]
    assert summary["final_circulating_supply"] == last["Circulating Supply"]
    assert summary["dao_balance"] == last["DAO Treasury"]


def test_print_summary_outputs_values(capsys):
    summary = {
        "years": 2,
        "final_price": 3.5,
        "final_total_supply": 200_000_000,
        "final_circulating_supply": 1_000_000,
        "total_burnt": 42.0,
        "dao_balance": 10.0,
    }
    main._print_summary(summary)
    out = capsys.readouterr().out
    assert "after 2 years" in out
    assert "$3.50" in out


# --------------------------------------------------------------------------- #
# plot_results
# --------------------------------------------------------------------------- #
def test_plot_results_writes_png(base_config, tmp_path):
    df = main.simulate(12, base_config)
    out = main.plot_results(df, years=1, results_dir=str(tmp_path))
    assert Path(out).exists()
    assert Path(out).stat().st_size > 0


# --------------------------------------------------------------------------- #
# run_all
# --------------------------------------------------------------------------- #
def test_run_all_writes_outputs(make_config, tmp_path):
    config = make_config(simulation_years=[1])
    summaries = main.run_all(config, results_dir=str(tmp_path))
    assert len(summaries) == 1
    assert (tmp_path / "simulation_data_1yrs.csv").exists()
    assert (tmp_path / "simulation_1yrs.png").exists()


def test_run_all_skips_summary_for_empty_frame(make_config, tmp_path):
    config = make_config(simulation_years=[0])
    summaries = main.run_all(config, results_dir=str(tmp_path))
    assert summaries == []
    # A (header-only) CSV is still written for the zero-length horizon.
    assert (tmp_path / "simulation_data_0yrs.csv").exists()


# --------------------------------------------------------------------------- #
# main() smoke test
# --------------------------------------------------------------------------- #
def test_main_smoke(tmp_path, monkeypatch):
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config["simulation_years"] = [1]
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main.main([]) is None
    assert (tmp_path / "results" / "simulation_data_1yrs.csv").exists()


# --------------------------------------------------------------------------- #
# Command-line options
# --------------------------------------------------------------------------- #
def _write_config(tmp_path, **overrides):
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config.update(overrides)
    path = tmp_path / "custom.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_parse_args_defaults():
    args = main.parse_args([])
    assert args.config == main.DEFAULT_CONFIG_PATH
    assert args.output == main.DEFAULT_RESULTS_DIR
    assert args.years is None and args.seed is None and not args.no_plot


def test_parse_args_rejects_non_positive_years(capsys):
    with pytest.raises(SystemExit):
        main.parse_args(["--years", "0"])
    assert "positive" in capsys.readouterr().err


def test_main_cli_overrides(tmp_path, capsys):
    cfg = _write_config(tmp_path, simulation_years=[10])
    out_dir = tmp_path / "out"
    main.main(["-c", str(cfg), "-y", "1", "2", "-s", "7", "-o", str(out_dir), "--no-plot"])
    assert (out_dir / "simulation_data_1yrs.csv").exists()
    assert (out_dir / "simulation_data_2yrs.csv").exists()
    assert not (out_dir / "simulation_data_10yrs.csv").exists()
    assert not list(out_dir.glob("*.png"))
    out = capsys.readouterr().out
    assert "after 2 years" in out
    assert "Results written to" in out


def test_main_seed_is_reproducible(tmp_path):
    cfg = _write_config(tmp_path)
    first, second = tmp_path / "a", tmp_path / "b"
    for out_dir in (first, second):
        main.main(["-c", str(cfg), "-y", "1", "-s", "99", "-o", str(out_dir), "--no-plot"])
    name = "simulation_data_1yrs.csv"
    assert (first / name).read_text() == (second / name).read_text()


def test_main_invalid_config_is_friendly(tmp_path):
    cfg = _write_config(tmp_path, total_supply=0)
    with pytest.raises(SystemExit, match="Invalid configuration"):
        main.main(["-c", str(cfg), "-o", str(tmp_path / "out")])
