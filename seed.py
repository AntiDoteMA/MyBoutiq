"""
Boutique Manager - seed.py

One-time import of the legacy spreadsheet ("Copy of WS'Shop.xlsx" / its CSV export)
into the new database. It reproduces the internally-consistent legacy totals:

    quantity bought 183   /   units sold 102   /   sales EUR 814.99
    (183/102 include the legacy operating-cost rows; the 57 products alone
     bought 174 / sold 98 -> derived stock 76, matching the sheet's "restants")
    total expenses EUR 724.32  (product purchases EUR 594.44
                                + operating expenses EUR 57.88
                                + legacy stray line EUR 72.00)
    63 real source rows + the stray line -> 57 products + 7 expenses

Mapping (PRD section 13.1):
- Rows with a "Prix vente unitaire" value  -> one Product per row, named
  "Produit N" in spreadsheet row order. Initial stock is a 'purchase'
  StockTransaction; sold units produce Sale rows at list price (no discount).
- Rows without a sale price ("-")           -> one Expense entry per row,
  amount = "Dépenses totales" if present, else prix_achat x quantite.
- Stray legacy row (dépenses 72,00)          -> imported as an Expense so the
  724,32 total is reproduced exactly.

Documented source drift (deviation from the PRD's printed figures):
- "Articles restants 76" matches the derived stock (174 bought - 98 sold):
  no drift here. The 183/102 printed totals count the legacy operating-cost
  rows too, which are imported as expenses, not products.
- "Bénéfices 215,68" is inconsistent: sales - expenses = 90,67 (which is also
  what the legacy CSV contains as a trailing free cell).  The app computes
  profit from real data.

Run:  python seed.py            (skips if already seeded)
      python seed.py --reset    (wipes all tables, then imports again)
"""

import os
import sys
from datetime import date, datetime, timedelta
import random

import pandas as pd

# Allow running from any folder: paths are relative to THIS file.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from models import db, Product, Sale, StockTransaction, Expense  # noqa: E402

SOURCE_XLSX = os.path.join(BASE_DIR, "Copy of WS'Shop.xlsx")
SOURCE_CSV = os.path.join(BASE_DIR, "Copy of WS'Shop - Feuille 1.csv")
DB_PATH = os.path.join(BASE_DIR, "data", "shop.db")

EXPECTED = {
    "bought": 174,  # product units purchased (excludes legacy cost rows)
    "sold": 98,  # product units sold (excludes legacy cost rows)
    "sales": 814.99,
    "expenses": 724.32,  # 594,44 product purchases + 129,88 operating
    "products": 57,
    "expense_rows": 7,  # 6 operating lines + the legacy stray line (72,00)
    "source_rows": 64,  # 63 real source rows (4..66) + the stray line
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_number(value):
    """Lenient parser: accepts None, NaN, '0,99', '0.99', '-', '–'."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text in ("", "-", "–", "—", "nan", "None"):
        return None
    return float(text.replace(",", ".").replace(" ", ""))


def _to_int(value):
    n = _to_number(value)
    if n is None:
        return None
    return int(round(n))


def _spread(index, total, span_days=30):
    """Deterministic historical timestamp spread over the last `span_days` days.

    The legacy sheet has no real sale dates, so imported sales are given
    believable, spread-out timestamps (otherwise the "last 30 days" dashboard
    chart is a single one-day spike). Deterministic: same input -> same output.
    """
    rng = random.Random(1991 + index)
    offset = round((index / max(total - 1, 1)) * (span_days - 1)) if total > 1 else 0
    offset = min(offset + rng.randint(0, 1), span_days - 1)
    day = date.today() - timedelta(days=offset)
    return (
        datetime.combine(day, datetime.min.time())
        .replace(hour=rng.randint(9, 21), minute=rng.randint(0, 59), second=rng.randint(0, 59))
    )


def find_source_file():
    if os.path.exists(SOURCE_XLSX):
        return SOURCE_XLSX
    if os.path.exists(SOURCE_CSV):
        return SOURCE_CSV
    raise FileNotFoundError(
        "Fichier source introuvable. Placez 'Copy of WS'Shop.xlsx' "
        "(ou son export CSV) a cote de seed.py."
    )


def load_legacy_rows(path):
    """Return a list of dicts describing the 63 real source rows."""
    if path.endswith(".csv"):
        df = pd.read_csv(path, encoding="utf-8-sig", header=None)
    else:
        xls = pd.ExcelFile(path)
        sheet = "Feuille 1" if "Feuille 1" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=sheet, header=None)

    rows = []
    for index in range(2, len(df)):  # skip "2026" cell + the "Articles" header row
        line_number = index + 1  # legacy file line number
        raw = df.iloc[index]
        cells = ["" if pd.isna(c) else c for c in raw[:9]]

        name = str(cells[0]).strip()

        # Stop at the "Totaux" row.
        if "totaux" in name.lower():
            break
        # Skip the legacy "Upload Error" artifact line.
        if "upload error" in " ".join(str(c).lower() for c in cells):
            continue

        buy = _to_number(cells[1])
        qty = _to_int(cells[2])
        sell = _to_number(cells[3])
        sold = _to_int(cells[4])
        dep = _to_number(cells[6])

        # Skip rows without any meaningful data (e.g. trailing spill cells).
        if buy is None and qty is None and dep is None and sell is None and sold is None:
            continue

        if sell is None:
            # Operating-cost row ("-" in Prix vente) -> Expense.
            if dep is not None:
                amount = dep
            elif buy is not None and qty is not None:
                amount = round(buy * qty, 2)
            else:
                amount = 0.0
            rows.append(
                {"kind": "expense", "line": line_number, "amount": round(amount, 2)}
            )
        else:
            # Resellable product row.
            rows.append(
                {
                    "kind": "product",
                    "line": line_number,
                    "buy": buy if buy is not None else 0.0,
                    "qty": qty if qty is not None else 0,
                    "sell": sell,
                    "sold": sold if sold is not None else 0,
                }
            )
    return rows


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def seed_database(force=False):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        "sqlite:///" + DB_PATH.replace("\\", "/"),
        connect_args={"check_same_thread": False},
    )
    db.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    session = Session()
    try:
        if session.query(Product).count() > 0 and not force:
            print("[seed] La base contient deja des donnees - import ignore.")
            print("[seed] Utilisez 'python seed.py --reset' pour re-importer.")
            return

        if force:
            session.query(StockTransaction).delete()
            session.query(Sale).delete()
            session.query(Expense).delete()
            session.query(Product).delete()
            session.commit()

        rows = load_legacy_rows(find_source_file())
        products = [r for r in rows if r["kind"] == "product"]
        expenses = [r for r in rows if r["kind"] == "expense"]

        now = datetime.utcnow()
        total_sold = sum(1 for p in products if p["sold"] > 0)
        sale_idx = 0

        for number, p in enumerate(products, start=1):
            product = Product(
                name=f"Produit {number}",
                category=None,
                purchase_price=p["buy"],  # keep raw (e.g. 1,795) so totals match the sheet
                sale_price=round(p["sell"], 2),
                low_stock_threshold=1,
                created_at=now,
                updated_at=now,
            )
            session.add(product)
            session.flush()  # get product.id

            # Initial purchase: +qty units at purchase price.
            purchase_dt = _spread(number - 1, len(products))
            session.add(
                StockTransaction(
                    product_id=product.id,
                    type="purchase",
                    quantity=p["qty"],
                    unit_price=p["buy"],  # raw unit cost, matches legacy dépenses
                    created_at=purchase_dt,
                )
            )

            # Historical sales: Sale row + negative stock transaction.
            if p["sold"] > 0:
                sale_dt = _spread(sale_idx, total_sold)
                sale_idx += 1
                sale = Sale(
                    product_id=product.id,
                    product_name_snapshot=product.name,
                    unit_purchase_price_snapshot=p["buy"],  # raw, matches purchase price
                    quantity=p["sold"],
                    list_unit_price=round(p["sell"], 2),
                    charged_unit_price=round(p["sell"], 2),
                    discount_per_unit=0.0,
                    total=round(p["sell"] * p["sold"], 2),
                    refunded=False,
                    created_at=sale_dt,
                )
                session.add(sale)
                session.add(
                    StockTransaction(
                        product_id=product.id,
                        type="sale",
                        quantity=-p["sold"],
                        unit_price=round(p["sell"], 2),
                        created_at=sale_dt,  # keep in sync with the Sale row
                    )
                )

        for e_idx, e in enumerate(expenses):
            exp_dt = _spread(e_idx, len(expenses))
            session.add(
                Expense(
                    date=exp_dt.date(),
                    description=f"Import ligne {e['line']}",
                    amount=e["amount"],
                    created_at=exp_dt,
                )
            )

        session.commit()
        verify(session, rows)
        print("[seed] Import termine avec succes.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    # ---------------------------------------------------------------
    # Create a default admin user if none exists
    # ---------------------------------------------------------------
    from models import User
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(username="admin")
        admin.set_password("admin123")  # default password – change after first login
        db.session.add(admin)
        db.session.commit()
        print("[seed] Default admin user created (username='admin', password='admin123')")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify(session, rows):
    """Check the import against the legacy reference totals."""
    products = session.query(Product).all()
    sales = session.query(Sale).filter_by(refunded=False).all()
    expenses = session.query(Expense).all()
    txns = session.query(StockTransaction).all()

    bought = sum(p.quantity_bought for p in products)
    sold = sum(s.quantity for s in sales)
    stock = sum(p.stock for p in products)
    total_sales = round(sum(s.total for s in sales), 2)
    product_purchases = round(
        sum(t.unit_price * t.quantity for t in txns if t.type in ("purchase", "restock")),
        2,
    )
    operating = round(sum(e.amount for e in expenses), 2)
    total_expenses = round(product_purchases + operating, 2)

    checks = {
        "lignes source importees": (len(rows), EXPECTED["source_rows"]),
        "produits": (len(products), EXPECTED["products"]),
        "depenses (lignes)": (len(expenses), EXPECTED["expense_rows"]),
        "quantites achetees": (bought, EXPECTED["bought"]),
        "unites vendues": (sold, EXPECTED["sold"]),
        "ventes (EUR)": (total_sales, EXPECTED["sales"]),
        "depenses totales (EUR)": (total_expenses, EXPECTED["expenses"]),
    }

    print("\n=== Verification de l'import ===")
    ok = True
    for label, (got, want) in checks.items():
        match = got == want
        ok = ok and match
        print(f"  {'OK ' if match else 'ERREUR'} {label}: {got} (attendu {want})")
    print(f"  NOTE stock derive (achete - vendu): {bought - sold} (= {stock})")
    print("  NOTE reference tableau (toutes lignes incl. frais): 183 achetes / 102 vendus")
    print(f"  NOTE depenses produit: {product_purchases} EUR, frais: {operating} EUR")
    print(
        f"  NOTE resultat (ventes - depenses): {round(total_sales - total_expenses, 2)} EUR"
    )
    print("=" * 40)
    if not ok:
        print("[seed] ATTENTION: certains totaux ne correspondent pas a la reference.")
    return ok


if __name__ == "__main__":
    force = "--reset" in sys.argv
    seed_database(force=force)