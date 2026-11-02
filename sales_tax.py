"""Sales tax tracker: record sales, compute tax by state and period, export CSV.

Local-first small-business tool. All data stays in a JSON file on your
machine. No API keys, no network, no accounts.

Credit: built for Asdale Dynamics, LLC (Indiana).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import date, datetime
from typing import Any

DEFAULT_DATA_FILE = "sales_tax_data.json"

# Default state sales tax rates (approximate base state rates, percent).
# Users should verify current rates for their states; pass --rate to override.
DEFAULT_RATES: dict[str, float] = {
    "AL": 4.00, "AK": 0.00, "AZ": 5.60, "AR": 6.50, "CA": 7.25,
    "CO": 2.90, "CT": 6.35, "DE": 0.00, "FL": 6.00, "GA": 4.00,
    "HI": 4.00, "ID": 6.00, "IL": 6.25, "IN": 7.00, "IA": 6.00,
    "KS": 6.50, "KY": 6.00, "LA": 4.45, "ME": 5.50, "MD": 6.00,
    "MA": 6.25, "MI": 6.00, "MN": 6.875, "MS": 7.00, "MO": 4.225,
    "MT": 0.00, "NE": 5.50, "NV": 6.85, "NH": 0.00, "NJ": 6.625,
    "NM": 5.125, "NY": 4.00, "NC": 4.75, "ND": 5.00, "OH": 5.75,
    "OK": 4.50, "OR": 0.00, "PA": 6.00, "RI": 7.00, "SC": 6.00,
    "SD": 4.50, "TN": 7.00, "TX": 6.25, "UT": 6.10, "VT": 6.00,
    "VA": 5.30, "WA": 6.50, "WV": 6.00, "WI": 5.00, "WY": 4.00,
    "DC": 6.00,
}


def period_for(date_str: str) -> str:
    """Return the YYYY-MM period for an ISO date string."""
    return date_str[:7]


def parse_date(value: str | None) -> str:
    """Validate and return an ISO date string (YYYY-MM-DD)."""
    if value is None:
        return date.today().isoformat()
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date '{value}'; expected YYYY-MM-DD"
        ) from exc
    return value


def parse_state(value: str) -> str:
    state = value.strip().upper()
    if len(state) != 2 or not state.isalpha():
        raise argparse.ArgumentTypeError(f"invalid state '{value}'; use a two-letter code")
    return state


def money(value: float) -> float:
    """Round to cents."""
    return round(float(value) + 1e-9, 2)


def tax_for_amount(amount: float, rate: float) -> float:
    """Compute sales tax collected for an amount at a given rate (percent)."""
    return money(amount * rate / 100.0)


class SalesTracker:
    """In-memory sales tax records backed by a local JSON file."""

    def __init__(self, data_file: str = DEFAULT_DATA_FILE, rates: dict[str, float] | None = None) -> None:
        self.data_file = data_file
        self.rates = dict(DEFAULT_RATES)
        if rates:
            self.rates.update({k.upper(): v for k, v in rates.items()})
        self.records: list[dict[str, Any]] = []
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        self.records = []
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as fh:
                contents = fh.read().strip()
            if not contents:
                data = {}
            else:
                data = json.loads(contents)
            if isinstance(data, dict):
                self.records = data.get("records", [])
                if data.get("rates"):
                    self.rates.update({k.upper(): float(v) for k, v in data["rates"].items()})
            elif isinstance(data, list):
                self.records = data
        self._loaded = True

    def save(self) -> None:
        with open(self.data_file, "w", encoding="utf-8") as fh:
            json.dump(
                {"records": self.records, "rates": self.rates},
                fh,
                indent=2,
            )

    def rate_for(self, state: str) -> float:
        return float(self.rates.get(state.upper(), 0.0))

    def add_sale(
        self,
        date_str: str,
        state: str,
        amount: float,
        tax_collected: float | None = None,
        rate: float | None = None,
    ) -> dict[str, Any]:
        self.load()
        state = state.upper()
        amount = money(amount)
        period = period_for(date_str)
        if tax_collected is None:
            used_rate = self.rate_for(state) if rate is None else float(rate)
            tax_collected = tax_for_amount(amount, used_rate)
        else:
            tax_collected = money(tax_collected)
        record = {
            "date": date_str,
            "state": state,
            "period": period,
            "amount": amount,
            "tax_collected": tax_collected,
        }
        self.records.append(record)
        self.save()
        return record

    def summary_by_state(self) -> list[dict[str, Any]]:
        self.load()
        totals: dict[str, dict[str, float]] = {}
        for rec in self.records:
            st = rec["state"]
            bucket = totals.setdefault(st, {"sales": 0.0, "tax": 0.0, "count": 0})
            bucket["sales"] = money(bucket["sales"] + rec["amount"])
            bucket["tax"] = money(bucket["tax"] + rec["tax_collected"])
            bucket["count"] += 1
        result = []
        for st in sorted(totals):
            b = totals[st]
            result.append(
                {
                    "state": st,
                    "sales": money(b["sales"]),
                    "tax_collected": money(b["tax"]),
                    "count": b["count"],
                    "rate": self.rate_for(st),
                }
            )
        return result

    def summary_by_period(self) -> list[dict[str, Any]]:
        self.load()
        totals: dict[str, dict[str, float]] = {}
        for rec in self.records:
            period = rec["period"]
            bucket = totals.setdefault(period, {"sales": 0.0, "tax": 0.0, "count": 0})
            bucket["sales"] = money(bucket["sales"] + rec["amount"])
            bucket["tax"] = money(bucket["tax"] + rec["tax_collected"])
            bucket["count"] += 1
        result = []
        for period in sorted(totals):
            b = totals[period]
            result.append(
                {
                    "period": period,
                    "sales": money(b["sales"]),
                    "tax_collected": money(b["tax"]),
                    "count": b["count"],
                }
            )
        return result

    def grand_totals(self) -> dict[str, float | int]:
        self.load()
        sales = money(sum(rec["amount"] for rec in self.records))
        tax = money(sum(rec["tax_collected"] for rec in self.records))
        return {"sales": sales, "tax_collected": tax, "count": len(self.records)}

    def export_csv(self, path: str) -> int:
        self.load()
        fields = ["date", "state", "period", "amount", "tax_collected"]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for rec in self.records:
                writer.writerow({k: rec.get(k, "") for k in fields})
        return len(self.records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales_tax",
        description="Track sales tax collected by state and period (local-first, no keys).",
    )
    parser.add_argument(
        "--data-file", default=DEFAULT_DATA_FILE, help="local JSON data file (default: sales_tax_data.json)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="record a sale")
    p_add.add_argument("--date", type=parse_date, default=None, help="sale date YYYY-MM-DD (default: today)")
    p_add.add_argument("--state", type=parse_state, required=True, help="two-letter state code")
    p_add.add_argument("--amount", type=float, required=True, help="sale amount in dollars")
    p_add.add_argument("--tax", type=float, default=None, help="tax collected (default: computed from state rate)")
    p_add.add_argument("--rate", type=float, default=None, help="override tax rate percent for this sale")

    sub.add_parser("summary", help="print summary by state and period")
    sub.add_parser("totals", help="print grand totals")

    p_exp = sub.add_parser("export", help="export records to CSV")
    p_exp.add_argument("--file", required=True, help="output CSV path")

    p_rate = sub.add_parser("rates", help="list default state tax rates")
    p_rate.add_argument("state", nargs="?", default=None, help="optional two-letter state code")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    tracker = SalesTracker(data_file=args.data_file)

    if args.command == "add":
        try:
            rec = tracker.add_sale(
                args.date, args.state, args.amount, tax_collected=args.tax, rate=args.rate
            )
        except (ValueError, TypeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(
            f"added {rec['date']} {rec['state']} ${rec['amount']:.2f} "
            f"tax ${rec['tax_collected']:.2f} (period {rec['period']})"
        )
        return 0

    if args.command == "summary":
        by_state = tracker.summary_by_state()
        by_period = tracker.summary_by_period()
        totals = tracker.grand_totals()
        print("Sales tax summary by state:")
        print(f"{'State':<7} {'Sales':>12} {'Tax':>12} {'Count':>7} {'Rate':>6}")
        for row in by_state:
            print(
                f"{row['state']:<7} {row['sales']:>12.2f} {row['tax_collected']:>12.2f} "
                f"{row['count']:>7} {row['rate']:>6.3f}"
            )
        print()
        print("Sales tax summary by period:")
        print(f"{'Period':<9} {'Sales':>12} {'Tax':>12} {'Count':>7}")
        for row in by_period:
            print(
                f"{row['period']:<9} {row['sales']:>12.2f} {row['tax_collected']:>12.2f} "
                f"{row['count']:>7}"
            )
        print()
        print(
            f"Grand totals: sales ${totals['sales']:.2f}, "
            f"tax collected ${totals['tax_collected']:.2f}, {totals['count']} sale(s)"
        )
        return 0

    if args.command == "totals":
        totals = tracker.grand_totals()
        print(
            f"sales ${totals['sales']:.2f}, tax collected ${totals['tax_collected']:.2f}, "
            f"{totals['count']} sale(s)"
        )
        return 0

    if args.command == "export":
        n = tracker.export_csv(args.file)
        print(f"exported {n} record(s) to {args.file}")
        return 0

    if args.command == "rates":
        if args.state:
            st = args.state.upper()
            print(f"{st}: {tracker.rate_for(st):.3f}%")
        else:
            for st in sorted(tracker.rates):
                print(f"{st}: {tracker.rates[st]:.3f}%")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
