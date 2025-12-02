// // Зберігаємо поточні дані товарів
// let productsData = [];
// let editModal;

// // Завантаження товарів з сервера
// async function loadProducts() {
//   try {
//     const res = await fetch('/products');
//     productsData = await res.json();
//     renderTable();
//   } catch (error) {
//     console.error('Помилка завантаження:', error);
//     alert('Помилка завантаження даних!');
//   }
// }

// // Відображення таблиці
// function renderTable() {
//   const table = document.getElementById('tableBody');
//   table.innerHTML = '';

//   productsData.forEach(p => {
//     const row = document.createElement('tr');
//     row.innerHTML = `
//       <td>${p.id}</td>
//       <td>${p.name}</td>
//       <td>${p.number || ''}</td>
//       <td>${p.quantity || 0}</td>
//       <td>${p.price || 0}</td>
//       <td>${p.warehouse_number}</td>
//       <td>${p.shelf}</td>
//       <td>${p.rack}</td>
//       <td>
//         <button class="btn btn-warning btn-sm me-1" data-id="${p.id}" data-action="edit">✏️</button>
//         <button class="btn btn-danger btn-sm" data-id="${p.id}" data-action="delete">🗑️</button>
//       </td>
//     `;
    
//     // Додаємо обробники для кнопок
//     row.querySelectorAll('button').forEach(btn => {
//       btn.addEventListener('click', function() {
//         const id = this.dataset.id;
//         const action = this.dataset.action;
        
//         if (action === 'edit') {
//           openEditModal(id);
//         } else if (action === 'delete') {
//           deleteProduct(id);
//         }
//       });
//     });
    
//     table.appendChild(row);
//   });
// }

// // Додавання нового товару
// async function addProduct() {
//   const data = {
//     name: document.getElementById('name').value.trim(),
//     number: document.getElementById('number').value.trim(),
//     quantity: parseInt(document.getElementById('qty').value) || 0,
//     price: parseFloat(document.getElementById('price').value) || 0,
//     warehouse_number: document.getElementById('storage').value.trim(),
//     shelf: document.getElementById('shelf').value.trim(),
//     rack: document.getElementById('rack').value.trim(),
//   };

//   if (!data.name) {
//     alert("Введіть назву товару!");
//     return;
//   }

//   if (!data.warehouse_number || !data.shelf || !data.rack) {
//     alert("Заповніть всі поля локації (Склад, Поличка, Стелаж)!");
//     return;
//   }

//   try {
//     const res = await fetch('/products', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify(data)
//     });

//     if (res.ok) {
//       await loadProducts();
//       clearForm();
//       alert("✅ Товар успішно додано!");
//     } else {
//       const err = await res.json();
//       alert("❌ Помилка: " + err.error);
//     }
//   } catch (error) {
//     console.error('Помилка додавання:', error);
//     alert('Помилка додавання товару!');
//   }
// }

// // Видалення товару
// async function deleteProduct(id) {
//   if (!confirm("❓ Видалити цей товар?")) return;
  
//   try {
//     const res = await fetch(`/products/${id}`, { method: 'DELETE' });
    
//     if (res.ok) {
//       await loadProducts();
//       alert("✅ Товар успішно видалено!");
//     } else {
//       alert("❌ Помилка видалення!");
//     }
//   } catch (error) {
//     console.error('Помилка видалення:', error);
//     alert('Помилка видалення товару!');
//   }
// }

// // Відкриття модального вікна редагування
// function openEditModal(id) {
//   const product = productsData.find(p => p.id == id);
  
//   if (!product) {
//     alert("Товар не знайдено!");
//     return;
//   }

//   // Заповнюємо поля форми
//   document.getElementById('editId').value = product.id;
//   document.getElementById('editName').value = product.name;
//   document.getElementById('editNumber').value = product.number || '';
//   document.getElementById('editQty').value = product.quantity || 0;
//   document.getElementById('editPrice').value = product.price || 0;
//   document.getElementById('editStorage').value = product.warehouse_number;
//   document.getElementById('editShelf').value = product.shelf;
//   document.getElementById('editRack').value = product.rack;

//   // Показуємо модальне вікно
//   editModal.show();
// }

// // Збереження змін після редагування
// async function saveEdit() {
//   const id = document.getElementById('editId').value;
//   const updatedData = {
//     name: document.getElementById('editName').value.trim(),
//     number: document.getElementById('editNumber').value.trim(),
//     quantity: parseInt(document.getElementById('editQty').value) || 0,
//     price: parseFloat(document.getElementById('editPrice').value) || 0
//   };

//   if (!updatedData.name) {
//     alert("Введіть назву товару!");
//     return;
//   }

//   try {
//     const res = await fetch(`/products/${id}`, {
//       method: 'PUT',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify(updatedData)
//     });

//     if (res.ok) {
//       await loadProducts();
//       editModal.hide();
//       alert("✅ Зміни успішно збережено!");
//     } else {
//       alert("❌ Помилка при збереженні змін!");
//     }
//   } catch (error) {
//     console.error('Помилка редагування:', error);
//     alert('Помилка збереження змін!');
//   }
// }

// // Очищення форми додавання
// function clearForm() {
//   document.getElementById('name').value = '';
//   document.getElementById('number').value = '';
//   document.getElementById('qty').value = '';
//   document.getElementById('price').value = '';
//   document.getElementById('storage').value = '';
//   document.getElementById('shelf').value = '';
//   document.getElementById('rack').value = '';
// }

// // Ініціалізація при завантаженні сторінки
// window.addEventListener('load', function() {
//   // Ініціалізуємо модальне вікно Bootstrap
//   editModal = new bootstrap.Modal(document.getElementById('editModal'));
  
//   // Обробник кнопки "Додати"
//   document.getElementById('addBtn').addEventListener('click', addProduct);
  
//   // Обробник кнопки "Зберегти" в модальному вікні
//   document.getElementById('saveEditBtn').addEventListener('click', saveEdit);
  
//   // Завантажуємо товари
//   loadProducts();
// });


// Зберігаємо поточні дані товарів
let productsData = [];
let editModal;
let addModal;

// Завантаження товарів з сервера
async function loadProducts() {
  try {
    const res = await fetch('/products');
    productsData = await res.json();
    renderTable();
  } catch (error) {
    console.error('Помилка завантаження:', error);
    alert('Помилка завантаження даних!');
  }
}

// Відображення таблиці
function renderTable() {
  const table = document.getElementById('tableBody');
  table.innerHTML = '';

  productsData.forEach(p => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${p.id}</td>
      <td>${p.name}</td>
      <td>${p.number || ''}</td>
      <td>${p.quantity || 0}</td>
      <td>${p.price || 0}</td>
      <td>${p.warehouse_number}</td>
      <td>${p.shelf}</td>
      <td>${p.rack}</td>
      <td>
        <button class="btn btn-warning btn-sm me-1" data-id="${p.id}" data-action="edit">✏️</button>
        <button class="btn btn-danger btn-sm" data-id="${p.id}" data-action="delete">🗑️</button>
      </td>
    `;
    
    // Додаємо обробники для кнопок
    row.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', function() {
        const id = this.dataset.id;
        const action = this.dataset.action;
        
        if (action === 'edit') {
          openEditModal(id);
        } else if (action === 'delete') {
          deleteProduct(id);
        }
      });
    });
    
    table.appendChild(row);
  });
}

// Відкриття модального вікна додавання
function openAddModal() {
  clearAddForm();
  addModal.show();
}

// Додавання нового товару
async function addProduct() {
  const data = {
    name: document.getElementById('addName').value.trim(),
    number: document.getElementById('addNumber').value.trim(),
    quantity: parseInt(document.getElementById('addQty').value) || 0,
    price: parseFloat(document.getElementById('addPrice').value) || 0,
    warehouse_number: document.getElementById('addStorage').value.trim(),
    shelf: document.getElementById('addShelf').value.trim(),
    rack: document.getElementById('addRack').value.trim(),
  };

  if (!data.name) {
    alert("Введіть назву товару!");
    return;
  }

  if (!data.warehouse_number || !data.shelf || !data.rack) {
    alert("Заповніть всі поля локації (Склад, Поличка, Стелаж)!");
    return;
  }

  try {
    const res = await fetch('/products', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (res.ok) {
      await loadProducts();
      addModal.hide();
      alert("✅ Товар успішно додано!");
    } else {
      const err = await res.json();
      alert("❌ Помилка: " + err.error);
    }
  } catch (error) {
    console.error('Помилка додавання:', error);
    alert('Помилка додавання товару!');
  }
}

// Видалення товару
async function deleteProduct(id) {
  if (!confirm("❓ Видалити цей товар?")) return;
  
  try {
    const res = await fetch(`/products/${id}`, { method: 'DELETE' });
    
    if (res.ok) {
      await loadProducts();
      alert("✅ Товар успішно видалено!");
    } else {
      alert("❌ Помилка видалення!");
    }
  } catch (error) {
    console.error('Помилка видалення:', error);
    alert('Помилка видалення товару!');
  }
}

// Відкриття модального вікна редагування
function openEditModal(id) {
  const product = productsData.find(p => p.id == id);
  
  if (!product) {
    alert("Товар не знайдено!");
    return;
  }

  // Заповнюємо поля форми
  document.getElementById('editId').value = product.id;
  document.getElementById('editName').value = product.name;
  document.getElementById('editNumber').value = product.number || '';
  document.getElementById('editQty').value = product.quantity || 0;
  document.getElementById('editPrice').value = product.price || 0;
  document.getElementById('editStorage').value = product.warehouse_number;
  document.getElementById('editShelf').value = product.shelf;
  document.getElementById('editRack').value = product.rack;

  // Показуємо модальне вікно
  editModal.show();
}

// Збереження змін після редагування
async function saveEdit() {
  const id = document.getElementById('editId').value;
  const updatedData = {
    name: document.getElementById('editName').value.trim(),
    number: document.getElementById('editNumber').value.trim(),
    quantity: parseInt(document.getElementById('editQty').value) || 0,
    price: parseFloat(document.getElementById('editPrice').value) || 0
  };

  if (!updatedData.name) {
    alert("Введіть назву товару!");
    return;
  }

  try {
    const res = await fetch(`/products/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatedData)
    });

    if (res.ok) {
      await loadProducts();
      editModal.hide();
      alert("✅ Зміни успішно збережено!");
    } else {
      alert("❌ Помилка при збереженні змін!");
    }
  } catch (error) {
    console.error('Помилка редагування:', error);
    alert('Помилка збереження змін!');
  }
}

// Очищення форми додавання
function clearAddForm() {
  document.getElementById('addName').value = '';
  document.getElementById('addNumber').value = '';
  document.getElementById('addQty').value = '';
  document.getElementById('addPrice').value = '';
  document.getElementById('addStorage').value = '';
  document.getElementById('addShelf').value = '';
  document.getElementById('addRack').value = '';
}

// Ініціалізація при завантаженні сторінки
window.addEventListener('load', function() {
  // Ініціалізуємо модальні вікна Bootstrap
  editModal = new bootstrap.Modal(document.getElementById('editModal'));
  addModal = new bootstrap.Modal(document.getElementById('addModal'));
  
  // Обробник кнопки "Додати товар"
  document.getElementById('addBtn').addEventListener('click', openAddModal);
  
  // Обробник кнопки "Додати" в модальному вікні
  document.getElementById('saveAddBtn').addEventListener('click', addProduct);
  
  // Обробник кнопки "Зберегти" в модальному вікні редагування
  document.getElementById('saveEditBtn').addEventListener('click', saveEdit);
  
  // Завантажуємо товари
  loadProducts();
});