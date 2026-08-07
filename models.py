"""
MyBoutiq - SQLAlchemy models.

Data model follows PRD section 8:
- Product           : resellable item (soft-deletable, keeps sales history)
- StockTransaction  : signed quantity ledger (purchase / restock / sale / refund)
- Sale              : sales history with price snapshots (survives product deletion)
- Expense           : standalone operating-cost ledger (transport, packaging, delivery)

Stock is ALWAYS derived from stock_transactions, never stored/typed by hand.
Comments are in English (PRD section 10).
"""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    purchase_price = db.Column(db.Float, nullable=False, default=0.0)
    sale_price = db.Column(db.Float, nullable=False, default=0.0)
    low_stock_threshold = db.Column(db.Integer, nullable=False, default=1)
    image_url = db.Column(db.String(500), nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    transactions = db.relationship(
        "StockTransaction", backref="product", lazy="dynamic",
        cascade="all, delete-orphan",
    )
    sales = db.relationship(
        "Sale", backref="product", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def stock(self) -> int:
        """Derived current stock.

        purchases/restocks are positive, sales are negative, refunds are positive,
        so the running sum of all quantities IS the current stock.
        """
        return int(sum(t.quantity for t in self.transactions))

    @property
    def quantity_bought(self) -> int:
        """Total units ever purchased/restocked for this product."""
        return int(
            sum(t.quantity for t in self.transactions if t.type in ("purchase", "restock"))
        )

    @property
    def status(self) -> str:
        """ok = En stock, low = Stock bas, out = Rupture."""
        if self.stock <= 0:
            return "out"
        if self.stock <= self.low_stock_threshold:
            return "low"
        return "ok"

    # The image URL is stored directly in the DB; no derived property needed.

# ---------------------------------------------------------------------------
# User model for authentication
# ---------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def __repr__(self):  # pragma: no cover - debug helper
        return f"<Product {self.id} {self.name!r} stock={self.stock}>"


class StockTransaction(db.Model):
    __tablename__ = "stock_transactions"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    type = db.Column(db.String(20), nullable=False)  # purchase / restock / sale / refund
    quantity = db.Column(db.Integer, nullable=False)  # signed: sale is negative
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    # Snapshots: survive product deletion / rename, keep profit accurate.
    product_name_snapshot = db.Column(db.String(200), nullable=False)
    unit_purchase_price_snapshot = db.Column(db.Float, nullable=False, default=0.0)
    quantity = db.Column(db.Integer, nullable=False)
    list_unit_price = db.Column(db.Float, nullable=False)
    charged_unit_price = db.Column(db.Float, nullable=False)
    discount_per_unit = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False)
    refunded = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    @property
    def profit(self) -> float:
        """Gross profit = revenue - (purchase cost of the sold units)."""
        return round(self.total - self.unit_purchase_price_snapshot * self.quantity, 2)

    @property
    def discount_percent(self) -> float:
        if self.list_unit_price > 0:
            return round((self.discount_per_unit / self.list_unit_price) * 100, 2)
        return 0.0

    def __repr__(self):  # pragma: no cover - debug helper
        return f"<Sale {self.id} {self.product_name_snapshot!r} x{self.quantity} {self.total}€>"


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.String(300), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):  # pragma: no cover - debug helper
        return f"<Expense {self.id} {self.description!r} {self.amount}€>"
