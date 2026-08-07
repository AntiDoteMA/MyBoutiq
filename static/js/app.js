/**
 * MyBoutiq - frontend behaviour (offline, no CDN).
 * - Confirm dialogs for destructive forms
 * - Restock modal wiring
 * - Product table column sorting
 * - Live discount badge + totals on the sale form
 */

document.addEventListener('DOMContentLoaded', function () {
  /* ---- Confirm destructive actions ---- */
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!window.confirm(form.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  /* ---- Copy-to-clipboard (product description) ---- */
  document.querySelectorAll('.btn-copy-desc').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const el = document.getElementById('productDescription');
      if (!el) return;
      const done = function () {
        const old = btn.textContent;
        btn.textContent = '✓';
        setTimeout(function () { btn.textContent = old; }, 1200);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(el.value).then(done, done);
      } else {
        el.select();
        try { document.execCommand('copy'); } catch (e) { /* ignore */ }
        done();
      }
    });
  });

  /* ---- Product table sorting ---- */
  document.querySelectorAll('.sort-link').forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const params = new URLSearchParams(window.location.search);
      const sort = link.dataset.sort;
      let order = 'asc';
      if (params.get('sort') === sort && params.get('order') === 'asc') {
        order = 'desc';
      }
      params.set('sort', sort);
      params.set('order', order);
      window.location.search = params.toString();
    });
  });

  /* ---- Restock modal ---- */
  const modalEl = document.getElementById('restockModal');
  const restockForm = document.getElementById('restockForm');
  if (modalEl && restockForm) {
    const modal = new bootstrap.Modal(modalEl);
    document.querySelectorAll('.btn-restock').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const label = (window.I18N && window.I18N.restock_current) || '';
        document.getElementById('restockName').textContent =
          btn.dataset.name + ' — ' + label + ' ' + btn.dataset.stock;
        restockForm.action = '/products/' + btn.dataset.id + '/restock';
        modal.show();
      });
    });
  }

  /* ---- Sale form: live discount + totals ---- */
  const productSel = document.getElementById('saleProduct');
  if (productSel) {
    const qty = document.getElementById('saleQty');
    const stockEl = document.getElementById('saleStock');
    const listEl = document.getElementById('saleList');
    const charged = document.getElementById('saleCharged');
    const panel = document.getElementById('remisePanel');
    const remiseAmt = document.getElementById('remiseAmount');
    const remisePct = document.getElementById('remisePercent');
    const totalEl = document.getElementById('saleTotal');

    let listPrice = 0;
    let maxStock = 0;

    function currentOption() {
      return productSel.options[productSel.selectedIndex];
    }

    function fmt(v) {
      const loc = (window.I18N && window.I18N.locale === 'en') ? 'en' : 'fr';
      const lc = loc === 'en' ? 'en-GB' : 'fr-FR';
      const sym = loc === 'en' ? '€' : ' €';
      return v.toLocaleString(lc, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + sym;
    }

    function update() {
      const c = parseFloat(String(charged.value).replace(',', '.'));
      const q = parseInt(qty.value, 10);
      const okQty = !isNaN(q) && q > 0 && q <= maxStock;
      const okPrice = !isNaN(c) && c >= 0 && c <= listPrice;

      // Live remise badge
      if (!isNaN(c) && c < listPrice && c >= 0) {
        panel.classList.remove('d-none');
        remiseAmt.textContent = fmt(listPrice - c);
        remisePct.textContent = ((listPrice - c) / listPrice * 100).toLocaleString('fr-FR', { maximumFractionDigits: 2 });
      } else {
        panel.classList.add('d-none');
      }

      // Total encaisse
      if (okPrice && okQty) {
        totalEl.textContent = fmt(c * q);
      } else {
        totalEl.textContent = '—';
      }

      // Stock warning (server also validates)
      const warning = document.getElementById('saleStockWarning');
      if (warning) {
        warning.classList.toggle('d-none', !(!isNaN(q) && q > maxStock));
        const base = (window.I18N && window.I18N.qty_exceeds) || '';
        warning.textContent = base.replace(/%\(n\)s/g, String(maxStock));
      }
    }

    productSel.addEventListener('change', function () {
      const opt = currentOption();
      if (opt.value) {
        listPrice = parseFloat(opt.dataset.price);
        maxStock = parseInt(opt.dataset.stock, 10);
        stockEl.textContent = maxStock;
        listEl.value = fmt(listPrice);
        charged.value = listPrice;
      } else {
        listPrice = 0; maxStock = 0;
        stockEl.textContent = '—';
        listEl.value = '—';
        charged.value = '';
      }
      update();
    });

    qty.addEventListener('input', update);
    charged.addEventListener('input', update);
  }
});