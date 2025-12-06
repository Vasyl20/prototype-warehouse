let suppliersData = [];
let filteredSuppliers = [];
let addModal, editModal, historyModal;

// Завантаження постачальників
async function loadSuppliers() {
  try {
    const res = await fetch('/api/suppliers');
    suppliersData = await res.json();
    filteredSuppliers = suppliersData;
    renderSuppliers();
  } catch (error) {
    console.error('Помилка завантаження постачальників:', error);
    alert('Помилка завантаження даних!');
  }
}

// Відображення постачальників
function renderSuppliers() {
  const container = document.getElementById('suppliersContainer');
  container.innerHTML = '';

  if (filteredSuppliers.length === 0) {
    container.innerHTML = `
      <div class="col-12 text-center py-5">
        <p class="text-muted">Постачальників не знайдено</p>
        <button class="btn btn-success" onclick="openAddModal()">➕ Додати першого постачальника</button>
      </div>
    `;
    return;
  }

  filteredSuppliers.forEach(s => {
    const card = document.createElement('div');
    card.className = 'col-md-6 col-lg-4 mb-4';

    const contactInfo = [];
    if (s.contact_person) contactInfo.push(`👤 ${s.contact_person}`);
    if (s.phone) contactInfo.push(`📞 ${s.phone}`);
    if (s.email) contactInfo.push(`📧 ${s.email}`);

    card.innerHTML = `
      <div class="card supplier-card h-100">
        <div class="card-body">
          <h5 class="card-title text-primary">🏢 ${s.name}</h5>
          <div class="contact-info mb-2">
            ${contactInfo.join('<br>')}
          </div>
          ${s.address ? `<p class="text-muted mb-2"><small>📍 ${s.address}</small></p>` : ''}
          ${s.notes ? `<p class="text-muted mb-2"><small>📝 ${s.notes}</small></p>` : ''}
          <div class="d-flex gap-2 mt-3">
            <button class="btn btn-sm btn-info flex-fill" onclick="viewHistory(${s.id}, '${s.name.replace(/'/g, "\\'")}')">
              📋 Історія
            </button>
            <button class="btn btn-sm btn-warning" onclick="openEditModal(${s.id})">
              ✏️
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteSupplier(${s.id})">
              🗑️
            </button>
          </div>
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

// Відкриття модального вікна додавання
function openAddModal() {
  clearAddForm();
  addModal.show();
}

// Очищення форми додавання
function clearAddForm() {
  document.getElementById('addName').value = '';
  document.getElementById('addContactPerson').value = '';
  document.getElementById('addPhone').value = '';
  document.getElementById('addEmail').value = '';
  document.getElementById('addAddress').value = '';
  document.getElementById('addNotes').value = '';
}

// Додавання постачальника
async function addSupplier() {
  const data = {
    name: document.getElementById('addName').value.trim(),
    contact_person: document.getElementById('addContactPerson').value.trim(),
    phone: document.getElementById('addPhone').value.trim(),
    email: document.getElementById('addEmail').value.trim(),
    address: document.getElementById('addAddress').value.trim(),
    notes: document.getElementById('addNotes').value.trim()
  };

  if (!data.name) {
    alert('Введіть назву постачальника!');
    return;
  }

  try {
    const res = await fetch('/api/suppliers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (res.ok) {
      await loadSuppliers();
      addModal.hide();
      alert('✅ Постачальник успішно доданий!');
    } else {
      const err = await res.json();
      alert('❌ Помилка: ' + err.error);
    }
  } catch (error) {
    console.error('Помилка додавання:', error);
    alert('Помилка додавання постачальника!');
  }
}

// Відкриття модального вікна редагування
function openEditModal(id) {
  const supplier = suppliersData.find(s => s.id === id);

  if (!supplier) {
    alert('Постачальник не знайдений!');
    return;
  }

  document.getElementById('editId').value = supplier.id;
  document.getElementById('editName').value = supplier.name;
  document.getElementById('editContactPerson').value = supplier.contact_person || '';
  document.getElementById('editPhone').value = supplier.phone || '';
  document.getElementById('editEmail').value = supplier.email || '';
  document.getElementById('editAddress').value = supplier.address || '';
  document.getElementById('editNotes').value = supplier.notes || '';

  editModal.show();
}

// Збереження змін
async function saveEdit() {
  const id = document.getElementById('editId').value;
  const data = {
    name: document.getElementById('editName').value.trim(),
    contact_person: document.getElementById('editContactPerson').value.trim(),
    phone: document.getElementById('editPhone').value.trim(),
    email: document.getElementById('editEmail').value.trim(),
    address: document.getElementById('editAddress').value.trim(),
    notes: document.getElementById('editNotes').value.trim()
  };

  if (!data.name) {
    alert('Введіть назву постачальника!');
    return;
  }

  try {
    const res = await fetch(`/api/suppliers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (res.ok) {
      await loadSuppliers();
      editModal.hide();
      alert('✅ Зміни успішно збережено!');
    } else {
      const err = await res.json();
      alert('❌ Помилка: ' + err.error);
    }
  } catch (error) {
    console.error('Помилка редагування:', error);
    alert('Помилка збереження змін!');
  }
}

// Видалення постачальника
async function deleteSupplier(id) {
  const supplier = suppliersData.find(s => s.id === id);

  if (!confirm(`Видалити постачальника "${supplier.name}"?\n\nУВАГА: Якщо є операції з цим постачальником, видалення буде неможливе.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/suppliers/${id}`, {
      method: 'DELETE'
    });

    if (res.ok) {
      await loadSuppliers();
      alert('✅ Постачальник успішно видалений!');
    } else {
      const err = await res.json();
      alert('❌ Помилка: ' + err.error);
    }
  } catch (error) {
    console.error('Помилка видалення:', error);
    alert('Помилка видалення постачальника!');
  }
}

// Перегляд історії поставок
async function viewHistory(supplierId, supplierName) {
  try {
    document.getElementById('historySupplierName').textContent = `Постачальник: ${supplierName}`;

    const res = await fetch(`/api/suppliers/${supplierId}/operations`);
    const operations = await res.json();

    const table = document.getElementById('historyTable');
    table.innerHTML = '';

    if (operations.length === 0) {
      table.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Поставок від цього постачальника ще не було</td></tr>';
    } else {
      operations.forEach(op => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${op.date}</td>
          <td>${op.time}</td>
          <td>${op.product_name}</td>
          <td>${op.product_number || '—'}</td>
          <td><strong>${op.quantity}</strong></td>
          <td>${op.invoice_number || '—'}</td>
        `;
        table.appendChild(row);
      });
    }

    historyModal.show();
  } catch (error) {
    console.error('Помилка завантаження історії:', error);
    alert('Помилка завантаження історії поставок!');
  }
}

// Пошук постачальників
function searchSuppliers() {
  const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();

  if (!searchTerm) {
    filteredSuppliers = suppliersData;
  } else {
    filteredSuppliers = suppliersData.filter(s => {
      return (
        s.name.toLowerCase().includes(searchTerm) ||
        (s.contact_person && s.contact_person.toLowerCase().includes(searchTerm)) ||
        (s.phone && s.phone.toLowerCase().includes(searchTerm)) ||
        (s.email && s.email.toLowerCase().includes(searchTerm)) ||
        (s.address && s.address.toLowerCase().includes(searchTerm))
      );
    });
  }

  renderSuppliers();
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
  console.log('Завантаження сторінки постачальників...');

  addModal = new bootstrap.Modal(document.getElementById('addModal'));
  editModal = new bootstrap.Modal(document.getElementById('editModal'));
  historyModal = new bootstrap.Modal(document.getElementById('historyModal'));

  document.getElementById('addSupplierBtn').addEventListener('click', openAddModal);
  document.getElementById('saveAddBtn').addEventListener('click', addSupplier);
  document.getElementById('saveEditBtn').addEventListener('click', saveEdit);
  document.getElementById('searchInput').addEventListener('input', searchSuppliers);
  document.getElementById('logoutBtn').addEventListener('click', logout);

  loadSuppliers();
});