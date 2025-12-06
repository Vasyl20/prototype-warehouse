let productsData = [];
let operationsData = [];
let suppliersData = [];
let clientsData = [];

// Завантаження товарів
async function loadProducts() {
  try {
    const res = await fetch('/products');
    productsData = await res.json();
    populateProductSelects();
  } catch (error) {
    console.error('Помилка завантаження товарів:', error);
    alert('Помилка завантаження товарів!');
  }
}

// Завантаження постачальників
async function loadSuppliers() {
  try {
    const res = await fetch('/api/suppliers');
    suppliersData = await res.json();
    populateSupplierSelect();
  } catch (error) {
    console.error('Помилка завантаження постачальників:', error);
  }
}

// Завантаження клієнтів
async function loadClients() {
  try {
    const res = await fetch('/api/clients');
    clientsData = await res.json();
    populateClientSelect();
  } catch (error) {
    console.error('Помилка завантаження клієнтів:', error);
  }
}

// Завантаження операцій
async function loadOperations() {
  try {
    const res = await fetch('/api/operations');

    if (!res.ok) {
      console.error('Помилка отримання операцій:', res.status);
      operationsData = [];
      renderOperationsTable();
      return;
    }

    operationsData = await res.json();
    console.log('Завантажено операцій:', operationsData.length);
    renderOperationsTable();
  } catch (error) {
    console.error('Помилка завантаження операцій:', error);
    operationsData = [];
    renderOperationsTable();
  }
}

// Заповнення випадаючих списків товарами
function populateProductSelects() {
  const incomeSelect = document.getElementById('incomeProduct');
  const outcomeSelect = document.getElementById('outcomeProduct');

  incomeSelect.innerHTML = '<option value="">Виберіть товар...</option>';
  outcomeSelect.innerHTML = '<option value="">Виберіть товар...</option>';

  productsData.forEach(p => {
    const displayText = `${p.name} ${p.number ? '| №' + p.number : ''} | Залишок: ${p.quantity || 0}`;

    const option1 = document.createElement('option');
    option1.value = p.id;
    option1.textContent = displayText;

    const option2 = document.createElement('option');
    option2.value = p.id;
    option2.textContent = displayText;

    incomeSelect.appendChild(option1);
    outcomeSelect.appendChild(option2);
  });
}

// Заповнення списку постачальників
function populateSupplierSelect() {
  const select = document.getElementById('incomeSupplier');
  select.innerHTML = '<option value="">Виберіть постачальника...</option>';

  suppliersData.forEach(s => {
    const option = document.createElement('option');
    option.value = s.id;
    option.textContent = `${s.name} ${s.contact_person ? '(' + s.contact_person + ')' : ''}`;
    select.appendChild(option);
  });
}

// Заповнення списку клієнтів
function populateClientSelect() {
  const select = document.getElementById('outcomeClient');
  select.innerHTML = '<option value="">Виберіть клієнта...</option>';

  clientsData.forEach(c => {
    const option = document.createElement('option');
    option.value = c.id;
    option.textContent = `${c.name} ${c.contact_person ? '(' + c.contact_person + ')' : ''}`;
    select.appendChild(option);
  });
}

// Відображення таблиці операцій
function renderOperationsTable() {
  const table = document.getElementById('operationsTable');
  table.innerHTML = '';

  if (operationsData.length === 0) {
    table.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Операцій поки немає</td></tr>';
    return;
  }

  operationsData.forEach(op => {
    const row = document.createElement('tr');
    const typeClass = op.type === 'income' ? 'text-success' : 'text-warning';
    const typeText = op.type === 'income' ? '➕ Надходження' : '➖ Відпуск';

    const productDisplay = op.product_number
      ? `${op.product_name} | №${op.product_number}`
      : op.product_name;

    // Відображаємо контрагента та номер накладної
    let counterparty = '—';
    if (op.type === 'income' && op.supplier_name) {
      counterparty = `📦 ${op.supplier_name}`;
    } else if (op.type === 'outcome' && op.client_name) {
      counterparty = `👤 ${op.client_name}`;
    }

    const invoice = op.invoice_number ? `📄 ${op.invoice_number}` : '—';

    row.innerHTML = `
      <td>${op.date}</td>
      <td>${op.time}</td>
      <td class="${typeClass}"><strong>${typeText}</strong></td>
      <td>${productDisplay}</td>
      <td>${op.quantity}</td>
      <td><small>${counterparty}<br>${invoice}</small></td>
    `;

    table.appendChild(row);
  });
}

// Додавання надходження
async function addIncome() {
  const productId = document.getElementById('incomeProduct').value;
  const quantity = parseInt(document.getElementById('incomeQty').value);
  const date = document.getElementById('incomeDate').value;
  const supplierId = document.getElementById('incomeSupplier').value;
  const invoiceNumber = document.getElementById('incomeInvoice').value.trim();

  if (!productId) {
    alert('Виберіть товар!');
    return;
  }

  if (!quantity || quantity <= 0) {
    alert('Введіть коректну кількість!');
    return;
  }

  if (!date) {
    alert('Виберіть дату!');
    return;
  }

  if (!supplierId) {
    alert('Виберіть постачальника!');
    return;
  }

  try {
    const res = await fetch('/operations/income', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_id: productId,
        quantity,
        date,
        supplier_id: supplierId,
        invoice_number: invoiceNumber
      })
    });

    if (res.ok) {
      alert('✅ Надходження успішно додано!');
      document.getElementById('incomeQty').value = '';
      document.getElementById('incomeProduct').value = '';
      document.getElementById('incomeSupplier').value = '';
      document.getElementById('incomeInvoice').value = '';
      setTodayDate();
      await loadProducts();
      await loadOperations();
    } else {
      const err = await res.json();
      alert('❌ Помилка: ' + err.error);
    }
  } catch (error) {
    console.error('Помилка:', error);
    alert('Помилка додавання надходження!');
  }
}

// Додавання відпуску
async function addOutcome() {
  const productId = document.getElementById('outcomeProduct').value;
  const quantity = parseInt(document.getElementById('outcomeQty').value);
  const date = document.getElementById('outcomeDate').value;
  const clientId = document.getElementById('outcomeClient').value;
  const invoiceNumber = document.getElementById('outcomeInvoice').value.trim();

  if (!productId) {
    alert('Виберіть товар!');
    return;
  }

  if (!quantity || quantity <= 0) {
    alert('Введіть коректну кількість!');
    return;
  }

  if (!date) {
    alert('Виберіть дату!');
    return;
  }

  if (!clientId) {
    alert('Виберіть клієнта!');
    return;
  }

  // Перевірка наявності товару
  const product = productsData.find(p => p.id == productId);
  if (!product || product.quantity < quantity) {
    alert(`❌ Недостатньо товару на складі! Доступно: ${product?.quantity || 0}`);
    return;
  }

  try {
    const res = await fetch('/operations/outcome', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_id: productId,
        quantity,
        date,
        client_id: clientId,
        invoice_number: invoiceNumber
      })
    });

    if (res.ok) {
      alert('✅ Відпуск успішно виконано!');
      document.getElementById('outcomeQty').value = '';
      document.getElementById('outcomeProduct').value = '';
      document.getElementById('outcomeClient').value = '';
      document.getElementById('outcomeInvoice').value = '';
      setTodayDate();
      await loadProducts();
      await loadOperations();
    } else {
      const err = await res.json();
      alert('❌ Помилка: ' + err.error);
    }
  } catch (error) {
    console.error('Помилка:', error);
    alert('Помилка виконання відпуску!');
  }
}

// Вихід з системи
async function logout() {
  try {
    await fetch('/logout', { method: 'POST' });
    window.location.href = '/login';
  } catch (error) {
    console.error('Помилка виходу:', error);
    window.location.href = '/login';
  }
}

// Встановлення сьогоднішньої дати
function setTodayDate() {
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('incomeDate').value = today;
  document.getElementById('outcomeDate').value = today;
}

// Ініціалізація
window.addEventListener('load', function() {
  console.log('Завантаження сторінки операцій...');
  setTodayDate();

  document.getElementById('addIncomeBtn').addEventListener('click', addIncome);
  document.getElementById('addOutcomeBtn').addEventListener('click', addOutcome);
  document.getElementById('logoutBtn').addEventListener('click', logout);

  loadProducts();
  loadSuppliers();
  loadClients();
  loadOperations();
});