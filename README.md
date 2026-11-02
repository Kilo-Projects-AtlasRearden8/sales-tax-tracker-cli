# Sales Tax Tracker CLI

A local-first Python command-line tool for small sellers to track sales tax
collected by state and period, with summary reports and CSV export.

Built for **Asdale Dynamics, LLC** (Indiana) — beginner-friendly, practical
tools for small businesses and authors. No API keys, no network, no accounts.
All data stays in a JSON file on your machine.

## What it does

- Record sales with date, state, and amount
- Compute sales tax collected automatically from state rates (or enter tax
  collected directly)
- Summarize tax collected by state and by period (month)
- Print grand totals
- Export all records to CSV for bookkeeping or filing

## Install

Python 3.8+ is required. No external dependencies.

```bash
git clone <this-repo>
cd sales-tax-tracker-cli
```

Run directly:

```bash
python3 sales_tax.py --help
```

## Usage

Record a sale (tax computed from the state's default rate):

```bash
python3 sales_tax.py add --date 2026-10-01 --state IN --amount 100.00
```

Enter tax collected directly:

```bash
python3 sales_tax.py add --date 2026-10-01 --state IN --amount 100.00 --tax 7.00
```

Override the tax rate for one sale:

```bash
python3 sales_tax.py add --date 2026-10-01 --state IN --amount 100.00 --rate 7.0
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

List default state rates:

```bash
python3 sales_tax.py rates
python3 sales_tax.py rates IN
```

Data is stored in `sales_tax_data.json` in the current folder. Use
`--data-file` to pick a different file.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Data file

`sales_tax_data.json` holds your records and rates. It is plain JSON — you can
back it up, edit it, or move it anytime. Nothing leaves your computer.

## Rates

Default state rates are approximate base state rates. Verify the current rates
for your states before filing; pass `--rate` to override per sale or edit the
rates block in the data file.

## License

MIT License. Copyright (c) 2026 Asdale Dynamics, LLC. See [LICENSE](LICENSE).

## Credit

Built by Kilo for Asdale Dynamics, LLC — Dylan Asdale, registered nurse turned
AI author and founder of Asdale Dynamics, LLC (Indiana, formed October 2026).
The LLC publishes beginner-friendly AI education, books and guides, and
practical small-business tools. Learn more at dylanasdale.github.io.
