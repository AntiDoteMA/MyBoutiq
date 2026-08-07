# Boutique Manager

Application web de gestion de boutique : produits (avec photos), stock, ventes avec
remises, dépenses, tableau de bord et exports — **sécurisée par une connexion** et
**bilingue FR / EN**. Elle remplace l'ancien tableau Excel et fonctionne en **local**
(double-clic sur `run.bat`, aucune configuration) ou **en ligne** (hébergement gratuit
sur PythonAnywhere, photos servies depuis le CDN ImageKit).

## 📝 Licence

C'est juste un petit projet sympa fait pour dépanner un ami. **Aucune licence, aucune
restriction** — chacun est libre de l'utiliser, de le modifier ou d'en faire ce qu'il
veut. 😄

## 🚀 Démarrage (utilisateur)

1. Double-cliquez sur **`run.bat`**.
2. Le navigateur s'ouvre sur `http://127.0.0.1:5000` → page de connexion.
3. Connectez-vous avec le compte par défaut : **admin / admin123**.
4. **Changez immédiatement le mot de passe** : bouton **« Compte »** dans la barre de navigation.

Aucune configuration : Python 3.11 suffit. Au premier lancement, la base est créée et
l'ancien tableau est **importé automatiquement** (`Copy of WS'Shop.xlsx` ou son export CSV).

## 🔑 Connexion & sécurité

- Toutes les pages (sauf la connexion) exigent d'être connecté.
- Mots de passe stockés **hachés** (`werkzeug.security`).
- **Protection CSRF** sur tous les formulaires (jetons Flask-WTF).
- Redirection `next=` limitée aux chemins internes (pas d'open redirect).
- En production, définissez **`SECRET_KEY`** dans l'environnement (sessions + jetons CSRF).

## 📦 Fonctionnalités

- **Tableau de bord** : ventes, bénéfice, dépenses (produits + frais), stock, remises
  données ; graphiques (ventes 30 jours, ventes/dépenses/bénéfice par mois, meilleures
  ventes, stock par statut) ; alertes stock bas / rupture.
- **Produits** : photo (jpg/png/webp ≤ 5 Mo), **description de publication** (emojis et
  sauts de ligne conservés, bouton **📋 Copier** pour Facebook), catégorie (suggestions),
  recherche / filtres / tri, réapprovisionnement, **suppression douce** (l'historique des
  ventes est conservé). Le stock est **toujours calculé** (achetés − vendus + remboursés).
- **Ventes** : prix de liste affiché, **prix facturé modifiable (remise)** avec badge
  « Remise € / % » en direct, blocage si quantité > stock, **remboursement/annulation**
  (restaure le stock et retire la vente des totaux).
- **Dépenses** : journal simple (date, description, montant) pour les frais opérationnels
  — jamais confondues avec des produits.
- **Compte** : page « Modifier le mot de passe » (mot de passe actuel + nouveau + confirmation).
- **Export** : XLSX (3 feuilles) ou CSV, dans la présentation de l'ancien tableau
  (ligne « Totaux » incluse), + feuille Ventes avec la colonne Remise + feuille Dépenses.
- **Bilingue FR / EN** : bascule **FR | EN** dans la barre de navigation (choix mémorisé
  par cookie), formats € et dates adaptés. Le français reste la langue par défaut.

## 🔄 Import initial (données existantes)

`seed.py` lit l'ancien tableau (XLSX de préférence, sinon CSV) :
- lignes avec un **prix de vente** → 1 produit par ligne (`Produit 1`, `Produit 2`, …) ;
- lignes avec « – » en prix de vente (transport, emballage, livraison…) → **dépenses** ;
- la ligne parasite (72,00 €) est importée comme 7ᵉ dépense (nécessaire pour le total).

Résultat vérifié sur les données réelles : **57 produits + 7 frais**, ventes **814,99 €**,
dépenses **724,32 €** (594,44 € d'achats + 129,88 € de frais), **stock dérivé 76**.

Écart volontaire avec les chiffres imprimés de l'ancien tableau (détails dans `seed.py`) :
- « 183 achetés / 102 vendus » comptait **aussi les lignes de frais** ; l'application
  affiche donc 174/98 avec un stock dérivé de **76** (= « restants ») ;
- « Bénéfices **215,68 €** » → le résultat réel est **90,67 €** (814,99 − 724,32), valeur
  qui figurait d'ailleurs dans le CSV source.

Ré-import : `python seed.py --reset` (supprime toutes les données puis ré-importe).
Les dates des ventes importées sont **étalées** sur les ~30 derniers jours (déterministe)
pour que le graphique « 30 jours » soit lisible ; `backfill_dates.py` fait de même sur une
base existante (ne touche qu'à `created_at`/`date`).

## 🌐 Déploiement (PythonAnywhere, gratuit)

Pour **chaque** déploiement (vous, votre ami…), il faut un compte gratuit différent et des
**clés ImageKit personnelles**.

1. Compte gratuit sur `pythonanywhere.com` + compte ImageKit (plan gratuit).
2. Récupérez les 4 valeurs ImageKit (`IMAGEKIT_PRIVATE_KEY`, `IMAGEKIT_PUBLIC_KEY`,
   `IMAGEKIT_URL_ENDPOINT`, `IMAGEKIT_ID`).
3. Téléversez le projet (Files ou Git), **sans** `data/` ni `.env`.
4. Console bash : `pip install --user -r requirements.txt`.
5. Fichier `.env` à la racine (ou Web → Environment variables) :
   ```
   IMAGEKIT_PRIVATE_KEY=...
   IMAGEKIT_PUBLIC_KEY=...
   IMAGEKIT_URL_ENDPOINT=...
   IMAGEKIT_ID=...
   SECRET_KEY=<chaîne aléatoire longue>
   ```
6. **Web → WSGI configuration file** :
   ```python
   from app import create_app
   application = create_app()
   ```
7. Rechargez le site, connectez-vous avec **admin / admin123**, puis changez le mot de
   passe via **« Compte »**.
8. (Facultatif) `python seed.py` pour importer l'ancien tableau.

**Sécurité :** ne partagez jamais `IMAGEKIT_PRIVATE_KEY` ni `SECRET_KEY`. Changez le mot de
passe initial dès la première connexion. Chaque compte possède son propre `data/shop.db`.

## 🛠 Notes développeur

- **Stack** : Python 3.11, Flask (server-rendered), SQLite via SQLAlchemy,
  Bootstrap 5 + Chart.js **vendored** dans `static/vendor/` (offline),
  pandas + openpyxl (import/export), Flask-WTF (CSRF), ImageKit SDK (photos CDN).
- **i18n** : dictionnaires dans `i18n.py` (`STRINGS["fr"]` / `STRINGS["en"]`) ;
  templates `{{ _("key") }}`, messages Python `_t("key", ...)`, filtres `eur`/`dte`
  adaptés à la langue, `GET /lang/<code>` (cookie). Ajouter une langue = nouveau dict +
  code dans `LANGUAGES`. Les en-têtes d'export restent en français (format familier).
- **Migrations** : `db.create_all()` + `_migrate_schema()` ajoute les nouvelles colonnes
  (ex. `products.description`) de façon idempotente (`ALTER TABLE ... ADD COLUMN`).
- **Dates de démo** : `seed.py` étale les dates importées sur ~30 jours (`_spread`) ;
  `backfill_dates.py` ré-étale une base existante.
- **Données** : `data/shop.db` (SQLite, WAL). Stock dérivé des `stock_transactions`
  (achat/restock +, vente −, remboursement +). Revenu et profit calculés sur le **prix
  facturé** ; remise = liste − facturé. Suppression douce : `is_deleted`, snapshots.
- **Serveur** : `python app.py` → http://127.0.0.1:5000 (localhost uniquement).
- **Tests** : `python tests_acceptance.py` (client de test Flask sur une base jetable).

## Structure

```
Bilal/
  PRD.md, PRD-v2.md, README.md, EN_README.md, requirements.txt
  app.py, models.py, i18n.py, seed.py, export.py, backfill_dates.py, run.bat
  tests_acceptance.py
  data/            # shop.db (créé au premier lancement)
  static/          # css, js, vendor (Bootstrap/Chart.js offline), uploads
  templates/       # Jinja2 (FR/EN via i18n.py)
```