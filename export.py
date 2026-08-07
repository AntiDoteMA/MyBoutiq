"""
MyBoutiq - export.py

Builds backup files in the familiar legacy spreadsheet layout:
- Sheet "Feuille 1"  : old layout (one row per product + totals row),
                       reproducing the legacy column formulas:
                       Dépenses = prix_achat x quantite ; Ventes = prix_vente x vendus ;
                       Bénéfices = ventes - dépenses.
- Sheet "Ventes"     : full sales history incl. the discount (Remise) columns.
- Sheet "Dépenses"   : operating-expense ledger.

XLSX -> one workbook with the three sheets.
CSV  -> legacy single-sheet CSV (comma-separated, French decimal commas, quoted).
"""

import csv
import io
import os
from datetime import datetime

import pandas as pd

from models import Product, Sale, Expense, StockTransaction, db


def _fr(value):
    """Format a number the French way: 1234.5 -> '1 234,50'."""
    if value is None:
        value = 0.0
    text = f"{value:,.2f}"
    return text.replace(",", " ").replace(".", ",")


def _old_layout_rows():
    """Return (header, rows, totals) for the legacy 'Feuille 1' layout."""
    products = (
        Product.query.filter_by(is_deleted=False).order_by(Product.id).all()
    )
    header = [
        "Articles",
        "Prix achat unitaire",
        "Quantité",
        "Prix vente unitaire",
        "Articles vendus",
        "Articles restants",
        "Dépenses totales",
        "Prix ventes totales",
        "Bénéfices",
    ]

    rows = []
    total_bought = total_sold = total_stock = 0
    total_dep = total_sales = 0.0

    for p in products:
        sales = [s for s in p.sales if not s.refunded]
        bought = p.quantity_bought
        sold = sum(s.quantity for s in sales)
        stock = p.stock
        sales_value = round(sum(s.total for s in sales), 2)
        dep = round(p.purchase_price * bought, 2)
        benef = round(sales_value - dep, 2)

        total_bought += bought
        total_sold += sold
        total_stock += stock
        total_dep += dep
        total_sales += sales_value

        rows.append(
            [
                p.name,
                p.purchase_price,
                bought,
                p.sale_price,
                sold,
                stock,
                dep,
                sales_value,
                benef,
            ]
        )

    operating = round(sum(e.amount for e in Expense.query.all()), 2)
    grand_dep = round(total_dep + operating, 2)
    totals = [
        "Totaux",
        "",
        total_bought,
        "",
        total_sold,
        total_stock,
        grand_dep,
        round(total_sales, 2),
        round(total_sales - grand_dep, 2),
    ]
    return header, rows, totals


def _sales_rows():
    header = [
        "Date",
        "Produit",
        "Quantité",
        "Prix liste",
        "Prix facturé",
        "Remise / unité",
        "Remise %",
        "Total",
        "Bénéfice",
        "Remboursé",
    ]
    rows = []
    for s in Sale.query.order_by(Sale.created_at).all():
        rows.append(
            [
                s.created_at.strftime("%d/%m/%Y %H:%M"),
                s.product_name_snapshot,
                s.quantity,
                s.list_unit_price,
                s.charged_unit_price,
                s.discount_per_unit,
                s.discount_percent,
                s.total,
                s.profit,
                "Oui" if s.refunded else "Non",
            ]
        )
    return header, rows


def _expense_rows():
    header = ["Date", "Description", "Montant"]
    rows = [
        [e.date.strftime("%d/%m/%Y"), e.description, e.amount]
        for e in Expense.query.order_by(Expense.date).all()
    ]
    return header, rows


def _write_csv(path, header, rows):
    """Legacy comma-separated CSV with French decimal commas, quoted values."""
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for row in rows:
            writer.writerow(
                [_fr(v) if isinstance(v, float) else (v if v is not None else "") for v in row]
            )


# ---------------------------------------------------------------------------
# Public entry points (used by the /export routes)
# ---------------------------------------------------------------------------

def build_xlsx():
    """Return a bytes buffer with the full 3-sheet workbook."""
    header, rows, totals = _old_layout_rows()
    s_header, s_rows = _sales_rows()
    e_header, e_rows = _expense_rows()

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(rows + [totals], columns=header).to_excel(
            writer, sheet_name="Feuille 1", index=False
        )
        pd.DataFrame(s_rows, columns=s_header).to_excel(
            writer, sheet_name="Ventes", index=False
        )
        pd.DataFrame(e_rows, columns=e_header).to_excel(
            writer, sheet_name="Dépenses", index=False
        )
    buffer.seek(0)
    return buffer


def build_csv_featured():
    """Legacy single-sheet CSV (Feuille 1 layout with totals row)."""
    header, rows, totals = _old_layout_rows()
    path = _temp_path("export_feuille1")
    _write_csv(path, header, rows + [totals])
    return path


def build_csv_sales():
    header, rows = _sales_rows()
    path = _temp_path("export_ventes")
    _write_csv(path, header, rows)
    return path


def build_csv_expenses():
    header, rows = _expense_rows()
    path = _temp_path("export_depenses")
    _write_csv(path, header, rows)
    return path


def _temp_path(label):
    return os.path.join(
        os.environ.get("TEMP", os.path.dirname(os.path.abspath(__file__))),
        f"boutique_{label}_{datetime.now():%Y%m%d_%H%M%S}.csv",
    )
