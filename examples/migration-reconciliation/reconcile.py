"""Reconcile resource-count snapshots. Uses synthetic fixtures, never live Jira data."""
import argparse
import csv
import sqlite3
from pathlib import Path


def read_snapshot(path):
    rows = []
    seen = set()
    with Path(path).open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['resource', 'count']:
            raise ValueError(f'{path}: expected resource,count columns')
        for row in reader:
            resource = (row['resource'] or '').strip()
            count = row['count'] or ''
            if not resource or resource in seen or not count.isascii() or not count.isdecimal():
                raise ValueError(f'{path}: blank/duplicate resource or invalid nonnegative integer')
            value = int(count)
            if value > 9223372036854775807:
                raise ValueError(f'{path}: count exceeds supported integer range')
            seen.add(resource)
            rows.append((resource, value))
    if not rows:
        raise ValueError(f'{path}: snapshot is empty')
    return rows


def reconcile(source, target):
    with sqlite3.connect(':memory:') as db:
        for table, rows in [('source', source), ('target', target)]:
            db.execute(f'CREATE TABLE {table} (resource TEXT PRIMARY KEY, count INTEGER NOT NULL)')
            db.executemany(f'INSERT INTO {table} VALUES (?, ?)', rows)
        query = Path(__file__).with_name('reconcile.sql').read_text(encoding='utf-8')
        cursor = db.execute(query)
        columns = [item[0] for item in cursor.description]
        return columns, cursor.fetchall()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('target', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        columns, rows = reconcile(read_snapshot(args.source), read_snapshot(args.target))
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(2, f'Input/reconciliation error: {exc}\n')
    with args.output.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)
    print(f'Wrote {len(rows)} resource comparisons to {args.output}')


if __name__ == '__main__':
    main()
