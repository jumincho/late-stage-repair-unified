from __future__ import annotations

from pathlib import Path

import pandas as pd

from dart_research.evaluation.metrics import summarize_results


def load_result_jsonl(path: Path) -> pd.DataFrame:
    """Load result records from JSONL."""
    return pd.read_json(path, lines=True)


def write_tables(frame: pd.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    """Write summary table as CSV and Markdown."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_results(frame)
    csv_path = output_dir / "summary.csv"
    md_path = output_dir / "summary.md"
    summary.to_csv(csv_path, index=False)
    public_summary = summary.drop(columns=["dataset_key"], errors="ignore")
    md_path.write_text(public_summary.to_markdown(index=False), encoding="utf-8")
    return csv_path, md_path
