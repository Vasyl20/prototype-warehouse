let productsData = [];
let movementHistory = [];
let selectedProduct = null;

// Завантаження товарів
async function loadProducts() {
  try {
    const res = await fetch('/products');
    productsData = await res.json();
    console.log('Завантажено товарів:', productsData.length);
    populateProductSelect();
  } catch (error) {
    console.error('Помилка завантаження товарів:', error);
    alert('Помилка завантаження товарів!');
  }
}

// Заповнення випадаючого списку товарами
function populateProductSelect() {
  const select = document.getElementById('productSelect');
  select.innerHTML = '<option value="">Виберіть товар...</option>';
  
  productsData.forEach(p => {
    const option = document.createElement('option');
    option.value = p.id;
    
    // Формуємо текст: "Назва | Артикул | Склад-Поличка-Стелаж | Залишок"
    let displayText = p.name;
    
    if (p.number) {
      displayText += ` | №${p.number}`;
    }
    
    displayText += ` | 📍 ${p.warehouse_number}-${p.shelf}-${p.rack}`;
    displayText += ` | Залишок: ${p.quantity || 0} шт`;
    
    option.textContent = displayText;
    
    // Зберігаємо дані товару в data-атрибуті
    option.dataset.productData = JSON.stringify(p);
    
    select.appendChild(option);
  });
}

// Обробка вибору товару
function handleProductSelect() {
  const select = document.getElementById('productSelect');
  const selectedOption = select.options[select.selectedIndex];
  
  if (!select.value) {
    // Ховаємо блоки якщо нічого не вибрано
    document.getElementById('currentLocationBlock').classList.add('d-none');
    document.getElementById('newLocationBlock').classList.add('d-none');
    selectedProduct = null;
    return;
  }
  
  // Отримуємо дані товару
  selectedProduct = JSON.parse(selectedOption.dataset.productData);
  
  // Показуємо поточну локацію
  const currentInfo = document.getElementById('currentLocationInfo');
  currentInfo.innerHTML = `
    <div class="row">
      <div class="col-md-3">
        <strong>Товар:</strong><br>
        ${selectedProduct.name}
      </div>
      <div class="col-md-2">
        <strong>Артикул:</strong><br>
        ${selectedProduct.number || '—'}
      </div>
      <div class="col-md-2">
        <strong>Склад:</strong><br>
        <span class="location-badge">${selectedProduct.warehouse_number}</span>
      </div>
      <div class="col-md-2">
        <strong>Поличка:</strong><br>
        <span class="location-badge">${selectedProduct.shelf}</span>
      </div>
      <div class="col-md-2">
        <strong>Стелаж:</strong><br>
        <span class="location-badge">${selectedProduct.rack}</span>
      </div>
      <div class="col-md-1">
        <strong>Кількість:</strong><br>
        ${selectedProduct.quantity || 0} шт
      </div>
    </div>
  `;
  
  // Показуємо блоки
  document.getElementById('currentLocationBlock').classList.remove('d-none');
  document.getElementById('newLocationBlock').classList.remove('d-none');
  
  // Очищаємо поля нової локації
  document.getElementById('newWarehouse').value = '';
  document.getElementById('newShelf').value = '';
  document.getElementById('newRack').value = '';
}

// Переміщення товару
async function moveProduct() {
  if (!selectedProduct) {
    alert('❌ Спочатку оберіть товар!');
    return;
  }
  
  const newWarehouse = document.getElementById('newWarehouse').value.trim();
  const newShelf = document.getElementById('newShelf').value.trim();
  const newRack = document.getElementById('newRack').value.trim();
  
  if (!newWarehouse || !newShelf || !newRack) {
    alert('❌ Заповніть всі поля нової локації!');
    return;
  }
  
  // Підтвердження
  const confirmText = `Перемістити товар "${selectedProduct.name}"?\n\n` +
                      `З: Склад ${selectedProduct.warehouse_number}, ` +
                      `Поличка ${selectedProduct.shelf}, ` +
                      `Стелаж ${selectedProduct.rack}\n\n` +
                      `В: Склад ${newWarehouse}, ` +
                      `Поличка ${newShelf}, ` +
                      `Стелаж ${newRack}`;
  
  if (!confirm(confirmText)) {
    return;
  }
  
  try {
    const res = await fetch('/relocation/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_id: selectedProduct.id,
        to_warehouse: newWarehouse,
        to_shelf: newShelf,
        to_rack: newRack
      })
    });
    
    if (res.ok) {
      alert('✅ Товар успішно переміщено!');
      
      // Оновлюємо дані
      await loadProducts();
      await loadMovementHistory();
      
      // Очищаємо форму
      document.getElementById('productSelect').value = '';
      document.getElementById('currentLocationBlock').classList.add('d-none');
      document.getElementById('newLocationBlock').classList.add('d-none');
      selectedProduct = null;
    } else {
      const err = await res.json();
      alert('❌ Помилка: ' + err.error);
    }
  } catch (error) {
    console.error('Помилка переміщення:', error);
    alert('❌ Помилка переміщення товару!');
  }
}

// Завантаження історії переміщень
async function loadMovementHistory() {
  try {
    const res = await fetch('/relocation/history');
    
    if (!res.ok) {
      console.error('Помилка отримання історії:', res.status);
      movementHistory = [];
      renderMovementTable();
      return;
    }
    
    movementHistory = await res.json();
    console.log('Завантажено історії переміщень:', movementHistory.length);
    renderMovementTable();
  } catch (error) {
    console.error('Помилка завантаження історії:', error);
    movementHistory = [];
    renderMovementTable();
  }
}

// Відображення таблиці історії
function renderMovementTable() {
  const table = document.getElementById('movementTable');
  table.innerHTML = '';
  
  if (movementHistory.length === 0) {
    table.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-muted">
          Історія переміщень порожня
        </td>
      </tr>
    `;
    return;
  }
  
  movementHistory.forEach(m => {
    const row = document.createElement('tr');
    row.classList.add('movement-row');
    
    const fromLocation = `${m.from_warehouse}-${m.from_shelf}-${m.from_rack}`;
    const toLocation = `${m.to_warehouse}-${m.to_shelf}-${m.to_rack}`;
    
    row.innerHTML = `
      <td>${m.date}</td>
      <td>${m.time}</td>
      <td>${m.product_name}</td>
      <td>${m.product_number || '—'}</td>
      <td>
        <span class="badge bg-secondary">${fromLocation}</span>
      </td>
      <td>
        <span class="badge bg-success">${toLocation}</span>
      </td>
    `;
    
    table.appendChild(row);
  });
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
  console.log('Завантаження сторінки переміщення товарів...');
  
  // Обробники подій
  document.getElementById('productSelect').addEventListener('change', handleProductSelect);
  document.getElementById('moveBtn').addEventListener('click', moveProduct);
  document.getElementById('logoutBtn').addEventListener('click', logout);
  
  // Завантажуємо дані
  loadProducts();
  loadMovementHistory();
  
  console.log('Сторінка переміщення ініціалізована!');
});