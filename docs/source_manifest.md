# CollectWise AI — Source Manifest

## Data Source

All generated portfolio records are synthetic. No real customer information or external customer dataset is used.

## Generation Configuration

| Setting | Value |
|---|---|
| Random seed | 20261022 |
| Reference date | 2026-10-22 |
| Completed run size | 10,000 loans |
| Installment schedule | 12 monthly installments per loan |
| Generator | Python with Faker and random-number generation |
| Database | SQLite |

## Generation Modules

| Module | Responsibility |
|---|---|
| `data_generator.py` | Creates synthetic customers, accounts, loans, installments, and contact preferences |
| `payment_engine.py` | Simulates full and partial payments |
| `delinquency_engine.py` | Calculates DPD, arrears, snapshots, and collection cases |
| `contact_engine.py` | Generates contact attempts while applying contact restrictions |
| `promise_engine.py` | Generates and tracks payment promises |
| `anomaly_engine.py` | Injects labelled anomalies for validation |
| `validator.py` | Checks database integrity and business-rule consistency |
| `exporter.py` | Exports generated datasets |

## Anomaly Ground Truth

Five labelled anomalies are deliberately introduced after baseline data generation. They cover paid accounts in collections, out-of-window contact, incorrect installment allocation, promises exceeding arrears, and disputed debt treated as confirmed.

These are intentional validation scenarios, not naturally occurring source-data errors.

## Output Formats

- SQLite database
- CSV datasets
- JSON datasets
- SQL database dump
- CSV validation report