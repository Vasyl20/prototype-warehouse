let productsData = [];
let operationsData = [];

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

// Завантаження операцій
async function loadOperations() {
  try {
    const res = await fetch('/operations');
    operationsData = await res.json();
    renderOperationsTable();
  } catch (error) {
    console.error('Помилка завантаження операцій:', error);
  }
}

// Заповнення випадаючих списків товарами
function populateProductSelects() {
  const incomeSelect = document.getElementById('incomeProduct');
  const outcomeSelect = document.getElementById('outcomeProduct');
  
  // Очищаємо списки
  incomeSelect.innerHTML = '<option value="">Виберіть товар...</option>';
  outcomeSelect.innerHTML = '<option value="">Виберіть товар...</option>';
  
  // Додаємо товари
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

// Відображення таблиці операцій
function renderOperationsTable() {
  const table = document.getElementById('operationsTable');
  table.innerHTML = '';
  
  if (operationsData.length === 0) {
    table.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Операцій поки немає</td></tr>';
    return;
  }
  
  operationsData.forEach(op => {
    const row = document.createElement('tr');
    const typeClass = op.type === 'income' ? 'text-success' : 'text-warning';
    const typeText = op.type === 'income' ? '➕ Надходження' : '➖ Відпуск';
    
    row.innerHTML = `
      <td>${op.date}</td>
      <td>${op.time}</td>
      <td class="${typeClass}"><strong>${typeText}</strong></td>
      <td>${op.product_name}</td>
      <td>${op.quantity}</td>
    `;
    
    table.appendChild(row);
  });
}

// Додавання надходження
async function addIncome() {
  const productId = document.getElementById('incomeProduct').value;
  const quantity = parseInt(document.getElementById('incomeQty').value);
  const date = document.getElementById('incomeDate').value;
  
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
  
  try {
    const res = await fetch('/operations/income', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, quantity, date })
    });
    
    if (res.ok) {
      alert('✅ Надходження успішно додано!');
      document.getElementById('incomeQty').value = '';
      document.getElementById('incomeProduct').value = '';
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
      body: JSON.stringify({ product_id: productId, quantity, date })
    });
    
    if (res.ok) {
      alert('✅ Відпуск успішно виконано!');
      document.getElementById('outcomeQty').value = '';
      document.getElementById('outcomeProduct').value = '';
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
  setTodayDate();
  
  document.getElementById('addIncomeBtn').addEventListener('click', addIncome);
  document.getElementById('addOutcomeBtn').addEventListener('click', addOutcome);
  document.getElementById('logoutBtn').addEventListener('click', logout);
  
  loadProducts();
  loadOperations();
});