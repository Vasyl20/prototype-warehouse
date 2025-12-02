// Зберігаємо поточні дані
let productsData = [];
let operationsData = [];

// Завантаження товарів
async function loadProducts() {
  try {
    const res = await fetch('/products');
    productsData = await res.json();
    updateDashboard();
    showCriticalStock();
  } catch (error) {
    console.error('Помилка завантаження товарів:', error);
  }
}

// Завантаження операцій за сьогодні
async function loadTodayOperations() {
  try {
    const res = await fetch('/api/operations/today');
    
    if (!res.ok) {
      console.error('Помилка отримання операцій:', res.status);
      operationsData = [];
      updateDashboard();
      showRecentOperations();
      return;
    }
    
    operationsData = await res.json();
    updateDashboard();
    showRecentOperations();
    calculateTodayStats();
  } catch (error) {
    console.error('Помилка завантаження операцій:', error);
    operationsData = [];
    updateDashboard();
    showRecentOperations();
  }
}

// Оновлення головних карточок дашборду
function updateDashboard() {
  // Всього товарів
  const totalProducts = productsData.length;
  
  // Загальна вартість залишків
  let totalValue = 0;
  productsData.forEach(p => {
    const quantity = p.quantity || 0;
    const price = p.price || 0;
    totalValue += quantity * price;
  });
  
  // Операцій сьогодні
  const todayOperations = operationsData.length;
  
  // Товарів з нульовим залишком
  let zeroStock = 0;
  productsData.forEach(p => {
    if ((p.quantity || 0) === 0) {
      zeroStock++;
    }
  });
  
  // Оновлюємо карточки
  document.getElementById('totalProducts').textContent = totalProducts;
  document.getElementById('totalValue').textContent = totalValue.toFixed(2) + ' грн';
  document.getElementById('todayOperations').textContent = todayOperations;
  document.getElementById('zeroStock').textContent = zeroStock;
}

// Відображення останніх операцій
function showRecentOperations() {
  const table = document.getElementById('recentOperations');
  table.innerHTML = '';
  
  if (operationsData.length === 0) {
    table.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Операцій сьогодні ще не було</td></tr>';
    return;
  }
  
  // Показуємо останні 10 операцій
  const recent = operationsData.slice(0, 10);
  
  recent.forEach(op => {
    const row = document.createElement('tr');
    const typeText = op.type === 'income' ? '➕' : '➖';
    const typeClass = op.type === 'income' ? 'text-success' : 'text-warning';
    
    row.innerHTML = `
      <td>${op.time}</td>
      <td class="${typeClass}"><strong>${typeText}</strong></td>
      <td>${op.product_name}</td>
      <td><strong>${op.quantity}</strong></td>
    `;
    
    table.appendChild(row);
  });
}

// Відображення товарів з критичним залишком
function showCriticalStock() {
  const table = document.getElementById('criticalStock');
  table.innerHTML = '';
  
  // Фільтруємо товари з залишком <= 5
  const critical = productsData.filter(p => (p.quantity || 0) <= 5);
  
  if (critical.length === 0) {
    table.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Всі товари в достатній кількості ✅</td></tr>';
    return;
  }
  
  // Сортуємо за залишком (найменші зверху)
  critical.sort((a, b) => (a.quantity || 0) - (b.quantity || 0));
  
  // Показуємо перші 10
  critical.slice(0, 10).forEach(p => {
    const row = document.createElement('tr');
    const qtyClass = (p.quantity || 0) === 0 ? 'text-danger' : 'text-warning';
    
    row.innerHTML = `
      <td>${p.name}</td>
      <td>${p.number || '—'}</td>
      <td class="${qtyClass}"><strong>${p.quantity || 0}</strong></td>
    `;
    
    table.appendChild(row);
  });
}

// Розрахунок статистики за сьогодні
function calculateTodayStats() {
  let totalIncome = 0;
  let totalOutcome = 0;
  
  operationsData.forEach(op => {
    if (op.type === 'income') {
      totalIncome += op.quantity;
    } else if (op.type === 'outcome') {
      totalOutcome += op.quantity;
    }
  });
  
  const balance = totalIncome - totalOutcome;
  
  document.getElementById('todayIncome').textContent = totalIncome;
  document.getElementById('todayOutcome').textContent = totalOutcome;
  document.getElementById('todayBalance').textContent = balance;
  
  // Змінюємо колір балансу залежно від значення
  const balanceEl = document.getElementById('todayBalance');
  if (balance > 0) {
    balanceEl.className = 'text-success';
  } else if (balance < 0) {
    balanceEl.className = 'text-danger';
  } else {
    balanceEl.className = 'text-info';
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

// Ініціалізація при завантаженні сторінки
window.addEventListener('load', function() {
  console.log('Завантаження дашборду...');
  
  // Обробник кнопки виходу
  document.getElementById('logoutBtn').addEventListener('click', logout);
  
  // Завантажуємо дані
  loadProducts();
  loadTodayOperations();
  
  // Автоматичне оновлення кожні 30 секунд
  setInterval(() => {
    loadProducts();
    loadTodayOperations();
  }, 30000);
});