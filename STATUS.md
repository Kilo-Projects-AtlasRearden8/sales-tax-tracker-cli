# STATUS

Sales Tax Tracker CLI — Asdale Dynamics, LLC

## What was built

A local-first Python command-line tool for small sellers to track sales tax
collected by state and period, with summary reports and CSV export.

Files:
- `sales_tax.py` — CLI and tracker logic (records, tax math, state/period
  summaries, grand totals, CSV export, local JSON storage)
- `tests/test_sales_tax.py` — 16 unit tests covering money rounding, tax
  computation, date helpers, persistence, summaries, totals, and CSV export
- `README.md` — usage guide and credit to Asdale Dynamics, LLC
- `LICENSE` — MIT License, Copyright (c) 2026 Asdale Dynamics, LLC
- `.gitignore` — excludes cache files and local data/CSV exports

Key behaviors:
- Record a sale with `--date`, `--state`, `--amount`; tax is computed from
  the state's default rate (or supplied via `--tax`/`--rate`)
- `summary` prints tax collected by state and by period (YYYY-MM), plus
  grand totals
- `totals` prints grand totals only
- `export --file` writes all records to CSV
- `rates` lists default state tax rates
- All data stays in a local JSON file (`sales_tax_data.json` by default).
  No API keys, no network, no accounts, no personal data.

## How to run it

Requirements: Python 3.8+ (no external dependencies).

```bash
cd sales-tax-tracker-cli
python3 sales_tax.py --help
```

Record a sale:

```bash
python3 sales_tax.py add --date 2026-10-01 --state IN --amount 100.00
```

View summaries:

```bash
python3 sales_tax.py summary
python3 sales_tax.py totals
```

Export to CSV:

```bash
python3 sales_tax.py export --file sales_tax_records.csv
```

## Verification results

```
$ python3 -m unittest discover -s tests
..............
----------------------------------------------------------------------
Ran 16 tests in 0.008s

OK
```

All 16 tests pass. CLI smoke test (add x2, summary, totals, export) ran
successfully and produced correct output:
- IN sale $100.00 -> tax $7.00 (7.000% rate)
- CA sale $50.00 -> tax $3.63 (7.250% rate)
- Grand totals: sales $150.00, tax collected $10.63, 2 sale(s)
- CSV export wrote 2 records with correct headers and values

## Known gaps

- Default state rates are approximate base state rates; users should verify
  current rates for their states before filing (noted in README).
- No per-county or local-jurisdiction tax support; state-level rates only.
- No validation that tax entered manually matches the state rate (intentional:
  users may need to override for exemptions or special districts).
- No interactive prompts; all input via CLI flags.
- Data file is not encrypted; it is plain JSON on the local machine.

Built for Asdale Dynamics, LLC (Indiana). Local-first, no keys, no secrets.
