/**
 * Smart Inventory System - Dynamic Line Items & Live Calculation (POS & Purchases)
 */

function initOrderBuilder(mode = 'sale') {
  const tableBody = document.getElementById('order-items-body');
  const addRowBtn = document.getElementById('add-item-btn');
  const subtotalEl = document.getElementById('calc-subtotal');
  const grandTotalEl = document.getElementById('calc-grand-total');
  const discountInput = document.getElementById('calc-discount');
  const taxInput = document.getElementById('calc-tax');
  const shippingInput = document.getElementById('calc-shipping');

  if (!tableBody || !addRowBtn) return;

  function recalculateTotals() {
    let subtotal = 0;
    const rows = tableBody.querySelectorAll('tr.item-row');

    rows.forEach(row => {
      const qtyInput = row.querySelector('.item-qty');
      const priceInput = row.querySelector('.item-price');
      const totalEl = row.querySelector('.item-line-total');

      const qty = parseFloat(qtyInput.value) || 0;
      const price = parseFloat(priceInput.value) || 0;
      const lineTotal = qty * price;

      if (totalEl) {
        totalEl.textContent = '₹' + lineTotal.toFixed(2);
      }
      subtotal += lineTotal;
    });

    if (subtotalEl) {
      subtotalEl.textContent = '₹' + subtotal.toFixed(2);
    }

    const discount = parseFloat(discountInput ? discountInput.value : 0) || 0;
    const tax = parseFloat(taxInput ? taxInput.value : 0) || 0;
    const shipping = parseFloat(shippingInput ? shippingInput.value : 0) || 0;

    const grandTotal = Math.max(0, subtotal - discount + tax + shipping);
    if (grandTotalEl) {
      grandTotalEl.textContent = '₹' + grandTotal.toFixed(2);
    }
  }

  // Row event delegation
  tableBody.addEventListener('input', function (e) {
    if (e.target.classList.contains('item-qty') || e.target.classList.contains('item-price')) {
      recalculateTotals();
    }
  });

  tableBody.addEventListener('change', function (e) {
    if (e.target.classList.contains('item-product-select')) {
      const selectedOption = e.target.options[e.target.selectedIndex];
      const row = e.target.closest('tr');
      const priceInput = row.querySelector('.item-price');
      const stockBadge = row.querySelector('.item-stock-badge');
      const qtyInput = row.querySelector('.item-qty');

      if (selectedOption && selectedOption.value !== '') {
        const price = selectedOption.getAttribute('data-price') || 0;
        const stock = parseInt(selectedOption.getAttribute('data-stock') || 0);

        if (priceInput) priceInput.value = parseFloat(price).toFixed(2);

        if (stockBadge) {
          stockBadge.textContent = `${stock} available`;
          if (stock <= 0) {
            stockBadge.className = 'item-stock-badge badge bg-danger';
          } else if (stock <= 5) {
            stockBadge.className = 'item-stock-badge badge bg-warning text-dark';
          } else {
            stockBadge.className = 'item-stock-badge badge bg-success';
          }
        }

        if (mode === 'sale') {
          qtyInput.max = stock;
          if (stock <= 0) {
            alert('Warning: Selected product is currently out of stock!');
          }
        }
      }
      recalculateTotals();
    }
  });

  tableBody.addEventListener('click', function (e) {
    const removeBtn = e.target.closest('.remove-row-btn');
    if (removeBtn) {
      const rows = tableBody.querySelectorAll('tr.item-row');
      if (rows.length > 1) {
        removeBtn.closest('tr').remove();
        recalculateTotals();
      } else {
        alert('You must maintain at least one item row in the order.');
      }
    }
  });

  // Add Item Row
  addRowBtn.addEventListener('click', function () {
    const firstRow = tableBody.querySelector('tr.item-row');
    const newRow = firstRow.cloneNode(true);

    // Reset inputs
    const select = newRow.querySelector('.item-product-select');
    select.selectedIndex = 0;
    const qtyInput = newRow.querySelector('.item-qty');
    qtyInput.value = 1;
    const priceInput = newRow.querySelector('.item-price');
    priceInput.value = '0.00';
    const totalEl = newRow.querySelector('.item-line-total');
    if (totalEl) totalEl.textContent = '₹0.00';
    const stockBadge = newRow.querySelector('.item-stock-badge');
    if (stockBadge) {
      stockBadge.textContent = '-';
      stockBadge.className = 'item-stock-badge badge bg-secondary';
    }

    tableBody.appendChild(newRow);
    recalculateTotals();
  });

  // Listeners for discount, tax, shipping inputs
  if (discountInput) discountInput.addEventListener('input', recalculateTotals);
  if (taxInput) taxInput.addEventListener('input', recalculateTotals);
  if (shippingInput) shippingInput.addEventListener('input', recalculateTotals);

  // Initial calculation
  recalculateTotals();
}
