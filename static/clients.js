let clientsData = [];
let filteredClients = [];
let addModal, editModal, historyModal;

// Завантаження клієнтів
async function loadClients() {
  try {
    const res = await fetch('/api/clients');
    clientsData = await res.json();
    filteredClients = clientsData;
    renderClients();
  } catch (error) {
    console.error('Помилка завантаження клієнтів:', error);
    alert('Помилка завантаження даних!');
  }
}

// Відображення клієнтів
function renderClients() {
  const container = document.getElementById('clientsContainer');
  container.innerHTML = '';

  if (filteredClients.length === 0) {
    container.innerHTML = `
      <div class="col-12 text-center py-5">
        <p class="text-muted">Клієнтів не знайдено</p>
        <button class="btn btn-info" onclick="openAddModal()">➕ Додати першого клієнта</button>
      </div>
    `;
    return;
  }

  filteredClients.forEach(c => {
    const card = document.createElement('div');
    card.className = 'col-md-6 col-lg-4 mb-4';

    const contactInfo = [];
    if (c.contact_person) contactInfo.push(`👤 ${c.contact_person}`);
    if (c.phone) contactInfo.push(`📞 ${c.phone}`);
    if (c.email) contactInfo.push(`📧 ${c.email}`);

    card.innerHTML = `
      <div class="card client-card h-100">
        <div class="card-body">
          <h5 class="card-title text-info">👥 ${c.name}</h5>
          <div class="contact-info mb-2">
            ${contactInfo.join('<br>')}
          </div>
          ${c.address ? `<p class="text-muted mb-2"><small>📍 ${c.address}</small></p>` : ''}
          ${c.notes ? `<p class="text-muted mb-2"><small>📝 ${c.notes}</small></p>` : ''}
          <div class="d-flex gap-2 mt-3">
            <button class="btn btn-sm btn-primary flex-fill" onclick="viewHistory(${c.id}, '${c.name.replace(/'/g, "\\'")}')">
              📋 Історія
            </button>
            <button class="btn btn-sm btn-warning" onclick="openEditModal(${c.id})">
              ✏️
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteClient(${c.id})">
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

// Додавання клієнта
async function addClient() {
  const data = {
    name: document.getElementById('addName').value.trim(),
    contact_person: document.getElementById('addContactPerson').value.trim(),
    phone: document.getElementById('addPhone').value.trim(),
    email: document.getElementById('addEmail').value.trim(),
    address: document.getElementById('addAddress').value.trim(),
    notes: document.getElementById('addNotes').value.trim()
  };

  if (!data.name) {
    alert('Введіть назву / ПІБ клієнта!');
    return;
  }

  try {
    const res = await fetch('/api/clients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (res.ok) {
      await loadClients();
      addModal.hide();
      alert('✅ Клієнт успішно доданий!');
    } else {
      const err = await res.json();
      alert('❌ Помилка: ' + err.error);
    }
  } catch (error) {
    console.error('Помилка додавання:', error);
    alert('Помилка додавання клієнта!');
  }
}

// Відкриття модального вікна редагування
function openEditModal(id) {
  const client = clientsData.find(c => c.id === id);

  if (!client) {
    alert('Клієнт не знайдений!');
    return;
  }

  document.getElementById('editId').value = client.id;
  document.getElementById('editName').value = client.name;
  document.getElementById('editContactPerson').value = client.contact_person || '';
  document.getElementById('editPhone').value = client.phone || '';
  document.getElementById('editEmail').value = client.email || '';
  document.getElementById('editAddress').value = client.address || '';
  document.getElementById('editNotes').value = client.notes || '';

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
    alert('Введіть назву / ПІБ клієнта!');
    return;
  }

  try {
    const res = await fetch(`/api/clients/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (res.ok) {
      await loadClients();
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

// Видалення клієнта
async function deleteClient(id) {
  const client = clientsData.find(c => c.id === id);

  if (!confirm(`Видалити клієнта "${client.name}"?\n\nУВАГА: Якщо є операції з цим клієнтом, видалення буде неможливе.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/clients/${id}`, {
      method: 'DELETE'
    });

    if (res.ok) {
      await loadClients();
      alert('✅ Клієнт успішно видалений!');
    } else {
      const err = await res.json();
      alert('❌ Помилка: ' + err.error);
    }
  } catch (error) {
    console.error('Помилка видалення:', error);
    alert('Помилка видалення клієнта!');
  }
}

// Перегляд історії відпусків
async function viewHistory(clientId, clientName) {
  try {
    document.getElementById('historyClientName').textContent = `Клієнт: ${clientName}`;

    const res = await fetch(`/api/clients/${clientId}/operations`);
    const operations = await res.json();

    const table = document.getElementById('historyTable');
    table.innerHTML = '';

    if (operations.length === 0) {
      table.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Відпусків цьому клієнту ще не було</td></tr>';
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
    alert('Помилка завантаження історії відпусків!');
  }
}

// Пошук клієнтів
function searchClients() {
  const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();

  if (!searchTerm) {
    filteredClients = clientsData;
  } else {
    filteredClients = clientsData.filter(c => {
      return (
        c.name.toLowerCase().includes(searchTerm) ||
        (c.contact_person && c.contact_person.toLowerCase().includes(searchTerm)) ||
        (c.phone && c.phone.toLowerCase().includes(searchTerm)) ||
        (c.email && c.email.toLowerCase().includes(searchTerm)) ||
        (c.address && c.address.toLowerCase().includes(searchTerm))
      );
    });
  }

  renderClients();
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
  console.log('Завантаження сторінки клієнтів...');

  addModal = new bootstrap.Modal(document.getElementById('addModal'));
  editModal = new bootstrap.Modal(document.getElementById('editModal'));
  historyModal = new bootstrap.Modal(document.getElementById('historyModal'));

  document.getElementById('addClientBtn').addEventListener('click', openAddModal);
  document.getElementById('saveAddBtn').addEventListener('click', addClient);
  document.getElementById('saveEditBtn').addEventListener('click', saveEdit);
  document.getElementById('searchInput').addEventListener('input', searchClients);

  // Два обробники для кнопки виходу (одна в меню, одна в хедері)
  document.getElementById('logoutBtn').addEventListener('click', logout);
  const logoutBtn2 = document.getElementById('logoutBtn2');
  if (logoutBtn2) {
    logoutBtn2.addEventListener('click', logout);
  }

  loadClients();
});