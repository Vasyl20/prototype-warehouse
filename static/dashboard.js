// Зберігаємо поточні дані
let productsData = [];
let operationsData = [];
let allOperationsData = [];

// Графіки
let operationsChart = null;
let operationsTypeChart = null;
let topProductsChart = null;
let warehouseChart = null;

// Завантаження товарів
async function loadProducts() {
  try {
    console.log('Завантаження товарів...');
    const res = await fetch('/products');
    productsData = await res.json();
    console.log('Товарів завантажено:', productsData.length);
    updateDashboard();
    showCriticalStock();
    createTopProductsChart();
    createWarehouseChart();
  } catch (error) {
    console.error('Помилка завантаження товарів:', error);
  }
}

// Завантаження операцій за сьогодні
async function loadTodayOperations() {
  try {
    console.log('Завантаження операцій за сьогодні...');
    const res = await fetch('/api/operations/today');
    
    if (!res.ok) {
      console.error('Помилка отримання операцій:', res.status);
      operationsData = [];
      updateDashboard();
      showRecentOperations();
      createOperationsTypeChart();
      return;
    }
    
    operationsData = await res.json();
    console.log('Операцій за сьогодні:', operationsData.length);
    updateDashboard();
    showRecentOperations();
    calculateTodayStats();
    createOperationsTypeChart();
  } catch (error) {
    console.error('Помилка завантаження операцій:', error);
    operationsData = [];
    updateDashboard();
    showRecentOperations();
  }
}

// Завантаження всіх операцій для графіка за 7 днів
async function loadAllOperations() {
  try {
    console.log('Завантаження всіх операцій...');
    const res = await fetch('/api/operations/all');
    
    if (!res.ok) {
      console.error('Помилка отримання всіх операцій:', res.status);
      allOperationsData = [];
      createOperationsChart();
      return;
    }
    
    allOperationsData = await res.json();
    console.log('Всіх операцій завантажено:', allOperationsData.length);
    createOperationsChart();
  } catch (error) {
    console.error('Помилка завантаження всіх операцій:', error);
    allOperationsData = [];
    createOperationsChart();
  }
}

// Оновлення головних карточок дашборду
function updateDashboard() {
  const totalProducts = productsData.length;
  
  let totalValue = 0;
  productsData.forEach(p => {
    const quantity = p.quantity || 0;
    const price = p.price || 0;
    totalValue += quantity * price;
  });
  
  const todayOperations = operationsData.length;
  
  let zeroStock = 0;
  productsData.forEach(p => {
    if ((p.quantity || 0) === 0) {
      zeroStock++;
    }
  });
  
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
  
  const critical = productsData.filter(p => (p.quantity || 0) <= 5);
  
  if (critical.length === 0) {
    table.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Всі товари в достатній кількості ✅</td></tr>';
    return;
  }
  
  critical.sort((a, b) => (a.quantity || 0) - (b.quantity || 0));
  
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
  
  const balanceEl = document.getElementById('todayBalance');
  if (balance > 0) {
    balanceEl.className = 'text-success';
  } else if (balance < 0) {
    balanceEl.className = 'text-danger';
  } else {
    balanceEl.className = 'text-info';
  }
}

// Графік операцій за останні 7 днів
function createOperationsChart() {
  console.log('Створення графіка операцій за 7 днів...');
  const ctx = document.getElementById('operationsChart');
  
  if (!ctx) {
    console.error('Canvas operationsChart не знайдено!');
    return;
  }
  
  // Отримуємо останні 7 днів
  const last7Days = [];
  for (let i = 6; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    last7Days.push(date.toISOString().split('T')[0]);
  }
  
  // Рахуємо операції по днях
  const incomeByDay = {};
  const outcomeByDay = {};
  
  last7Days.forEach(day => {
    incomeByDay[day] = 0;
    outcomeByDay[day] = 0;
  });
  
  allOperationsData.forEach(op => {
    if (incomeByDay.hasOwnProperty(op.date)) {
      if (op.type === 'income') {
        incomeByDay[op.date] += op.quantity;
      } else {
        outcomeByDay[op.date] += op.quantity;
      }
    }
  });
  
  const labels = last7Days.map(date => {
    const d = new Date(date);
    return d.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit' });
  });
  
  if (operationsChart) {
    operationsChart.destroy();
  }
  
  operationsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Надходження',
          data: last7Days.map(day => incomeByDay[day]),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.3,
          fill: true
        },
        {
          label: 'Відпуск',
          data: last7Days.map(day => outcomeByDay[day]),
          borderColor: 'rgb(255, 159, 64)',
          backgroundColor: 'rgba(255, 159, 64, 0.2)',
          tension: 0.3,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
  
  console.log('Графік операцій створено ✓');
}

// Кругова діаграма типів операцій
function createOperationsTypeChart() {
  console.log('Створення діаграми типів операцій...');
  const container = document.getElementById('operationsTypeContainer');
  const ctx = document.getElementById('operationsTypeChart');
  
  if (!ctx || !container) {
    console.error('Canvas operationsTypeChart не знайдено!');
    return;
  }
  
  let incomeCount = 0;
  let outcomeCount = 0;
  
  operationsData.forEach(op => {
    if (op.type === 'income') {
      incomeCount += op.quantity;
    } else {
      outcomeCount += op.quantity;
    }
  });
  
  if (operationsTypeChart) {
    operationsTypeChart.destroy();
  }
  
  if (incomeCount === 0 && outcomeCount === 0) {
    container.innerHTML = '<p class="text-center text-muted mt-5">Немає даних за сьогодні</p>';
    console.log('Немає даних для діаграми типів операцій');
    return;
  }
  
  operationsTypeChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Надходження', 'Відпуск'],
      datasets: [{
        data: [incomeCount, outcomeCount],
        backgroundColor: [
          'rgba(75, 192, 192, 0.8)',
          'rgba(255, 159, 64, 0.8)'
        ],
        borderWidth: 2,
        borderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });
  
  console.log('Діаграма типів операцій створено ✓');
}

// Графік топ-5 товарів за вартістю
function createTopProductsChart() {
  console.log('Створення графіка топ-5 товарів...');
  const container = document.getElementById('topProductsContainer');
  const ctx = document.getElementById('topProductsChart');
  
  if (!ctx || !container) {
    console.error('Canvas topProductsChart не знайдено!');
    return;
  }
  
  // Рахуємо вартість кожного товару
  const productsWithValue = productsData.map(p => ({
    name: p.name,
    value: (p.quantity || 0) * (p.price || 0)
  }));
  
  // Сортуємо та беремо топ-5
  productsWithValue.sort((a, b) => b.value - a.value);
  const top5 = productsWithValue.slice(0, 5);
  
  if (topProductsChart) {
    topProductsChart.destroy();
  }
  
  if (top5.length === 0 || top5.every(p => p.value === 0)) {
    container.innerHTML = '<p class="text-center text-muted mt-5">Немає даних</p>';
    console.log('Немає даних для графіка топ-5');
    return;
  }
  
  topProductsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top5.map(p => p.name.length > 15 ? p.name.substring(0, 15) + '...' : p.name),
      datasets: [{
        label: 'Вартість (грн)',
        data: top5.map(p => p.value.toFixed(2)),
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)'
        ],
        borderWidth: 1,
        borderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
  
  console.log('Графік топ-5 створено ✓');
}

// Графік розподілу товарів по складах
function createWarehouseChart() {
  console.log('Створення графіка розподілу по складах...');
  const container = document.getElementById('warehouseContainer');
  const ctx = document.getElementById('warehouseChart');
  
  if (!ctx || !container) {
    console.error('Canvas warehouseChart не знайдено!');
    return;
  }
  
  // Рахуємо кількість товарів на кожному складі
  const warehouseCount = {};
  
  productsData.forEach(p => {
    const warehouse = p.warehouse_number;
    if (warehouseCount[warehouse]) {
      warehouseCount[warehouse]++;
    } else {
      warehouseCount[warehouse] = 1;
    }
  });
  
  const labels = Object.keys(warehouseCount);
  const data = Object.values(warehouseCount);
  
  if (warehouseChart) {
    warehouseChart.destroy();
  }
  
  if (labels.length === 0) {
    container.innerHTML = '<p class="text-center text-muted mt-5">Немає даних</p>';
    console.log('Немає даних для графіка складів');
    return;
  }
  
  const colors = [
    'rgba(255, 99, 132, 0.8)',
    'rgba(54, 162, 235, 0.8)',
    'rgba(255, 206, 86, 0.8)',
    'rgba(75, 192, 192, 0.8)',
    'rgba(153, 102, 255, 0.8)',
    'rgba(255, 159, 64, 0.8)',
    'rgba(199, 199, 199, 0.8)'
  ];
  
  warehouseChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: labels.map(l => `Склад ${l}`),
      datasets: [{
        data: data,
        backgroundColor: colors.slice(0, labels.length),
        borderWidth: 2,
        borderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });
  
  console.log('Графік розподілу по складах створено ✓');
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
  console.log('=== Завантаження дашборду ===');
  console.log('Chart.js версія:', Chart.version);
  
  document.getElementById('logoutBtn').addEventListener('click', logout);
  
  // Завантажуємо дані
  loadProducts();
  loadTodayOperations();
  loadAllOperations();
  
  // Автоматичне оновлення кожні 30 секунд
  setInterval(() => {
    console.log('Автоматичне оновлення даних...');
    loadProducts();
    loadTodayOperations();
    loadAllOperations();
  }, 30000);
  
  console.log('=== Дашборд ініціалізовано ===');
});