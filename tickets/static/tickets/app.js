const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
            ...(options.headers || {})
        },
        credentials: "same-origin"
    });

    let data = null;
    if (response.status !== 204) {
        data = await response.json().catch(() => null);
    }

    if (!response.ok) {
        let errorMsg = "";
        if (data && typeof data === 'object') {
            errorMsg = Object.entries(data)
                .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
                .join(' | ');
        } else {
            errorMsg = data?.detail || "Ошибка выполнения запроса";
        }
        throw new Error(errorMsg);
    }
    return data;
}

const categorySelect = document.getElementById("category");
const form = document.getElementById("ticket-form");
const titleInput = document.getElementById("title");
const message = document.getElementById("message");
const list = document.getElementById("tickets-list");
const loading = document.getElementById("loading");
const filter = document.getElementById("status-filter");

// Инициализация объекта модального окна Tabler
const statusModalElement = document.getElementById('statusModal');
const bootstrapStatusModal = statusModalElement ? new bootstrap.Modal(statusModalElement) : null;

function showMessage(text, isError = false) {
    message.textContent = text;
    message.className = "alert " + (isError ? "alert-danger" : "alert-success");
}

async function loadCategories() {
    const categories = await apiRequest("/api/categories/");
    categorySelect.replaceChildren();
    for (const category of categories) {
        const option = document.createElement("option");
        option.value = category.id;
        option.textContent = category.name;
        categorySelect.append(option);
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await apiRequest("/api/tickets/", {
            method: "POST",
            body: JSON.stringify({
                title: titleInput.value,
                category: Number(categorySelect.value)
            })
        });
        titleInput.value = "";
        showMessage("Заявка успешно создана");
        await loadTickets();
    } catch (error) {
        showMessage("Не удалось создать заявку: " + error.message, true);
    }
});

async function loadTickets() {
    loading.hidden = false;
    const params = new URLSearchParams();
    if (filter.value) {
        params.set("status", filter.value);
    }
    const query = params.toString();
    const url = "/api/tickets/" + (query ? "?" + query : "");

    try {
        const tickets = await apiRequest(url);
        list.replaceChildren();

        if (tickets.length === 0) {
            const empty = document.createElement("p");
            empty.textContent = "Заявки не найдены";
            list.append(empty);
            return;
        }

        for (const ticket of tickets) {
            const row = document.createElement("div");
            row.className = "d-flex justify-content-between align-items-center border-bottom py-3 gap-3";

            const title = document.createElement("div");
            title.textContent = `${ticket.title} — ${ticket.category_name}`;

            // Контейнер для кнопок управления и статуса
            const actionContainer = document.createElement("div");
            actionContainer.className = "d-flex align-items-center gap-2";

            const status = document.createElement("span");
            status.className = "badge bg-blue-lt";
            status.textContent = ticket.status;

            const editStatusBtn = document.createElement("button");
            editStatusBtn.className = "btn btn-sm btn-outline-secondary";
            editStatusBtn.textContent = "Изменить статус";
            editStatusBtn.onclick = () => openStatusModal(ticket.id, ticket.status);

            const deleteBtn = document.createElement("button");
            deleteBtn.className = "btn btn-sm btn-outline-danger";
            deleteBtn.textContent = "Удалить";
            deleteBtn.onclick = () => deleteTicket(ticket.id, ticket.title);

            actionContainer.append(status, editStatusBtn, deleteBtn);
            row.append(title, actionContainer);
            list.append(row);
        }
    } catch (error) {
        showMessage("Не удалось загрузить заявки: " + error.message, true);
    } finally {
        loading.hidden = true;
    }
}

// САМОСТОЯТЕЛЬНАЯ ЧАСТЬ: Логика открытия модального окна
function openStatusModal(ticketId, currentStatus) {
    document.getElementById('modal-ticket-id').value = ticketId;
    document.getElementById('modal-status-select').value = currentStatus;
    if (bootstrapStatusModal) {
        bootstrapStatusModal.show();
    }
}

// САМОСТОЯТЕЛЬНАЯ ЧАСТЬ: Обработчик клика сохранения статуса в модальном окне
document.getElementById('save-status-btn').onclick = async () => {
    const ticketId = document.getElementById('modal-ticket-id').value;
    const newStatus = document.getElementById('modal-status-select').value;

    if (bootstrapStatusModal) {
        bootstrapStatusModal.hide();
    }

    try {
        await apiRequest(`/api/tickets/${ticketId}/`, {
            method: "PATCH",
            body: JSON.stringify({ status: newStatus })
        });
        showMessage("Статус заявки успешно изменен!");
        await loadTickets();
    } catch (error) {
        showMessage("Не удалось изменить статус: " + error.message, true);
    }
};

// САМОСТОЯТЕЛЬНАЯ ЧАСТЬ: Функция удаления объекта с подтверждением
async function deleteTicket(ticketId, ticketTitle) {
    const confirmed = confirm(`Удалить заявку «${ticketTitle}»?`);
    if (!confirmed) {
        return;
    }
    try {
        await apiRequest(`/api/tickets/${ticketId}/`, {
            method: "DELETE"
        });
        showMessage("Заявка успешно удалена");
        await loadTickets();
    } catch (error) {
        showMessage("Не удалось удалить заявку: " + error.message, true);
    }
}

filter.addEventListener("change", loadTickets);

async function initialize() {
    try {
        await loadCategories();
        await loadTickets();
    } catch (error) {
        showMessage("Ошибка инициализации: " + error.message, true);
    }
}

initialize();

