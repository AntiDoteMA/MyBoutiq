"""
Boutique Manager - lightweight internationalization.

No external dependency: strings live in two plain dictionaries (fr / en).
French is the default UI language (PRD section 6). To add another language,
add a new dict under `STRINGS` and register the code in `LANGUAGES`.

Usage (Python):  t("key", lang, name="x")      -> localized string
Template:        {{ _("key", name=p.name) }}   -> localized string
"""

LANGUAGES = ("fr", "en")
DEFAULT_LANG = "fr"
LANGS = {"fr": "Français", "en": "English"}


def normalize(code):
    """Return a supported language code, or the default."""
    return code if code in LANGUAGES else DEFAULT_LANG


def t(key, lang=DEFAULT_LANG, **kwargs):
    """Return the localized string for `key` in `lang`.

    Falls back to French, then to the key itself. Supports Python
    %(name)s formatting for interpolation.
    """
    lang = normalize(lang)
    table = STRINGS.get(lang, STRINGS[DEFAULT_LANG])
    text = table.get(key) or STRINGS[DEFAULT_LANG].get(key) or key
    if kwargs:
        try:
            return text % kwargs
        except (ValueError, TypeError):
            return text
    return text


STRINGS = {
    "fr": {
        # ---- Navbar ----
        "nav.dashboard": "Tableau de bord",
        "nav.products": "Produits",
        "nav.sales": "Ventes",
        "nav.expenses": "Dépenses",
        "nav.export": "Exporter",
        "nav.logout": "Déconnexion",

        # ---- Shared actions ----
        "action.filter": "Filtrer",
        "action.reset": "Réinitialiser",
        "action.add_product": "＋ Ajouter un produit",
        "action.new_sale": "💶 Enregistrer une vente",
        "action.new_expense": "💸 Ajouter une dépense",
        "action.cancel": "Annuler",
        "action.save": "Enregistrer",
        "action.confirm": "Valider",
        "action.edit": "Modifier",
        "action.restock": "Réapprovisionner",
        "action.delete": "Supprimer",
        "action.copy": "Copier",
        "confirm.delete": "Supprimer « %(name)s » ?",

        # Status badges
        "status.ok": "En stock",
        "status.low": "Stock bas",
        "status.out": "Rupture",
        "in.stock": "en stock",

        # Dashboard
        "dashboard.title": "Tableau de bord",
        "kpi.total_sales": "Ventes totales",
        "kpi.profit": "Bénéfice",
        "kpi.total_expenses": "Dépenses totales",
        "kpi.operating": "Frais (opérationnels)",
        "kpi.units_stock": "Unités en stock",
        "kpi.units_sold": "Unités vendues",
        "kpi.total_discounts": "Total remises données",
        "kpi.margin": "Marge brute / unité vendue",
        "chart.line_title": "Ventes – 30 derniers jours",
        "chart.doughnut_title": "Stock par statut",
        "chart.bar_title": "Ventes vs dépenses vs bénéfice (par mois)",
        "chart.top_title": "Meilleures ventes (quantité)",
        "chart.sales": "Ventes (€)",
        "chart.revenue": "Ventes",
        "chart.expenses": "Dépenses",
        "chart.profit": "Bénéfice",
        "chart.qty_sold": "Qté vendue",
        "alerts.title": "Alertes de stock",
        "alerts.none": "Aucune alerte : les niveaux de stock sont suffisants.",

        # Products
        "products.title": "Produits",
        "search.placeholder": "Rechercher par nom…",
        "products.all_categories": "Toutes les catégories",
        "products.all_status": "Tous les statuts",
        "products.photo": "Photo",
        "products.name": "Nom",
        "products.category": "Catégorie",
        "products.buy_price": "Prix achat",
        "products.sale_price": "Prix vente",
        "products.stock": "Stock",
        "products.status": "Statut",
        "products.actions": "Actions",
        "products.empty": "Aucun produit trouvé.",
        "restock.title": "Réapprovisionner",
        "restock.quantity": "Quantité ajoutée",
        "restock.current": "Stock actuel :",

        # Product form
        "product_form.new": "Ajouter un produit",
        "product_form.edit": "Modifier le produit",
        "product_form.name": "Nom (unique) *",
        "product_form.category": "Catégorie",
        "product_form.category_ph": "Ex. Bricolage, Électronique…",
        "product_form.description": "Description (facultatif)",
        "product_form.description_hint": "Texte libre — emojis et sauts de ligne acceptés. Une copie est prête pour une publication.",
        "product_form.buy": "Prix d'achat unitaire (€) *",
        "product_form.sale": "Prix de vente unitaire (€) *",
        "product_form.threshold": "Seuil de stock bas",
        "product_form.threshold_hint": "En dessous de ce seuil, le badge devient « Stock bas ».",
        "product_form.initial_stock": "Quantité initiale en stock",
        "product_form.initial_stock_hint": "Ajoutée comme un achat (le stock reste calculé).",
        "product_form.image": "Image (jpg / png / webp, max 5 Mo)",

        # Sales
        "sales.title": "Historique des ventes",
        "sales.new": "💶 Nouvelle vente",
        "sales.total_received": "Total encaissé (ventes actives) :",
        "sales.from": "Du",
        "sales.to": "Au",
        "sales.product": "Produit",
        "sales.all_products": "Tous les produits",
        "sales.date": "Date",
        "sales.qty": "Qté",
        "sales.list_price": "Prix liste",
        "sales.charged": "Prix facturé",
        "sales.discount": "Remise",
        "sales.total": "Total",
        "sales.profit": "Bénéfice",
        "sales.status": "Statut",
        "sales.refunded": "Remboursée",
        "sales.void": "Rembourser",
        "sales.confirm_void": "Rembourser cette vente ?",
        "sales.empty": "Aucune vente enregistrée.",

        # Sale form
        "sale_form.title": "Enregistrer une vente",
        "sale_form.product": "Produit *",
        "sale_form.choose": "— Choisir un produit —",
        "sale_form.quantity": "Quantité *",
        "sale_form.stock_available": "Stock disponible :",
        "sale_form.list_price": "Prix affiché (liste)",
        "sale_form.charged": "Prix facturé / unité (€) *",
        "sale_form.discount_label": "Remise :",
        "sale_form.reduction": "% de réduction",
        "sale_form.total": "Total encaissé :",
        "sale_form.submit": "💶 Valider la vente",
        "sale_form.qty_exceeds": "La quantité dépasse le stock disponible (%(n)s).",
        "sale_form.placeholder": "0,00",

        # Expenses
        "expenses.title": "Dépenses (frais opérationnels)",
        "expenses.total": "Total affiché :",
        "expenses.description": "Description",
        "expenses.amount": "Montant",
        "expenses.empty": "Aucune dépense enregistrée.",
        "expense_form.title": "Ajouter une dépense",
        "expense_form.hint": "Transport, emballage, livraison… une dépense n'est pas un produit : elle n'affecte ni le stock ni la liste des produits.",
        "expense_form.date": "Date *",
        "expense_form.description": "Description *",
        "expense_form.desc_ph": "Ex. Livraison colis, emballages…",
        "expense_form.amount": "Montant (€) *",

        # Export
        "export.title": "Exporter les données",
        "export.intro": "Sauvegardez vos données au format familier : présentation de l'ancien tableau (lignes + ligne « Totaux »), historique des ventes avec la colonne Remise, et feuille des dépenses.",
        "export.xlsx": "📗 Fichier Excel complet",
        "export.xlsx_desc": "Un classeur avec 3 feuilles : Feuille 1 (ancien format + totaux), Ventes, Dépenses.",
        "export.download_xlsx": "Télécharger le XLSX",
        "export.csv": "📄 Fichiers CSV",
        "export.csv_desc": "Un CSV par feuille, compatible avec l'ancien tableau.",
        "export.csv_fe11": "Feuille 1 (CSV)",
        "export.csv_sales": "Ventes (CSV)",
        "export.csv_expenses": "Dépenses (CSV)",

        # Error
        "error.404": "Page introuvable.",
        "error.413": "Fichier trop volumineux (max 5 Mo).",
        "error.generic": "Une erreur est survenue.",
        "error.oops": "Oups !",
        "error.back": "Retour au tableau de bord",

        # Login
        "login.title": "Connexion",
        "login.username": "Nom d'utilisateur",
        "login.password": "Mot de passe",
        "login.submit": "Se connecter",
        "login.cancel": "Annuler",

        # Flash messages (Python-side, translated at flash time)
        "flash.product_added": "Produit ajouté.",
        "flash.product_updated": "Produit modifié.",
        "flash.product_deleted": "Produit supprimé (l'historique des ventes est conservé).",
        "flash.restock": "Réapprovisionnement de %(qty)s unité(s).",
        "flash.invalid_qty": "Quantité invalide.",
        "flash.product_not_found": "Produit introuvable.",
        "flash.invalid_qty_min": "Quantité invalide (doit être ≥ 1).",
        "flash.stock_insufficient": "Stock insuffisant : %(stock)s unité(s) disponible(s).",
        "flash.invalid_charged": "Prix facturé invalide (doit être ≥ 0).",
        "flash.charged_above": "Le prix facturé ne peut pas dépasser le prix affiché (%(price)s €).",
        "flash.sale_discounted": "Vente enregistrée avec remise.",
        "flash.sale_ok": "Vente enregistrée.",
        "flash.voided": "Vente remboursée : stock restauré, vente retirée des totaux.",
        "flash.desc_required": "La description est obligatoire.",
        "flash.invalid_amount": "Montant invalide (doit être ≥ 0).",
        "flash.invalid_date": "Date invalide.",
        "flash.expense_added": "Dépense enregistrée.",
        "flash.login_success": "Connexion réussie.",
        "flash.login_failed": "Nom d'utilisateur ou mot de passe incorrect.",
        "flash.logout_success": "Vous êtes déconnecté.",

        # Validation returns (product form)
        "err.name_required": "Le nom du produit est obligatoire.",
        "err.buy_price": "Prix d'achat invalide (doit être ≥ 0).",
        "err.sale_price": "Prix de vente invalide (doit être ≥ 0).",
        "err.threshold": "Seuil de stock bas invalide.",
        "err.name_exists": "Un produit nommé «%(name)s» existe déjà.",
        "err.image_format": "Format d'image non supporté (jpg, png, webp uniquement).",
        "err.image_mime": "Le fichier envoyé n'est pas une image.",
        "err.image_big": "Image trop volumineuse (max 5 Mo).",
    },
    "en": {
        # ---- Navbar ----
        "nav.dashboard": "Dashboard",
        "nav.products": "Products",
        "nav.sales": "Sales",
        "nav.expenses": "Expenses",
        "nav.export": "Export",
        "nav.logout": "Log out",

        # ---- Shared actions ----
        "action.filter": "Filter",
        "action.reset": "Reset",
        "action.add_product": "＋ Add a product",
        "action.new_sale": "💶 Register a sale",
        "action.new_expense": "💸 Add an expense",
        "action.cancel": "Cancel",
        "action.save": "Save",
        "action.confirm": "Confirm",
        "action.edit": "Edit",
        "action.restock": "Restock",
        "action.delete": "Delete",
        "action.copy": "Copy",
        "confirm.delete": "Delete “%(name)s”?",

        # Status badges
        "status.ok": "In stock",
        "status.low": "Low stock",
        "status.out": "Out of stock",
        "in.stock": "in stock",

        # Dashboard
        "dashboard.title": "Dashboard",
        "kpi.total_sales": "Total sales",
        "kpi.profit": "Profit",
        "kpi.total_expenses": "Total expenses",
        "kpi.operating": "Operating expenses",
        "kpi.units_stock": "Units in stock",
        "kpi.units_sold": "Units sold",
        "kpi.total_discounts": "Total discounts given",
        "kpi.margin": "Gross margin / unit sold",
        "chart.line_title": "Sales – last 30 days",
        "chart.doughnut_title": "Stock by status",
        "chart.bar_title": "Sales vs expenses vs profit (by month)",
        "chart.top_title": "Top sellers (quantity)",
        "chart.sales": "Sales (€)",
        "chart.revenue": "Sales",
        "chart.expenses": "Expenses",
        "chart.profit": "Profit",
        "chart.qty_sold": "Qty sold",
        "alerts.title": "Stock alerts",
        "alerts.none": "No alerts: stock levels are sufficient.",

        # Products
        "products.title": "Products",
        "search.placeholder": "Search by name…",
        "products.all_categories": "All categories",
        "products.all_status": "All statuses",
        "products.photo": "Photo",
        "products.name": "Name",
        "products.category": "Category",
        "products.buy_price": "Buy price",
        "products.sale_price": "Sale price",
        "products.stock": "Stock",
        "products.status": "Status",
        "products.actions": "Actions",
        "products.empty": "No products found.",
        "restock.title": "Restock",
        "restock.quantity": "Added quantity",
        "restock.current": "Current stock:",

        # Product form
        "product_form.new": "Add a product",
        "product_form.edit": "Edit the product",
        "product_form.name": "Name (unique) *",
        "product_form.category": "Category",
        "product_form.category_ph": "e.g. DIY, Electronics…",
        "product_form.description": "Description (optional)",
        "product_form.description_hint": "Free text — emojis and line breaks are kept. One click copies it, ready to post.",
        "product_form.buy": "Unit purchase price (€) *",
        "product_form.sale": "Unit sale price (€) *",
        "product_form.threshold": "Low-stock threshold",
        "product_form.threshold_hint": "Below this threshold the badge turns “Low stock”.",
        "product_form.initial_stock": "Initial stock",
        "product_form.initial_stock_hint": "Recorded as a purchase (stock stays derived).",
        "product_form.image": "Image (jpg / png / webp, max 5 MB)",

        # Sales
        "sales.title": "Sales history",
        "sales.new": "💶 New sale",
        "sales.total_received": "Total received (active sales):",
        "sales.from": "From",
        "sales.to": "To",
        "sales.product": "Product",
        "sales.all_products": "All products",
        "sales.date": "Date",
        "sales.qty": "Qty",
        "sales.list_price": "List price",
        "sales.charged": "Charged price",
        "sales.discount": "Discount",
        "sales.total": "Total",
        "sales.profit": "Profit",
        "sales.status": "Status",
        "sales.refunded": "Refunded",
        "sales.void": "Refund",
        "sales.confirm_void": "Refund this sale?",
        "sales.empty": "No sales recorded.",

        # Sale form
        "sale_form.title": "Register a sale",
        "sale_form.product": "Product *",
        "sale_form.choose": "— Choose a product —",
        "sale_form.quantity": "Quantity *",
        "sale_form.stock_available": "Available stock:",
        "sale_form.list_price": "List price",
        "sale_form.charged": "Charged price / unit (€) *",
        "sale_form.discount_label": "Discount:",
        "sale_form.reduction": "% off",
        "sale_form.total": "Total charged:",
        "sale_form.submit": "💶 Confirm sale",
        "sale_form.qty_exceeds": "Quantity exceeds the available stock (%(n)s).",
        "sale_form.placeholder": "0.00",

        # Expenses
        "expenses.title": "Expenses (operating costs)",
        "expenses.total": "Displayed total:",
        "expenses.description": "Description",
        "expenses.amount": "Amount",
        "expenses.empty": "No expenses recorded.",
        "expense_form.title": "Add an expense",
        "expense_form.hint": "Shipping, packaging, delivery… an expense is not a product: it affects neither stock nor the product list.",
        "expense_form.date": "Date *",
        "expense_form.description": "Description *",
        "expense_form.desc_ph": "e.g. Parcel delivery, packaging…",
        "expense_form.amount": "Amount (€) *",

        # Export
        "export.title": "Export data",
        "export.intro": "Back up your data in the familiar layout: the legacy sheet (rows + a “Totaux” line), sales history with the Discount column, and the expenses sheet.",
        "export.xlsx": "📗 Full Excel workbook",
        "export.xlsx_desc": "A workbook with 3 sheets: Sheet 1 (legacy layout + totals), Sales, Expenses.",
        "export.download_xlsx": "Download the XLSX",
        "export.csv": "📄 CSV files",
        "export.csv_desc": "One CSV per sheet, compatible with the legacy spreadsheet.",
        "export.csv_fe11": "Sheet 1 (CSV)",
        "export.csv_sales": "Sales (CSV)",
        "export.csv_expenses": "Expenses (CSV)",

        # Error
        "error.404": "Page not found.",
        "error.413": "File too large (max 5 MB).",
        "error.generic": "An error occurred.",
        "error.oops": "Oops!",
        "error.back": "Back to dashboard",

        # Login
        "login.title": "Sign in",
        "login.username": "Username",
        "login.password": "Password",
        "login.submit": "Sign in",
        "login.cancel": "Cancel",

        # Flash messages (Python-side)
        "flash.product_added": "Product added.",
        "flash.product_updated": "Product updated.",
        "flash.product_deleted": "Product deleted (sales history is kept).",
        "flash.restock": "Restocked %(qty)s unit(s).",
        "flash.invalid_qty": "Invalid quantity.",
        "flash.product_not_found": "Product not found.",
        "flash.invalid_qty_min": "Invalid quantity (must be ≥ 1).",
        "flash.stock_insufficient": "Insufficient stock: %(stock)s unit(s) available.",
        "flash.invalid_charged": "Invalid charged price (must be ≥ 0).",
        "flash.charged_above": "The charged price cannot exceed the list price (%(price)s €).",
        "flash.sale_discounted": "Sale recorded with a discount.",
        "flash.sale_ok": "Sale recorded.",
        "flash.voided": "Sale refunded: stock restored, sale removed from totals.",
        "flash.desc_required": "Description is required.",
        "flash.invalid_amount": "Invalid amount (must be ≥ 0).",
        "flash.invalid_date": "Invalid date.",
        "flash.expense_added": "Expense recorded.",
        "flash.login_success": "Signed in successfully.",
        "flash.login_failed": "Invalid username or password.",
        "flash.logout_success": "You have been signed out.",

        # Validation returns (product form)
        "err.name_required": "The product name is required.",
        "err.buy_price": "Invalid purchase price (must be ≥ 0).",
        "err.sale_price": "Invalid sale price (must be ≥ 0).",
        "err.threshold": "Invalid low-stock threshold.",
        "err.name_exists": "A product named “%(name)s” already exists.",
        "err.image_format": "Unsupported image format (jpg, png, webp only).",
        "err.image_mime": "The uploaded file is not an image.",
        "err.image_big": "Image too large (max 5 MB).",
    },
}