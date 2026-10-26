# Migration count reconciliation: runnable example

This example was created for the public portfolio in October 2026 with AI assistance. It illustrates the reconciliation approach described in the [migration case study](../../projects/cloud-migration-validation/README.md). It is a new demonstration, not recovered employer source code or a production Jira connector. All input and output values are synthetic.

## Business question

Which resource categories need investigation after a migration? Matching totals are useful, but missing categories and differences need a review trail. Equal counts alone do not prove that the records migrated correctly.

## Run locally

Requires Python 3.9+ with its standard library only. Run from this directory:

```bash
python3 reconcile.py source.csv target.csv --output comparison.csv
python3 -m unittest -v
```

- [Python implementation](reconcile.py): validates CSV inputs and runs the SQL query.
- [SQL query](reconcile.sql): joins both snapshots, preserves missing values and classifies results.
- [Example output](comparison.csv): generated from the supplied synthetic fixtures.

## Interpret the sample

| Resource | Result | Next check |
| --- | --- | --- |
| issues | Target is two lower | Reconcile issue keys and migration exclusions |
| workflows | Target is two higher | Check pre-existing workflows and expected differences |
| custom_fields | Missing target category | Check extraction coverage before treating it as zero |
| dashboards | Missing source category | Check source coverage and pre-existing target resources |
| filters | Both zero | Keep a genuine zero distinct from a missing category |

These are possible investigations, not explanations established by the counts. Production validation also needs permissions, issue-level field checks, attachments, history and user acceptance tests. The script does not connect to external systems or alter source data.
