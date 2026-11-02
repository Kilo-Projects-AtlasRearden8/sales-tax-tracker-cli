"""Unit tests for the sales tax tracker math and logic."""

import csv
import json
import os
import tempfile
import unittest

from sales_tax import (
    SalesTracker,
    money,
    parse_date,
    period_for,
    tax_for_amount,
)


class TestMoneyRounding(unittest.TestCase):
    def test_rounds_to_cents(self):
        self.assertEqual(money(10.005), 10.01)
        self.assertEqual(money(10.004), 10.0)
        self.assertEqual(money(0.1 + 0.2), 0.3)

    def test_tax_computation(self):
        self.assertEqual(tax_for_amount(100.00, 7.0), 7.0)
        self.assertEqual(tax_for_amount(10.00, 7.0), 0.7)
        self.assertEqual(tax_for_amount(33.33, 6.25), 2.08)


class TestDateHelpers(unittest.TestCase):
    def test_period_for(self):
        self.assertEqual(period_for("2026-10-15"), "2026-10")

    def test_parse_date_defaults_to_today(self):
        import datetime

        self.assertEqual(parse_date(None), datetime.date.today().isoformat())

    def test_parse_date_valid(self):
        self.assertEqual(parse_date("2026-01-02"), "2026-01-02")

    def test_parse_date_invalid(self):
        with self.assertRaises(Exception):
            parse_date("not-a-date")


class TestTracker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.tracker = SalesTracker(data_file=self.tmp.name, rates={"IN": 7.0, "CA": 7.25})

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_add_sale_computes_tax(self):
        rec = self.tracker.add_sale("2026-10-01", "IN", 100.00)
        self.assertEqual(rec["state"], "IN")
        self.assertEqual(rec["amount"], 100.0)
        self.assertEqual(rec["tax_collected"], 7.0)
        self.assertEqual(rec["period"], "2026-10")

    def test_add_sale_explicit_tax(self):
        rec = self.tracker.add_sale("2026-10-01", "IN", 100.00, tax_collected=5.00)
        self.assertEqual(rec["tax_collected"], 5.0)

    def test_add_sale_override_rate(self):
        rec = self.tracker.add_sale("2026-10-01", "IN", 100.00, rate=10.0)
        self.assertEqual(rec["tax_collected"], 10.0)

    def test_persistence_roundtrip(self):
        self.tracker.add_sale("2026-10-01", "IN", 100.00)
        self.tracker.add_sale("2026-10-02", "CA", 50.00)
        other = SalesTracker(data_file=self.tmp.name)
        other.load()
        self.assertEqual(len(other.records), 2)

    def test_summary_by_state(self):
        self.tracker.add_sale("2026-10-01", "IN", 100.00)
        self.tracker.add_sale("2026-10-02", "IN", 200.00)
        self.tracker.add_sale("2026-10-03", "CA", 50.00)
        states = {row["state"]: row for row in self.tracker.summary_by_state()}
        self.assertEqual(states["IN"]["sales"], 300.0)
        self.assertEqual(states["IN"]["tax_collected"], 21.0)
        self.assertEqual(states["IN"]["count"], 2)
        self.assertEqual(states["CA"]["sales"], 50.0)
        self.assertEqual(states["CA"]["tax_collected"], money(50 * 7.25 / 100.0))
        self.assertEqual(states["CA"]["count"], 1)

    def test_summary_by_period(self):
        self.tracker.add_sale("2026-09-15", "IN", 100.00)
        self.tracker.add_sale("2026-10-01", "IN", 200.00)
        periods = {row["period"]: row for row in self.tracker.summary_by_period()}
        self.assertEqual(periods["2026-09"]["sales"], 100.0)
        self.assertEqual(periods["2026-10"]["sales"], 200.0)
        self.assertEqual(periods["2026-10"]["count"], 1)

    def test_grand_totals(self):
        self.tracker.add_sale("2026-10-01", "IN", 100.00)
        self.tracker.add_sale("2026-10-02", "CA", 50.00)
        totals = self.tracker.grand_totals()
        self.assertEqual(totals["sales"], 150.0)
        self.assertEqual(totals["tax_collected"], money(7.0 + 3.625))
        self.assertEqual(totals["count"], 2)

    def test_export_csv(self):
        path = self.tmp.name + ".csv"
        self.tracker.add_sale("2026-10-01", "IN", 100.00)
        n = self.tracker.export_csv(path)
        self.assertEqual(n, 1)
        with open(path, "r", encoding="utf-8") as fh:
            reader = list(csv.DictReader(fh))
        self.assertEqual(len(reader), 1)
        self.assertEqual(reader[0]["state"], "IN")
        os.unlink(path)

    def test_unknown_state_defaults_zero_rate(self):
        rec = self.tracker.add_sale("2026-10-01", "ZZ", 100.00)
        self.assertEqual(rec["tax_collected"], 0.0)

    def test_data_file_json_structure(self):
        self.tracker.add_sale("2026-10-01", "IN", 100.00)
        with open(self.tmp.name, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertIn("records", data)
        self.assertIn("rates", data)
        self.assertEqual(len(data["records"]), 1)


if __name__ == "__main__":
    unittest.main()
