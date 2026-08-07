"""
backfill_dates.py - one-time demo helper.

The seed import stamps every historical sale with a single "now" timestamp,
so the dashboard "Sales - last 30 days" chart collapses into a one-day spike.
This utility deterministically re-spreads the dates of existing sales (and
their paired stock transactions), purchases and expenses over the last ~30
days so the charts look meaningful.

It ONLY rewrites created_at / date fields - product names, sale snapshots and
all totals are preserved. Deterministic (fixed seed) so re-running is stable.

Run:  python backfill_dates.py
"""

import random
import sqlite3
from datetime import date, datetime, time as dtime, timedelta

DB = "data/shop.db"


def spread(index, total, span_days=30):
    """Deterministic timestamp spread over the last `span_days` days."""
    rng = random.Random(1991 + index)
    offset = round((index / max(total - 1, 1)) * (span_days - 1)) if total > 1 else 0
    offset = min(offset + rng.randint(0, 1), span_days - 1)
    day = date.today() - timedelta(days=offset)
    t = dtime(rng.randint(9, 21), rng.randint(0, 59), rng.randint(0, 59))
    return datetime.combine(day, t)


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sales = cur.execute("select id from sales order by id").fetchall()
    sale_txns = cur.execute(
        "select id from stock_transactions where type='sale' order by id"
    ).fetchall()
    buys = cur.execute(
        "select id from stock_transactions where type in ('purchase','restock') order by id"
    ).fetchall()
    exps = cur.execute("select id from expenses order by id").fetchall()

    print(f"sales={len(sales)} sale_txns={len(sale_txns)} "
          f"purchases={len(buys)} expenses={len(exps)}")

    ns = len(sales)
    # Pair each sale with its stock transaction by id order (both are created
    # back-to-back, so their id ordering matches).
    for i in range(max(len(sales), len(sale_txns))):
        ts = spread(i, ns).isoformat(sep=" ")
        if i < len(sales):
            cur.execute("update sales set created_at=? where id=?",
                        (ts, sales[i]["id"]))
        if i < len(sale_txns):
            cur.execute("update stock_transactions set created_at=? where id=?",
                        (ts, sale_txns[i]["id"]))

    for i, r in enumerate(buys):
        cur.execute("update stock_transactions set created_at=? where id=?",
                    (spread(i, len(buys)).isoformat(sep=" "), r["id"]))

    for i, r in enumerate(exps):
        ts = spread(i, len(exps))
        cur.execute("update expenses set date=?, created_at=? where id=?",
                    (ts.date().isoformat(), ts.isoformat(sep=" "), r["id"]))

    conn.commit()

    print("\nSales per day (now spread):")
    for r in conn.execute("select date(created_at) d, count(*) n from sales group by d order by d"):
        print("   ", r["d"], "->", r["n"])
    print("min/max:", conn.execute("select min(created_at), max(created_at) from sales").fetchone())
    conn.close()


if __name__ == "__main__":
    main()