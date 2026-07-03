#!/usr/bin/env python3
"""Pull denser GDELT historical data for the backtest window.

Usage:
    python scripts/pull_gdelt_backtest.py \\
        --start 2026-01-15 --end 2026-06-30 \\
        --output data/samples/gdelt_hormuz_backtest_dense.json \\
        --sample-interval 4
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.signals.gdelt_client import pull_gdelt_historical  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("pull_gdelt_backtest")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull GDELT backtest data")
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=date(2026, 1, 15),
        help="Start date (ISO format, default: 2026-01-15)",
    )
    parser.add_argument(
        "--end",
        type=date.fromisoformat,
        default=date(2026, 6, 30),
        help="End date (ISO format, default: 2026-06-30)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "samples" / "gdelt_hormuz_backtest_dense.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data" / "samples" / ".gdelt_pull_manifest.json",
        help="Manifest file for resumable pulls",
    )
    parser.add_argument(
        "--sample-interval",
        type=int,
        default=4,
        help="Sample every Nth 15-min file (default: 4 = hourly)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("GDELT Backtest Dense Pull")
    logger.info("  Window: %s to %s", args.start, args.end)
    logger.info("  Output: %s", args.output)
    logger.info("  Sample interval: every %d files (1 per %d min)",
                args.sample_interval, args.sample_interval * 15)
    logger.info("=" * 60)

    stats = pull_gdelt_historical(
        start_date=args.start,
        end_date=args.end,
        output_path=args.output,
        manifest_path=args.manifest,
        sample_interval=args.sample_interval,
    )

    logger.info("=" * 60)
    logger.info("Pull Summary:")
    logger.info("  Files downloaded: %d", stats.files_downloaded)
    logger.info("  Files skipped (resume): %d", stats.files_skipped)
    logger.info("  Files failed: %d", stats.files_failed)
    logger.info("  Rows parsed: %d", stats.rows_parsed)
    logger.info("  Rows accepted: %d", stats.rows_accepted)
    logger.info("  Rows rejected: %d", stats.rows_rejected)
    logger.info("  Accept rate: %.1f%%",
                100.0 * stats.rows_accepted / max(stats.rows_parsed, 1))
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
