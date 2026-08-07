# Boutique Manager

Application web **locale** de gestion de boutique (produits, stock, ventes avec remises,
dépenses, tableaux de bord). Remplace le tableau Excel actuel.

## 🚀 Démarrage (utilisateur)

1. Double-cliquez sur **`run.bat`**.
2. Le navigateur s'ouvre sur `http://127.0.0.1:5000`.
3. Au premier lancement, l'application crée la base et **importe automatiquement**
   le fichier existant (`Copy of WS'Shop.xlsx` ou son export CSV).

Aucune configuration : Python 3.11 suffit. Les dépendances sont installées
automatiquement au premier lancement (une connexion Internet est alors nécessaire).

## 📦 Fonctionnalités

- **Tableau de bord** : ventes, bénéfice, dépenses (produits + frais), stock,
  remises données ; graphiques (ventes 30 jours, ventes/dépenses/bénéfice par mois,
  meilleures ventes, stock par statut) ; alertes stock bas / rupture.
- **Produits** : ajout avec photo (jpg/png/webp ≤ 5 Mo), **description de publication**
  (texte libre, emojis et sauts de ligne conservés, bouton « Copier » pour Facebook),
  catégorie (suggestions),
  recherche / filtres / tri, réapprovisionnement, suppression douce
  (l'historique des ventes est conservé). Le stock est **toujours calculé**
  (achetés − vendus + remboursés), jamais saisi à la main.
- **Ventes** : sélection du produit, prix de liste affiché, **prix facturé modifiable
  (remise)** avec badge « Remise € / % » en direct, blocage si quantité > stock,
  remboursement/annulation (restaure le stock et retire la vente des totaux).
- **Dépenses** : journal simple (date, description, montant) pour les frais
  opérationnels — jamais confondues avec des produits.
- **Export** : XLSX (3 feuilles) ou CSV, dans la présentation de l'ancien tableau
  (ligne « Totaux » incluse), + feuille Ventes avec la colonne Remise + feuille Dépenses.
- **Bilingue FR / EN** : bascule **FR | EN** dans la barre de navigation, choix mémorisé
  (cookie), formats € et dates adaptés à la langue. Le français reste la langue par défaut.

## 🔄 Import initial (données existantes)

`seed.py` lit l'ancien tableau (XLSX de préférence, sinon CSV) :
- lignes avec un **prix de vente** → 1 produit par ligne (`Produit 1`, `Produit 2`, …) ;
- lignes avec « – » en prix de vente (transport, emballage, livraison…) → **dépenses** ;
- la ligne parasite de l'ancien fichier (72,00 €) est importée comme 7ᵉ dépense,
  indispensable pour reproduire le total des dépenses.

Résultat vérifié sur les données réelles : 63 lignes réelles → **57 produits + 6 frais**
(+ 1 ligne parasite en frais), ventes **814,99 €**, dépenses **724,32 €**
(594,44 € d'achats produits + 129,88 € de frais), **stock dérivé 76**
(174 achetés − 98 vendus).

Écart volontaire par rapport aux chiffres imprimés de l'ancien tableau
(expliqué dans `seed.py`) :
- « 183 achetés / 102 vendus » comptait **aussi les lignes de frais** (quantités et
  ventes des lignes transport/livraison) ; ces lignes ne sont pas des produits,
  donc l'application affiche 174/98 et un stock dérivé de **76** (= « restants ») ;
- « Bénéfices **215,68** € » → l'application calcule le résultat réel :
  **90,67 €** (814,99 − 724,32), valeur qui figurait d'ailleurs dans le CSV source.

Ré-import : `python seed.py --reset` (supprime toutes les données puis ré-importe).

## 🛠 Notes développeur (English)

- **Stack** : Python 3.11, Flask (server-rendered), SQLite via SQLAlchemy,
  Bootstrap 5 + Chart.js **vendored locally** in `static/vendor/` (offline),
  pandas + openpyxl for import/export.
- **i18n** : lightweight dictionaries in `i18n.py` (`STRINGS["fr"]` / `STRINGS["en"]`);
  templates use `{{ _("key") }}`, Python-side messages use `_t("key", ...)` (app.py),
  locale-aware `eur`/`dte` Jinja filters, `GET /lang/<code>` sets a `lang` cookie.
  To add a language: add a dict to `STRINGS`, register the code in `LANGUAGES`,
  and add a `?lang=<code>` branch in the `eur`/`dte` filters if the format differs.
  Export file headers stay French on purpose (the familiar spreadsheet layout).
- **Schema migrations** : `db.create_all()` + `_migrate_schema()` in `app.py` adds
  new columns (e.g. `products.description`) to an existing `shop.db` idempotently
  via `ALTER TABLE ... ADD COLUMN` — non-destructive, offline-safe.
- **Demo dates** : the legacy sheet has no real dates, so `seed.py` spreads imported
  sales/purchases/expenses over the last ~30 days (`_spread`, deterministic) instead
  of stamping them all at "now" — otherwise the "last 30 days" dashboard chart is a
  one-day spike. `backfill_dates.py` applies the same re-spread to an existing DB
  (rewrites only `created_at`/`date`; totals, names and snapshots are untouched).
- **Files** : `app.py` (routes + app factory), `models.py` (Product, StockTransaction,
  Sale, Expense), `seed.py` (legacy import), `export.py` (CSV/XLSX export),
  `templates/` (Jinja2, French UI), `static/` (css, js, vendor, uploads).
- **Data** : `data/shop.db` (SQLite, WAL). Stock is derived from
  `stock_transactions` (purchase/restock positive, sale negative, refund positive).
  Revenue and profit always use the **charged** price; discounts = list − charged.
- **Soft-delete** : `products.is_deleted = 1`; sales keep name/price snapshots.
- **Dev server** : `python app.py` → http://127.0.0.1:5000 (localhost only).
- **Tests** : run the acceptance script with `python tests_acceptance.py`
  (uses Flask's test client against a throwaway DB).

## Structure

```
Bilal/
  PRD.md, README.md, requirements.txt
  app.py, models.py, i18n.py, seed.py, export.py, run.bat
  tests_acceptance.py
  data/            # shop.db (created at first run)
  static/          # css, js, vendor (offline Bootstrap/Chart.js), uploads
  templates/       # Jinja2 templates (FR/EN via i18n.py)
```
