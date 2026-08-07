"""
Boutique Manager - Flask application.

Server-rendered, French UI, single-user local app.
- Binds 127.0.0.1 only, SQLite (WAL), offline vendored assets.
- Parameterized queries (SQLAlchemy ORM), validated uploads.
See PRD for full functional requirements.

Launch:  python app.py   (or double-click run.bat)
"""

import os
# Load environment variables from a .env file if present (helps during local dev)
# Load environment variables from a .env file if present.
try:
    from dotenv import load_dotenv
    # First load the default .env in the current working directory.
    load_dotenv()
    # Then explicitly load a .env located in the project root (BASE_DIR).
    load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))
except Exception as e:
    # If python-dotenv is not installed or the file is missing, we simply
    # continue – Flask will still read variables from the actual environment.
    pass
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
    session,
)
from sqlalchemy import event, func, text
from sqlalchemy.engine import Engine

from models import db, Product, Sale, StockTransaction, Expense, User
from i18n import t, normalize, DEFAULT_LANG

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
# Overridable via env var so tests can use a throwaway database.
DB_PATH = os.environ.get("BOUTIQUE_DB") or os.path.join(DATA_DIR, "shop.db")

os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="boutique-manager-local-key",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + DB_PATH.replace("\\", "/"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,  # just above the 5 MB image cap
    )

    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    db.init_app(app)

    # Initialise ImageKit SDK (used for direct upload to CDN)
    # The modern ImageKit SDK exposes the `ImageKit` class directly.
    from imagekitio import ImageKit
    try:
        # The modern `ImageKit` client only accepts the private key in its constructor.
        imagekit = ImageKit(
            private_key=os.getenv("IMAGEKIT_PRIVATE_KEY")
        )
    except Exception as exc:  # pragma: no cover – during local dev env vars may be absent
        # If the SDK cannot be initialised (missing keys), store None and continue.
        imagekit = None
        app.logger.warning(f"ImageKit client not initialised: {exc}")
    # expose via app config for later use
    app.config["IMAGEKIT_CLIENT"] = imagekit
    app.config["IMAGEKIT_URL_ENDPOINT"] = os.getenv("IMAGEKIT_URL_ENDPOINT")

    # Log which ImageKit environment variables are present (without exposing secrets)
    app.logger.info(
        "ImageKit env – ID: %s, Public: %s, Private: %s",
        "set" if os.getenv("IMAGEKIT_ID") else "missing",
        "set" if os.getenv("IMAGEKIT_PUBLIC_KEY") else "missing",
        "set" if os.getenv("IMAGEKIT_PRIVATE_KEY") else "missing",
    )

    @app.before_request
    def _auth_and_language():
        """Enforce authentication on all routes (except static assets and login).
        Also set the request language as before.
        """
        from flask import session
        # Static files are served under the `/static/` path.
        if request.path.startswith('/static/') or request.endpoint in ('login', 'logout', 'set_lang'):
            pass
        else:
            if not session.get('user_id'):
                return redirect(url_for('login'))
        # Language handling (unchanged)
        code = request.args.get("lang") or request.cookies.get("lang") or DEFAULT_LANG
        g.lang = normalize(code)

    @app.context_processor
    def _inject_i18n():
        lang = getattr(g, "lang", DEFAULT_LANG)
        return {
            "_": lambda key, **kw: t(key, lang, **kw),
            "lang": lang,
            "logged_in": bool(session.get("user_id")),
        }

    @app.template_filter("eur")
    def fr_eur(value):
        """1234.5 -> '1 234,50 €' (fr) or '€1,234.50' (en)."""
        if value is None:
            value = 0.0
        lang = getattr(g, "lang", DEFAULT_LANG)
        if lang == "en":
            return "€" + f"{value:,.2f}"
        return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " €"

    @app.template_filter("dte")
    def fr_date(value):
        lang = getattr(g, "lang", DEFAULT_LANG)
        fmt = "%m/%d/%Y" if lang == "en" else "%d/%m/%Y"
        return value.strftime(fmt)

    with app.app_context():
        db.create_all()
        _migrate_schema()

    register_routes(app)
    register_error_handlers(app)
    # Return the configured Flask app instance
    return app
def _migrate_schema():
    """Idempotently add columns introduced after the initial schema (SQLite).

    The original schema had an ``image_filename`` column.  The new PRD requires
    an ``image_url`` column to store a CDN URL.  SQLite does not support a direct
    ``DROP COLUMN`` operation, so we simply add the new column if it does not
    already exist.  Existing rows will have ``NULL`` for ``image_url`` which is
    compatible with the rest of the code.
    """
    from sqlalchemy import text
    from sqlalchemy import inspect as sa_inspect

    insp = sa_inspect(db.engine)
    # Add image_url column if missing
    if not any(col["name"] == "image_url" for col in insp.get_columns("products")):
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE products ADD COLUMN image_url VARCHAR(500)'))
    # The old image_filename column is left unchanged (SQLite cannot drop it easily)."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _to_float(value, fallback=None):
    if value is None:
        return fallback
    text = str(value).strip().replace(",", ".")
    try:
        return round(float(text), 2)
    except ValueError:
        return fallback


def _to_int(value, fallback=None):
    if value is None:
        return fallback
    text = str(value).strip()
    try:
        return int(round(float(text)))
    except ValueError:
        return fallback


# The original local‑file image handling helpers have been removed because images
# are now uploaded directly to ImageKit and stored as a CDN URL.


def active_products():
    return Product.query.filter_by(is_deleted=False).order_by(Product.name).all()


def all_product_names():
    return sorted(p.name for p in Product.query.all())


def _t(key, **kwargs):
    """Translate `key` in the current request's language (g.lang)."""
    return t(key, getattr(g, "lang", DEFAULT_LANG), **kwargs)


# ---------------------------------------------------------------------------
# Aggregates (dashboard / KPI)
# ---------------------------------------------------------------------------

def kpi_totals():
    active_sales = Sale.query.filter_by(refunded=False).all()

    total_sales = round(sum(s.total for s in active_sales), 2)
    units_sold = int(sum(s.quantity for s in active_sales))
    total_discounts = round(
        sum(s.discount_per_unit * s.quantity for s in active_sales), 2
    )
    total_profit = round(sum(s.profit for s in active_sales), 2)

    purchases = (
        db.session.query(
            func.coalesce(
                func.sum(StockTransaction.unit_price * StockTransaction.quantity), 0.0
            )
        )
        .filter(StockTransaction.type.in_(["purchase", "restock"]))
        .scalar()
        or 0.0
    )
    operating = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0.0)).scalar() or 0.0
    )
    total_expenses = round(purchases + operating, 2)

    units_stock = sum(p.stock for p in Product.query.filter_by(is_deleted=False).all())

    return {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "total_expenses": total_expenses,
        "operating": round(operating, 2),
        "units_stock": units_stock,
        "units_sold": units_sold,
        "total_discounts": total_discounts,
    }


def chart_payload():
    today = date.today()

    # Sales over the last 30 days (line chart).
    by_day = defaultdict(float)
    for s in Sale.query.filter_by(refunded=False).all():
        by_day[s.created_at.date()] += s.total
    days = [today - timedelta(days=i) for i in range(29, -1, -1)]
    line_30 = {
        "labels": [d.strftime("%d/%m") for d in days],
        "values": [round(by_day.get(d, 0.0), 2) for d in days],
    }

    # Revenue vs expenses vs profit by month (bar chart).
    by_month_rev = defaultdict(float)
    by_month_profit = defaultdict(float)
    by_month_exp = defaultdict(float)
    for s in Sale.query.filter_by(refunded=False).all():
        key = s.created_at.strftime("%Y-%m")
        by_month_rev[key] += s.total
        by_month_profit[key] += s.profit
    for e in Expense.query.all():
        by_month_exp[e.date.strftime("%Y-%m")] += e.amount
    for t in StockTransaction.query.filter(
        StockTransaction.type.in_(["purchase", "restock"])
    ):
        by_month_exp[t.created_at.strftime("%Y-%m")] += t.unit_price * t.quantity

    months = sorted(set(by_month_rev) | set(by_month_exp))
    bar = {
        "labels": [m[5:] + "/" + m[:4] for m in months],
        "revenue": [round(by_month_rev.get(m, 0.0), 2) for m in months],
        "expenses": [round(by_month_exp.get(m, 0.0), 2) for m in months],
        "profit": [round(by_month_profit.get(m, 0.0), 2) for m in months],
    }

    # Top sellers by quantity (bar chart).
    by_product = defaultdict(int)
    for s in Sale.query.filter_by(refunded=False).all():
        by_product[s.product_name_snapshot] += s.quantity
    top = sorted(by_product.items(), key=lambda kv: kv[1], reverse=True)[:8]
    top_sellers = {"labels": [n for n, _ in top], "values": [q for _, q in top]}

    # Stock by status (doughnut chart).
    statuses = {"ok": 0, "low": 0, "out": 0}
    for p in Product.query.filter_by(is_deleted=False).all():
        statuses[p.status] += 1
    doughnut = {
        "labels": [_t("status.ok"), _t("status.low"), _t("status.out")],
        "values": [statuses["ok"], statuses["low"], statuses["out"]],
    }

    return {"line": line_30, "bar": bar, "top": top_sellers, "doughnut": doughnut}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def register_routes(app):
    @app.route("/")
    def dashboard():
        totals = kpi_totals()
        products = Product.query.filter_by(is_deleted=False).all()
        alerts = [p for p in products if p.status in ("low", "out")][:10]
        return render_template(
            "dashboard.html", totals=totals, charts=chart_payload(), alerts=alerts
        )

    @app.route("/lang/<code>")
    def set_lang(code):
        code = normalize(code)
        resp = redirect(request.referrer or url_for("dashboard"))
        resp.set_cookie("lang", code, max_age=60 * 60 * 24 * 365)
        return resp

    # --------------------------- Products -------------------------------

    @app.route("/products")
    def products():
        query = request.args.get("q", "").strip().lower()
        category = request.args.get("category", "").strip()
        status_filter = request.args.get("status", "").strip()
        sort = request.args.get("sort", "name")

        items = active_products()
        if query:
            items = [
                p
                for p in items
                if query in p.name.lower()
                or query in (p.description or "").lower()
            ]
        if category:
            items = [p for p in items if (p.category or "") == category]
        if status_filter in ("ok", "low", "out"):
            items = [p for p in items if p.status == status_filter]

        key_map = {
            "name": lambda p: p.name.lower(),
            "category": lambda p: (p.category or "").lower(),
            "purchase": lambda p: p.purchase_price,
            "sale": lambda p: p.sale_price,
            "stock": lambda p: p.stock,
            "status": lambda p: p.status,
        }
        items.sort(key=key_map.get(sort, key_map["name"]))
        if sort in ("stock", "status") and request.args.get("order") == "desc":
            items.reverse()

        categories = sorted({p.category for p in active_products() if p.category})
        return render_template(
            "products.html",
            products=items,
            categories=categories,
            q=request.args.get("q", ""),
            category=category,
            status_filter=status_filter,
            sort=sort,
        )

    @app.route("/products/new", methods=["GET", "POST"])
    def product_new():
        if request.method == "POST":
            error = _create_or_update_product(None)
            if error:
                flash(error, "danger")
            else:
                flash(_t("flash.product_added"), "success")
                return redirect(url_for("products"))
        return render_template("product_form.html", product=None, categories=_all_categories())

    @app.route("/products/<int:pid>/edit", methods=["GET", "POST"])
    def product_edit(pid):
        product = Product.query.get_or_404(pid)
        if request.method == "POST":
            error = _create_or_update_product(product)
            if error:
                flash(error, "danger")
            else:
                flash(_t("flash.product_updated"), "success")
                return redirect(url_for("products"))
        return render_template(
            "product_form.html", product=product, categories=_all_categories()
        )

    @app.route("/products/<int:pid>/delete", methods=["POST"])
    def product_delete(pid):
        product = Product.query.get_or_404(pid)
        if not product.is_deleted:
            product.is_deleted = True  # soft-delete: keeps sales history intact
            # No local file to delete; simply clear the stored URL.
            product.image_url = None
            db.session.commit()
            flash(_t("flash.product_deleted"), "success")
        return redirect(url_for("products"))

    @app.route("/products/<int:pid>/restock", methods=["POST"])
    def product_restock(pid):
        product = Product.query.get_or_404(pid)
        qty = _to_int(request.form.get("quantity"), 0)
        if qty and qty > 0:
            db.session.add(
                StockTransaction(
                    product_id=product.id,
                    type="restock",
                    quantity=qty,
                    unit_price=product.purchase_price,
                )
            )
            db.session.commit()
            flash(_t("flash.restock", qty=qty), "success")
        else:
            flash(_t("flash.invalid_qty"), "danger")
        return redirect(url_for("products"))

    # ---------------------------------------------------------------------------
    # Authentication routes (login / logout)
    # ---------------------------------------------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Simple session based login using the User model."""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["user_id"] = user.id
                flash(_t("flash.login_success"), "success")
                # Redirect to original target if present
                next_url = request.args.get("next") or url_for("dashboard")
                return redirect(next_url)
            else:
                flash(_t("flash.login_failed"), "danger")
        # GET request – render login form
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash(_t("flash.logout_success"), "success")
        return redirect(url_for("login"))

    # --------------------------- Sales -------------------------------

    @app.route("/sales")
    def sales():
        date_from = request.args.get("from", "").strip()
        date_to = request.args.get("to", "").strip()
        product_name = request.args.get("product", "").strip()

        items = Sale.query.order_by(Sale.created_at.desc()).all()
        if date_from:
            try:
                d = datetime.strptime(date_from, "%Y-%m-%d").date()
                items = [s for s in items if s.created_at.date() >= d]
            except ValueError:
                pass
        if date_to:
            try:
                d = datetime.strptime(date_to, "%Y-%m-%d").date()
                items = [s for s in items if s.created_at.date() <= d]
            except ValueError:
                pass
        if product_name:
            items = [s for s in items if s.product_name_snapshot == product_name]

        total_received = round(sum(s.total for s in items if not s.refunded), 2)
        return render_template(
            "sales.html",
            sales=items,
            names=all_product_names(),
            total_received=total_received,
            date_from=date_from,
            date_to=date_to,
            product_name=product_name,
        )

    @app.route("/sales/new", methods=["GET", "POST"])
    def sale_new():
        if request.method == "POST":
            product = Product.query.filter_by(
                id=_to_int(request.form.get("product_id"), 0), is_deleted=False
            ).first()
            qty = _to_int(request.form.get("quantity"), 0)
            charged = _to_float(request.form.get("charged_price"))

            if product is None:
                flash(_t("flash.product_not_found"), "danger")
            elif qty is None or qty < 1:
                flash(_t("flash.invalid_qty_min"), "danger")
            elif product.stock < qty:
                flash(_t("flash.stock_insufficient", stock=product.stock), "danger")
            elif charged is None or charged < 0:
                flash(_t("flash.invalid_charged"), "danger")
            elif charged > product.sale_price:
                flash(
                    _t("flash.charged_above", price=f"{product.sale_price:g}"),
                    "danger",
                )
            else:
                sale = Sale(
                    product_id=product.id,
                    product_name_snapshot=product.name,
                    unit_purchase_price_snapshot=product.purchase_price,
                    quantity=qty,
                    list_unit_price=product.sale_price,
                    charged_unit_price=charged,
                    discount_per_unit=round(product.sale_price - charged, 2),
                    total=round(charged * qty, 2),
                )
                db.session.add(sale)
                db.session.add(
                    StockTransaction(
                        product_id=product.id,
                        type="sale",
                        quantity=-qty,
                        unit_price=charged,
                    )
                )
                db.session.commit()
                if charged < product.sale_price:
                    flash(_t("flash.sale_discounted"), "success")
                else:
                    flash(_t("flash.sale_ok"), "success")
                return redirect(url_for("sales"))
        return render_template("sale_form.html", products=active_products())

    @app.route("/sales/<int:sid>/void", methods=["POST"])
    def sale_void(sid):
        sale = Sale.query.get_or_404(sid)
        if not sale.refunded:
            sale.refunded = True
            # Restore stock via a positive 'refund' transaction.
            db.session.add(
                StockTransaction(
                    product_id=sale.product_id,
                    type="refund",
                    quantity=sale.quantity,
                    unit_price=sale.charged_unit_price,
                )
            )
            db.session.commit()
            flash(_t("flash.voided"), "success")
        return redirect(request.referrer or url_for("sales"))

    # --------------------------- Expenses -------------------------------

    @app.route("/expenses")
    def expenses():
        date_from = request.args.get("from", "").strip()
        date_to = request.args.get("to", "").strip()
        items = Expense.query.order_by(Expense.date.desc(), Expense.id.desc()).all()
        if date_from:
            try:
                d = datetime.strptime(date_from, "%Y-%m-%d").date()
                items = [e for e in items if e.date >= d]
            except ValueError:
                pass
        if date_to:
            try:
                d = datetime.strptime(date_to, "%Y-%m-%d").date()
                items = [e for e in items if e.date <= d]
            except ValueError:
                pass
        total = round(sum(e.amount for e in items), 2)
        return render_template(
            "expenses.html",
            expenses=items,
            total=total,
            date_from=date_from,
            date_to=date_to,
        )

    @app.route("/expenses/new", methods=["GET", "POST"])
    def expense_new():
        if request.method == "POST":
            description = request.form.get("description", "").strip()
            amount = _to_float(request.form.get("amount"))
            day = request.form.get("date", "").strip()
            try:
                expense_date = (
                    datetime.strptime(day, "%Y-%m-%d").date() if day else date.today()
                )
            except ValueError:
                expense_date = None

            if not description:
                flash(_t("flash.desc_required"), "danger")
            elif amount is None or amount < 0:
                flash(_t("flash.invalid_amount"), "danger")
            elif expense_date is None:
                flash(_t("flash.invalid_date"), "danger")
            else:
                db.session.add(
                    Expense(date=expense_date, description=description, amount=amount)
                )
                db.session.commit()
                flash(_t("flash.expense_added"), "success")
                return redirect(url_for("expenses"))
        return render_template("expense_form.html", today=date.today())

    # --------------------------- Export -------------------------------

    @app.route("/export")
    def export():
        return render_template("export.html")

    @app.route("/export/xlsx")
    def export_xlsx():
        from export import build_xlsx

        buffer = build_xlsx()
        return send_file(
            buffer,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"boutique_{datetime.now():%Y%m%d_%H%M}.xlsx",
        )

    @app.route("/export/csv/feuille1")
    def export_csv_feuille1():
        from export import build_csv_featured

        path = build_csv_featured()
        return send_file(path, mimetype="text/csv", as_attachment=True)

    @app.route("/export/csv/ventes")
    def export_csv_ventes():
        from export import build_csv_sales

        path = build_csv_sales()
        return send_file(path, mimetype="text/csv", as_attachment=True)

    @app.route("/export/csv/depenses")
    def export_csv_depenses():
        from export import build_csv_expenses

        path = build_csv_expenses()
        return send_file(path, mimetype="text/csv", as_attachment=True)


# ---------------------------------------------------------------------------
# Product form helper (shared by /products/new and /products/<id>/edit)
# ---------------------------------------------------------------------------

def _all_categories():
    return sorted({p.category for p in Product.query.all() if p.category})


def _create_or_update_product(product):
    """Shared create/edit logic. Returns an error string, or None on success."""
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip() or None
    description = request.form.get("description", "").strip() or None
    purchase = _to_float(request.form.get("purchase_price"))
    sale = _to_float(request.form.get("sale_price"))
    low_threshold = _to_int(request.form.get("low_stock_threshold"), 1)
    initial_stock = _to_int(request.form.get("initial_stock"), 0)

    if not name:
        return _t("err.name_required")
    if purchase is None or purchase < 0:
        return _t("err.buy_price")
    if sale is None or sale < 0:
        return _t("err.sale_price")
    if low_threshold is None or low_threshold < 0:
        return _t("err.threshold")

    # Unique-name check across ALL products (soft-deleted included).
    dup = Product.query.filter(
        Product.name == name, Product.id != (product.id if product else None)
    ).first()
    if dup:
        return _t("err.name_exists", name=name)

    # Image handling: upload directly to ImageKit (no local file storage).
    image_file = request.files.get("image")
    image_url = None
    if image_file and image_file.filename:
        # Read bytes and upload via ImageKit client stored in app config.
        img_bytes = image_file.read()
        # Access the Flask app config via the application context
        from flask import current_app
        imagekit = current_app.config.get("IMAGEKIT_CLIENT")
        if not imagekit:
            return "ImageKit client not configured"
        # If the client exists, attempt the upload
        try:
            # Modern ImageKit SDK API uses `imagekit.files.upload`
            resp = imagekit.files.upload(
                file=img_bytes,
                file_name=image_file.filename
            )
            image_url = resp.url
        except Exception as exc:
            # Attempt to provide more diagnostic info if the SDK gave a response.
            if hasattr(exc, "response") and exc.response is not None:
                try:
                    err_json = exc.response.json()
                except Exception:
                    err_json = exc.response.text
                return f"Image upload failed: {exc} – server response: {err_json}"
            return f"Image upload failed: {exc}"

    if product is None:
        product = Product(
            name=name,
            category=category,
            description=description,
            purchase_price=purchase,
            sale_price=sale,
            low_stock_threshold=low_threshold or 1,
            image_url=image_url,
        )
        db.session.add(product)
        db.session.flush()  # get product.id for the stock transaction
        if initial_stock and initial_stock > 0:
            db.session.add(
                StockTransaction(
                    product_id=product.id,
                    type="purchase",
                    quantity=initial_stock,
                    unit_price=purchase,
                )
            )
    else:
        # Update existing product. If a new image was uploaded, replace the URL.
        if image_url:
            product.image_url = image_url
        product.name = name
        product.category = category
        product.description = description
        product.purchase_price = purchase
        product.sale_price = sale
        product.low_stock_threshold = low_threshold or 1

    db.session.commit()
    return None


# ---------------------------------------------------------------------------
# Error pages
# ---------------------------------------------------------------------------

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", message=_t("error.404")), 404

    @app.errorhandler(413)
    def too_large(error):
        return render_template("error.html", message=_t("error.413")), 413

    @app.errorhandler(Exception)
    def generic(error):
        app.logger.exception("Unhandled error")
        return render_template("error.html", message=_t("error.generic")), 500


# ---------------------------------------------------------------------------

def main():
    app = create_app()

    # Open the browser a moment after the server is up (keeps run.bat simple).
    import threading
    import time
    import webbrowser

    def _open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:5000")

    threading.Thread(target=_open_browser, daemon=True).start()

    # Bind to localhost only - zero exposure to the network.
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    print("Starting Boutique Manager...")
    from werkzeug.security import generate_password_hash
    x_password_hash = generate_password_hash("admin")
    print(f"generate_password_hash: {x_password_hash}")
    main()