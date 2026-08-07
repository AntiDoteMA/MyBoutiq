# MyBoutiq
FR : [FR README.md]([https://github.com/AntiDoteMA/AXIOM-APP-Alpha](https://github.com/AntiDoteMA/MyBoutiq/blob/main/FR_README.md))
A shop-management web app: products (with photos), stock, sales with discounts,
expenses, dashboard and exports — **protected by a sign-in** and **bilingual FR / EN**.
It replaces the legacy Excel spreadsheet and runs either **locally** (double-click
`run.bat`, zero setup) or **online** (free hosting on PythonAnywhere, photos served
from the ImageKit CDN).

## 📝 License

This is just a fun little project built to help out a friend. **No licensing, no
restrictions** — anyone is free to use it, modify it, or do whatever they like with
it. 😄

## 🚀 Quick start (end user)

1. Double-click **`run.bat`**.
2. The browser opens `http://127.0.0.1:5000` → login page.
3. Sign in with the default account: **admin / admin123**.
4. **Change the password immediately**: the **Account** button in the navbar.

No configuration needed: Python 3.11 is enough. On first launch the database is created
and the legacy spreadsheet is **imported automatically** (`Copy of WS'Shop.xlsx` or its CSV export).

## 🔑 Sign-in & security

- Every page (except login) requires being signed in.
- Passwords are stored **hashed** (`werkzeug.security`).
- **CSRF protection** on every form (Flask-WTF tokens).
- The login `next=` redirect is limited to internal paths (no open redirect).
- In production, set **`SECRET_KEY`** in the environment (sessions + CSRF tokens).

## 📦 Features

- **Dashboard**: sales, profit, expenses (products + operating costs), stock, discounts
  given; charts (30-day sales, monthly sales/expenses/profit, top sellers, stock by
  status); low-stock / out-of-stock alerts.
- **Products**: photo (jpg/png/webp ≤ 5 MB), **post-ready description** (emojis and line
  breaks kept, **📋 Copy** button for Facebook), category (suggestions), search / filters /
  sorting, restocking, **soft delete** (sales history is kept). Stock is **always derived**
  (bought − sold + refunded).
- **Sales**: list price shown, **editable charged price (discount)** with a live
  “Discount € / %” badge, blocked if quantity > stock, **refund/void** (restores stock
  and removes the sale from totals).
- **Expenses**: a simple ledger (date, description, amount) for operating costs — never
  mixed up with products.
- **Account**: a “Change password” page (current + new + confirmation).
- **Export**: XLSX (3 sheets) or CSV in the familiar legacy layout (incl. the “Totaux”
  line), plus a Sales sheet with the Discount column and an Expenses sheet.
- **Bilingual FR / EN**: **FR | EN** toggle in the navbar (choice stored in a cookie),
  currency and date formats adapted. French remains the default language.

## 🔄 Initial import (legacy data)

`seed.py` reads the legacy spreadsheet (XLSX preferred, otherwise CSV):
- rows with a **sale price** → one product per row (`Produit 1`, `Produit 2`, …);
- rows with “–” as the sale price (transport, packaging, delivery…) → **expenses**;
- the stray 72.00 € line is imported as a 7th expense (needed to match the total).

Verified against the real data: **57 products + 7 expenses**, sales **€814.99**,
expenses **€724.32** (€594.44 purchases + €129.88 operating), **derived stock 76**.

Deliberate differences from the printed legacy figures (details in `seed.py`):
- “183 bought / 102 sold” counted the **cost lines too**; the app therefore shows
  174/98 with a derived stock of **76** (= “remaining”);
- “Profit €215.68” → the real result is **€90.67** (814.99 − 724.32), which is even what
  the source CSV contains as a trailing cell.

Re-import: `python seed.py --reset` (wipes all data, then re-imports). Imported sale
dates are **spread** over the last ~30 days (deterministic) so the “last 30 days” chart
is readable; `backfill_dates.py` does the same on an existing database (touches only
`created_at`/`date`).

## 🌐 Deployment (PythonAnywhere, free)

Every deployment (you, your friend…) needs its own free account and **personal ImageKit keys**.

1. Free account on `pythonanywhere.com` + an ImageKit account (free plan).
2. Get the 4 ImageKit values (`IMAGEKIT_PRIVATE_KEY`, `IMAGEKIT_PUBLIC_KEY`,
   `IMAGEKIT_URL_ENDPOINT`, `IMAGEKIT_ID`).
3. Upload the project (Files or Git), **without** `data/` or `.env`.
4. Bash console: `pip install --user -r requirements.txt`.
5. Create a `.env` file at the root (or use **Web → Environment variables**):
   ```
   IMAGEKIT_PRIVATE_KEY=...
   IMAGEKIT_PUBLIC_KEY=...
   IMAGEKIT_URL_ENDPOINT=...
   IMAGEKIT_ID=...
   SECRET_KEY=<a long random string>
   ```
6. **Web → WSGI configuration file**:
   ```python
   from app import create_app
   application = create_app()
   ```
7. Reload the site, sign in with **admin / admin123**, then change the password via
   **Account**.
8. (Optional) `python seed.py` to import the legacy spreadsheet.

**Security:** never share `IMAGEKIT_PRIVATE_KEY` or `SECRET_KEY`. Change the initial
password on first sign-in. Each PythonAnywhere account has its own `data/shop.db`.

## 🛠 Developer notes

- **Stack**: Python 3.11, Flask (server-rendered), SQLite via SQLAlchemy,
  Bootstrap 5 + Chart.js **vendored** in `static/vendor/` (offline),
  pandas + openpyxl (import/export), Flask-WTF (CSRF), ImageKit SDK (CDN photos).
- **i18n**: dictionaries in `i18n.py` (`STRINGS["fr"]` / `STRINGS["en"]`);
  templates use `{{ _("key") }}`, Python-side messages use `_t("key", ...)`,
  locale-aware `eur`/`dte` Jinja filters, `GET /lang/<code>` sets a cookie.
  To add a language: add a dict to `STRINGS` and register the code in `LANGUAGES`.
  Export headers stay French on purpose (the familiar spreadsheet layout).
- **Migrations**: `db.create_all()` + `_migrate_schema()` add new columns
  (e.g. `products.description`) idempotently (`ALTER TABLE ... ADD COLUMN`).
- **Demo dates**: `seed.py` spreads imported dates over ~30 days (`_spread`);
  `backfill_dates.py` re-spreads an existing database.
- **Data**: `data/shop.db` (SQLite, WAL). Stock is derived from `stock_transactions`
  (purchase/restock +, sale −, refund +). Revenue and profit always use the **charged**
  price; discount = list − charged. Soft delete: `is_deleted`, sales keep snapshots.
- **Dev server**: `python app.py` → http://127.0.0.1:5000 (localhost only).
- **Tests**: `python tests_acceptance.py` (Flask test client on a throwaway DB).

## Structure

```
MyBoutiq/
  README.md, requirements.txt
  app.py, models.py, i18n.py, seed.py, export.py, backfill_dates.py, run.bat
  tests_acceptance.py
  data/            # shop.db (created on first run)
  static/          # css, js, vendor (offline Bootstrap/Chart.js), uploads
  templates/       # Jinja2 (FR/EN via i18n.py)
```
