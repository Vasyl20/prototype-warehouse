let productsData = [];
let filteredProducts = [];

// Завантаження товарів
async function loadProducts() {
  try {
    const res = await fetch('/products');
    productsData = await res.json();
    filteredProducts = productsData;
    renderStockTable();
    calculateTotals();
  } catch (error) {
    console.error('Помилка завантаження товарів:', error);
    alert('Помилка завантаження даних!');
  }
}

// Відображення таблиці залишків
function renderStockTable() {
  const table = document.getElementById('stockTable');
  table.innerHTML = '';
  
  if (filteredProducts.length === 0) {
    table.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Товарів не знайдено</td></tr>';
    return;
  }
  
  filteredProducts.forEach(p => {
    const row = document.createElement('tr');
    const quantity = p.quantity || 0;
    const price = p.price || 0;
    const totalPrice = (quantity * price).toFixed(2);
    
    // Додаємо клас для товарів з нульовим залишком
    if (quantity === 0) {
      row.classList.add('zero-stock');
    }
    
    row.innerHTML = `
      <td>${p.name}</td>
      <td>${p.number || '—'}</td>
      <td>${price.toFixed(2)}</td>
      <td>${quantity}</td>
      <td>${totalPrice}</td>
    `;
    
    table.appendChild(row);
  });
}

// Розрахунок загальних показників
function calculateTotals() {
  let totalValue = 0;
  let totalProducts = productsData.length;
  let zeroStockCount = 0;
  
  productsData.forEach(p => {
    const quantity = p.quantity || 0;
    const price = p.price || 0;
    totalValue += quantity * price;
    
    if (quantity === 0) {
      zeroStockCount++;
    }
  });
  
  // Оновлюємо картки з показниками
  document.getElementById('totalValue').textContent = totalValue.toFixed(2) + ' грн';
  document.getElementById('totalProducts').textContent = totalProducts;
  document.getElementById('zeroStockCount').textContent = zeroStockCount;
}

// Пошук товарів
function searchProducts() {
  const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();
  
  if (!searchTerm) {
    filteredProducts = productsData;
  } else {
    filteredProducts = productsData.filter(p => {
      return (
        p.name.toLowerCase().includes(searchTerm) ||
        (p.number && p.number.toLowerCase().includes(searchTerm))
      );
    });
  }
  
  renderStockTable();
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
  console.log('Завантаження сторінки залишків...');
  
  // Обробник пошуку
  document.getElementById('searchInput').addEventListener('input', searchProducts);
  
  // Обробник кнопки "Вийти"
  document.getElementById('logoutBtn').addEventListener('click', logout);
  
  // Завантажуємо товари
  loadProducts();
});