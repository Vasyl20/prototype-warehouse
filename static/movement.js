let allOperations = [];
let filteredOperations = [];

// Завантаження всіх операцій
async function loadAllOperations() {
  try {
    const res = await fetch('/api/operations/all');
    
    if (!res.ok) {
      console.error('Помилка отримання операцій:', res.status);
      allOperations = [];
      filteredOperations = [];
      renderMovementTable();
      calculateSummary();
      return;
    }
    
    allOperations = await res.json();
    console.log('Завантажено операцій:', allOperations.length);
    
    // Показуємо всі операції при завантаженні
    filteredOperations = allOperations;
    renderMovementTable();
    calculateSummary();
  } catch (error) {
    console.error('Помилка завантаження операцій:', error);
    allOperations = [];
    filteredOperations = [];
    renderMovementTable();
    calculateSummary();
  }
}

// Фільтрація за датами
function filterByDate() {
  const dateFrom = document.getElementById('dateFrom').value;
  const dateTo = document.getElementById('dateTo').value;
  
  if (!dateFrom && !dateTo) {
    filteredOperations = allOperations;
  } else {
    filteredOperations = allOperations.filter(op => {
      const opDate = op.date;
      
      if (dateFrom && dateTo) {
        return opDate >= dateFrom && opDate <= dateTo;
      } else if (dateFrom) {
        return opDate >= dateFrom;
      } else if (dateTo) {
        return opDate <= dateTo;
      }
      
      return true;
    });
  }
  
  renderMovementTable();
  calculateSummary();
}

// Пошук по товарах
function searchOperations() {
  const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
  
  if (!searchTerm) {
    // Якщо пошук порожній, показуємо всі відфільтровані за датами
    filterByDate();
    return;
  }
  
  // Спочатку фільтруємо за датами
  filterByDate();
  
  // Потім додатково фільтруємо за пошуковим запитом
  const tempFiltered = filteredOperations.filter(op => {
    return (
      op.product_name.toLowerCase().includes(searchTerm) ||
      (op.product_number && op.product_number.toLowerCase().includes(searchTerm))
    );
  });
  
  filteredOperations = tempFiltered;
  renderMovementTable();
  calculateSummary();
}

// Відображення таблиці
function renderMovementTable() {
  const table = document.getElementById('movementTable');
  table.innerHTML = '';
  
  if (filteredOperations.length === 0) {
    table.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Операцій за вибраний період не знайдено</td></tr>';
    return;
  }
  
  filteredOperations.forEach(op => {
    const row = document.createElement('tr');
    
    // Додаємо клас залежно від типу операції
    if (op.type === 'income') {
      row.classList.add('income-row');
    } else {
      row.classList.add('outcome-row');
    }
    
    const typeText = op.type === 'income' ? '➕ Надходження' : '➖ Відпуск';
    const typeClass = op.type === 'income' ? 'text-success' : 'text-warning';
    
    row.innerHTML = `
      <td>${op.date}</td>
      <td>${op.time}</td>
      <td class="${typeClass}"><strong>${typeText}</strong></td>
      <td>${op.product_name}</td>
      <td>${op.product_number || '—'}</td>
      <td><strong>${op.quantity}</strong></td>
    `;
    
    table.appendChild(row);
  });
}

// Розрахунок підсумків
function calculateSummary() {
  let totalIncome = 0;
  let totalOutcome = 0;
  let totalOperations = filteredOperations.length;
  
  filteredOperations.forEach(op => {
    if (op.type === 'income') {
      totalIncome += op.quantity;
    } else if (op.type === 'outcome') {
      totalOutcome += op.quantity;
    }
  });
  
  // Оновлюємо картки
  document.getElementById('totalIncome').textContent = totalIncome;
  document.getElementById('totalOutcome').textContent = totalOutcome;
  document.getElementById('totalOperations').textContent = totalOperations;
}

// Встановлення поточного місяця за замовчуванням
function setDefaultDates() {
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  
  const dateFrom = firstDay.toISOString().split('T')[0];
  const dateTo = today.toISOString().split('T')[0];
  
  document.getElementById('dateFrom').value = dateFrom;
  document.getElementById('dateTo').value = dateTo;
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

// Ініціалізація
window.addEventListener('load', function() {
  console.log('Завантаження сторінки руху товарів...');
  
  // Встановлюємо дати за замовчуванням
  setDefaultDates();
  
  // Обробники подій
  document.getElementById('filterBtn').addEventListener('click', filterByDate);
  document.getElementById('searchInput').addEventListener('input', searchOperations);
  document.getElementById('logoutBtn').addEventListener('click', logout);
  
  // Завантажуємо операції
  loadAllOperations();
});