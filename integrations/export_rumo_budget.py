"""Export only selected monthly grocery budgets, without writing to the Rumo database."""
import argparse
import json
import os
import sqlite3
import tempfile
import time
import sys
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.strip().casefold()) if not unicodedata.combining(c))


def money(value):
    amount = Decimal(str(value or 0))
    if not amount.is_finite() or amount < 0:
        raise ValueError('Orçamento inválido no Rumo')
    return int((amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def export_budget(database, output, names=('Supermercado',)):
    selected = {normalized(n) for n in names}
    db = sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True, timeout=3)
    db.row_factory = sqlite3.Row
    months = {}
    try:
        # Read within one snapshot. Do not run Rumo migrations, refreshes or recomputations.
        db.execute('BEGIN')
        for row in db.execute('''SELECT m.year,m.month,e.name,e.category,e.planned,e.actual
                FROM month_expenses e JOIN months m ON m.id=e.month_id ORDER BY m.year,m.month,e.id'''):
            if normalized(row['name']) not in selected:
                continue
            key = f'{row["year"]:04d}-{row["month"]:02d}'
            entry = months.setdefault(key, dict(lines=[]))
            entry['lines'].append(dict(name=row['name'], category=row['category'],
                planned_cents=money(row['planned']), actual_cents=money(row['actual']) if row['actual'] is not None else None))
    finally:
        db.close()
    for entry in months.values():
        entry['amount_cents'] = sum(line['planned_cents'] for line in entry['lines'])
        actuals = [line['actual_cents'] for line in entry['lines']]
        entry['actual_cents'] = sum(actuals) if all(n is not None for n in actuals) else None
    data = dict(version=1, updated_at=datetime.now(timezone.utc).isoformat(), months=months)
    output = Path(output)
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=output.parent, prefix='.budget-', delete=False) as tmp:
            path = tmp.name
            json.dump(data, tmp, ensure_ascii=False)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(path, output)
    finally:
        if path and os.path.exists(path):
            os.unlink(path)
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--name', action='append', dest='names')
    parser.add_argument('--watch', type=int, default=0, help='Refresh interval in seconds (minimum 30)')
    args = parser.parse_args()
    while True:
        try:
            result = export_budget(args.database, args.output, args.names or ('Supermercado',))
            print(f'Orçamentos de supermercado atualizados: {len(result["months"])} meses', flush=True)
        except Exception:
            if not args.watch:
                raise
            print('Não foi possível atualizar o orçamento; último snapshot preservado.', file=sys.stderr, flush=True)
        if not args.watch:
            break
        time.sleep(max(30,args.watch))
