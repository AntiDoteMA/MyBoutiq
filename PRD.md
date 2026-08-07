# PRD — Boutique Manager (Local Shop Management Web App)

**Version:** 1.2 — 2026-08-07
**Status:** Ready for implementation
**Project root:** `c:\Users\Antidote\Desktop\Work-Ground\python Projects\Bilal`

## Purpose of this document
This PRD is the single source of truth for the project. An implementation agent should read it and produce a build plan. Decisions marked **[DECIDED]** are final and must not change without re-discussion. All items formerly marked **[OPEN]** have been resolved as of v1.2 (see §13).

## 1. Overview
Build a self-contained, single-user **local web application** that replaces the manual Excel spreadsheet currently used to run a small shop. The owner manages products (with photos), stock, sales, expenses, profit, and reports through a browser UI. Launched by double-clicking a file on the shop PC — no server, no cloud, no accounts. Sales support **discounts**: an item can be sold below its list price.

## 2. Background and current state
- Today all tracking is manual in `Copy of WS'Shop.xlsx` (sheet "Feuille 1", rows 4–66 = product lines, row 67 = totals). A matching CSV export also exists: `Copy of WS'Shop - Feuille 1.csv`.
- Columns: **Prix achat unitaire, Quantité, Prix vente unitaire, Articles vendus, Articles restants, Dépenses totales, Prix ventes totales, Bénéfices.**
- Formulas: Dépenses = prix_achat × quantité ; Ventes = prix_vente × vendus ; Bénéfices = ventes − dépenses.
- Data problems the app must fix: no product names (only prices/quantities), rows with a "–" for Prix vente unitaire (these are **not unsold products but operating costs** — transport, packaging, delivery — that were tracked in the same sheet), occasional float vs int quantity, manual drift in "restants".

### Current totals (row 67) — must be reproduced by the seed import
| Metric | Value |
|---|---|
| Quantity bought | 183 |
| Units sold | 102 |
| Units remaining | 76 |
| Total expenses | €724.32 |
| Total sales | €814.99 |
| Profit | €215.68 |

Note: "Total expenses" (€724.32) is the sum of *all* purchase costs recorded in the sheet, which includes both resellable-product stock purchases and service/operating costs (rows with "–" for Prix vente). The seed import must reproduce this total across the new `products` (via `stock_transactions`) and `expenses` tables combined.

## 3. Goals
1. Remove manual spreadsheet maintenance entirely.
2. Fast, obvious UI: add product (+ photo), restock, register a sale (with optional discount), log an expense — each 2–3 clicks.
3. Correct automatic math: current stock, revenue, expenses, profit per product and overall, including discounted sales and standalone operating expenses.
4. Visual dashboard: KPIs, sales-over-time, best sellers, stock alerts, discounts given, operating expenses.
5. Export back to CSV/XLSX in the familiar spreadsheet layout for backups, plus a dedicated expenses sheet.
6. Double-click launch with zero configuration.

## 4. Non-Goals (v1)
- No multi-user, roles, or login (single owner, one PC).
- No cloud hosting, no online payments, no PDF invoices.
- No barcode scanning, no supplier management, no taxes/full accounting (expenses tracking is a simple ledger, not double-entry bookkeeping).
- Stock valuation is simple quantity tracking, not FIFO/FEFO costing.

## 5. Users
- **Owner (non-technical, primary):** uses daily; needs big buttons, search, status badges, no configuration. Often prices items down to clear stock — discounts are a normal everyday action. Also incurs regular operating costs (transport, packaging, delivery) that aren't tied to a specific product.
- **Maintainer (technical, secondary):** extends later; needs clean structure, comments, README.

## 6. Tech stack [DECIDED]
| Layer | Choice |
|---|---|
| Language | Python 3.11 (already installed) |
| Web framework | Flask (server-rendered Jinja2 templates) |
| Database | SQLite via SQLAlchemy (`data/shop.db`) |
| Frontend | Bootstrap 5 + Chart.js, **vendored locally** (works offline) |
| Images | Uploads to `static/uploads/`, served by Flask; placeholder when absent |
| Import/Export | pandas + openpyxl (already installed) |
| Launch | `run.bat` starts Flask on 127.0.0.1:5000 and opens the browser |
| UI language | French (owner and data are French) |

## 7. Functional requirements

### 7.1 Dashboard (`/`)
- KPI cards: Total sales, Profit, Total expenses (product purchases + operating expenses combined), **Operating expenses (Frais)**, Units in stock, Units sold, **Total discounts given**.
- Chart.js charts: sales last 30 days (line); revenue vs expenses vs profit by month (bar); top sellers (bar); stock by category/status (doughnut).
- Alerts: low-stock and out-of-stock products with links.
- Quick actions: "Ajouter un produit", "Enregistrer une vente", "Ajouter une dépense".

### 7.2 Products and inventory (`/products` + CRUD)
- Fields: **Nom** (required, unique — *new*), **Catégorie** (free text with autocomplete suggestions drawn from existing categories), **Prix d'achat unitaire**, **Prix de vente unitaire**, **Quantité en stock**, **Seuil de stock bas** (default 1), **Image** (jpg/png/webp ≤5MB; thumbnail; placeholder).
- List: search, filter by category and status (En stock / Stock bas / Rupture), sortable.
- Actions: edit, delete (**soft-delete** — hidden from active lists but retained in DB so sales history stays intact), **restock** (records a stock-in transaction).
- **Stock is always derived** (bought − sold + refunds), never typed by hand.

### 7.3 Sales and discounts (`/sales`, `/sales/new`, `/sales/<id>/void`)  **[DECIDED — discounts are required]**
- New sale: searchable product picker, quantity input, current list price shown.
- **Discount control:** the owner may set the actual charged unit price **lower** than the product list price (a clear-sale discount). Validate: discount price ≤ list price, and ≥ 0. Show the discount as amount (€) and percentage (%) live. Discount % = (list − charged) / list.
- Revenue is computed from the **actually charged** price, never the list price.
- Blocked if quantity exceeds stock.
- Sales history table (filters: date range, product) shows date/time, product, qty, list price, **charged price, discount**, total received, profit.
- **Void/refund:** restores stock, excludes the sale from totals (kept as flagged row).
- Deleting a product keeps its sales via name/price snapshots.

### 7.4 Operating expenses (`/expenses`, `/expenses/new`)  **[NEW in v1.2]**
- Simple ledger for costs not tied to a specific resellable product: transport, packaging, delivery, and similar operating costs.
- Fields: **Date**, **Description**, **Montant (€)**. No product/stock linkage.
- List view: date range filter, running total.
- These entries are **not** products — they never appear in the sale picker, stock lists, or stock alerts.
- Counted in the dashboard's overall "Total expenses" figure alongside product purchase costs, and shown separately as "Frais" (operating expenses).

### 7.5 Import / Export
- **Import (first run):** `seed.py` reads the existing CSV/XLSX → products + initial stock + expenses. Row-mapping (see §13, resolved):
  - Rows with a Prix vente value → one **product** per row, named generically `Produit 1`, `Produit 2`, … in spreadsheet row order (owner will rename manually afterward); category left blank/free text.
  - Rows with "–" for Prix vente (no listed sale price — transport, packaging, delivery, etc.) → one **expense** entry per row instead, using the purchase price × quantity as the amount, with a generic description (e.g. `Import ligne <row>`) for the owner to refine.
  - This split must reproduce the row-67 totals in §2 exactly across products + stock_transactions + expenses combined.
- **Export:** CSV/XLSX in old layout (rows + totals row) plus a sales-history sheet (incl. discount column) plus an **expenses sheet**.

### 7.6 Images
- Validate extension & size; save as `uuid.ext` in `static/uploads/`; remove old file on replace/delete.

## 8. Data model (SQLite via SQLAlchemy)

**`products`**
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT NOT NULL UNIQUE | |
| category | TEXT NULL | |
| purchase_price | REAL NOT NULL | unit cost |
| sale_price | REAL NOT NULL | list (normal) unit price |
| low_stock_threshold | INTEGER DEFAULT 1 | |
| image_filename | TEXT NULL | |
| is_deleted | BOOLEAN DEFAULT 0 | soft-delete flag |
| created_at / updated_at | DATETIME | |

**`stock_transactions`**
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| product_id | FK products | |
| type | TEXT | purchase / restock / sale / refund |
| quantity | INTEGER | signed, applied to stock |
| unit_price | REAL | price at the time |
| created_at | DATETIME | |

**`sales`**
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| product_id | FK products | |
| product_name_snapshot | TEXT | survives deletion |
| unit_purchase_price_snapshot | REAL | accurate profit |
| quantity | INTEGER > 0 | |
| list_unit_price | REAL | product list price at time of sale |
| charged_unit_price | REAL | price actually charged (may be lower) |
| discount_per_unit | REAL | list − charged (≥ 0) |
| total | REAL | charged_unit_price × qty |
| refunded | BOOLEAN DEFAULT 0 | |
| created_at | DATETIME | |

**`expenses`** *(new in v1.2)*
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| date | DATE NOT NULL | |
| description | TEXT NOT NULL | |
| amount | REAL NOT NULL | |
| created_at | DATETIME | |

Derived: stock = Σ purchases/restocks − Σ non-refunded sales + Σ refunds; profit = total − snapshot_purchase × qty; discounts = Σ discount_per_unit × qty; total expenses (dashboard) = Σ stock_transactions purchase/restock cost + Σ expenses.amount.

## 9. Routes (Flask)
| Route | Methods | Purpose |
|---|---|---|
| `/` | GET | Dashboard |
| `/products` | GET | List/search/filter |
| `/products/new` | GET, POST | Add |
| `/products/<id>/edit` | GET, POST | Edit |
| `/products/<id>/delete` | POST | Delete (soft) |
| `/products/<id>/restock` | POST | Restock |
| `/sales` | GET | History/filters |
| `/sales/new` | GET, POST | Register sale (with optional discount) |
| `/sales/<id>/void` | POST | Void/refund |
| `/expenses` | GET | List/filter |
| `/expenses/new` | GET, POST | Add operating expense |
| `/export` | GET | Download CSV/XLSX |

## 10. Non-functional requirements
- `run.bat` checks necessary tools, prints clear messages, opens http://127.0.0.1:5000.
- Every write committed; data survives restarts (SQLite WAL).
- Offline: no CDN calls — Bootstrap/Chart.js bundled in `static/vendor/`.
- Bind 127.0.0.1 only; validate uploads; parameterized queries; friendly error pages.
- Instant performance at this scale; clear module split, English comments, README.

## 11. UI/UX
- French labels, reuse spreadsheet terminology; responsive, touch-friendly; confirm destructive actions; clear empty states; uniform badges (green En stock / amber Stock bas / red Rupture).
- The sale form must make the discount obvious: list price shown, editable charged price, live "Remise" badge showing € and %.
- The expense form is intentionally minimal (date, description, amount) — no product picker, no stock impact.

## 12. Acceptance criteria
1. Clean Win machine + Python 3.11 → double-click `run.bat` → browser opens, DB auto-created.
2. Seed import reproduces totals: expenses €724.32 (products + operating expenses combined), sales €814.99, profit €215.68, stock 76, 63 source rows split across products and expenses.
3. Add product with image → visible with thumbnail and correct badge.
4. Sale of 2 units at list price → stock −2; dashboard updates immediately.
5. **Discounted sale:** product listed at €6.00 sold for €5.00 × 2 → revenue recorded €10.00 (not €12), discount column shows €1.00 per unit / 16.67%, profit computed correctly, dashboard "Total discounts" updates.
6. Selling more than stock is blocked with a clear French error.
7. Void restores stock and rolls back totals (including discount totals).
8. Low/out-of-stock flagged on dashboard.
9. Export yields old-format CSV/XLSX with totals row + sales sheet incl. discount + expenses sheet.
10. Restart preserves all data.
11. Zero-stock products show "Rupture".
12. **Expense entries never appear in the sale picker, stock lists, or stock alerts**, but do count toward the dashboard's overall expense total.
13. Deleting a product soft-deletes it (hidden from active lists) while its past sales remain intact via snapshots.

## 13. Resolved decisions (formerly Open Questions)
1. **Import mapping [RESOLVED]:** one product per spreadsheet row, named generically `Produit 1`, `Produit 2`, … in row order; owner renames manually post-import. Rows with no Prix vente ("–") are **not** imported as products — they become `expenses` entries instead (purchase price × quantity as the amount), since they represent operating costs (transport, packaging, delivery), not unsold inventory.
2. **Discounts [RESOLVED — required feature]:** always allowed, ≤ list price, ≥ 0. No approval workflow needed.
3. **Category [RESOLVED]:** free text with autocomplete suggestions (drawn from existing categories already in use).
4. **Soft-delete [RESOLVED]:** products are soft-deleted (`is_deleted` flag); hidden from active lists/pickers but retained for sales-history integrity.
5. **Number format [RESOLVED]:** EUR, comma-decimal display in the UI (e.g. `5,00 €`), stored as REAL internally.
6. **Operating expenses [NEW, RESOLVED]:** modeled as a standalone `expenses` table (date, description, amount) rather than as non-resale products. Surfaced in the UI via a dashboard KPI card and a dedicated `/expenses` page, and included as a sheet in CSV/XLSX export.

## 14. Target file tree
```
Bilal/
  PRD.md
  README.md            # FR quick-start + EN dev notes
  requirements.txt     # flask, flask-sqlalchemy, pandas, openpyxl
  app.py               # Flask app + routes
  models.py            # SQLAlchemy models (Product, StockTransaction, Sale, Expense)
  seed.py              # DB create + CSV/XLSX import (products + expenses split)
  export.py            # CSV/XLSX export helpers (incl. expenses sheet)
  run.bat              # double-click launcher
  data/                # shop.db (runtime)
  static/css/styles.css
  static/js/app.js
  static/vendor/       # Bootstrap 5, Chart.js
  static/uploads/      # product images
  templates/           # base, dashboard, products, product_form,
                       # sales, sale_form, expenses, expense_form,
                       # export, error
```

## 15. Definition of done (implementation agent)
- All acceptance criteria pass in a manual end-to-end test.
- Seed import verified against the real CSV (totals match exactly, including the products/expenses split).
- `run.bat` verified from a clean checkout.
- Handoff notes document each resolved item in §13 and why.

## Appendix — real data sample (rows 4–13 of Feuille 1)
| Row | Prix achat | Qté | Prix vente | Vendus | Restants | Import target |
|---|---|---|---|---|---|---|
| 4 | 0.99 | 4 | – | 3 | 1 | expenses (0.99 × 4 = €3.96) |
| 5 | 1.49 | 1 | – | 1 | 0 | expenses (1.49 × 1 = €1.49) |
| 6 | 21.51 | 1 | – | – | 1 | expenses (21.51 × 1 = €21.51) |
| 8 | 3.89 | 2 | 6.00 | 2 | 0 | product "Produit 8" |
| 9 | 3.89 | 4 | 6.00 | 4 | 0 | product "Produit 9" |
| 10 | 3.89 | 3 | 6.00 | 3 | 0 | product "Produit 10" |
| 11 | 3.89 | 2 | 6.00 | – | 2 | product "Produit 11" |
| 12 | 3.89 | 1 | 6.00 | 1 | 0 | product "Produit 12" |
| 13 | 3.89 | 1 | 6.00 | 1 | 0 | product "Produit 13" |

*(Totals: bought 183, sold 102, remaining 76, expenses €724.32, sales €814.99, profit €215.68.)*
