let currentEnvId = null;
let logsInterval = null;

// Inicialização
document.addEventListener("DOMContentLoaded", () => {
  refreshEnvironments();

  // Auto-refresh a cada 5 segundos
  setInterval(refreshEnvironments, 3000);

  // Handler do formulário
  document
    .getElementById("createForm")
    .addEventListener("submit", handleCreateEnvironment);
});

// Criar novo ambiente
async function handleCreateEnvironment(event) {
  event.preventDefault();

  const formData = new FormData(event.target);
  const data = {
    name: formData.get("name"),
    cpu_limit: parseFloat(formData.get("cpu_limit")),
    memory_mb: parseInt(formData.get("memory_mb")),
    io_weight: parseInt(formData.get("io_weight")),
    script_content: formData.get("script_content"),
  };

  const submitBtn = event.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = "Criando...";

  try {
    const response = await fetch("/api/environments", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erro ao criar ambiente");
    }

    const result = await response.json();

    showNotification("Ambiente criado com sucesso!", "success");
    event.target.reset();
    await refreshEnvironments();
  } catch (error) {
    console.error("Erro:", error);
    showNotification(error.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Criar Ambiente";
  }
}

// Listar ambientes
async function refreshEnvironments() {
  try {
    const response = await fetch("/api/environments");

    if (!response.ok) {
      throw new Error("Erro ao carregar ambientes");
    }

    const environments = await response.json();
    renderEnvironments(environments);
  } catch (error) {
    console.error("Erro:", error);
    document.getElementById(
      "environmentsList"
    ).innerHTML = `<p class="loading">Erro ao carregar ambientes: ${error.message}</p>`;
  }
}

// Renderizar lista de ambientes
function renderEnvironments(environments) {
  const container = document.getElementById("environmentsList");

  if (environments.length === 0) {
    container.innerHTML = `
            <div class="empty-state">
                <h3>Nenhum ambiente criado</h3>
                <p>Crie seu primeiro ambiente usando o formulário acima</p>
            </div>
        `;
    return;
  }

  container.innerHTML = `
        <div class="environments-grid">
            ${environments.map((env) => renderEnvironmentCard(env)).join("")}
        </div>
    `;
}

// Renderizar card de ambiente
function renderEnvironmentCard(env) {
  const statusClass = `status-${env.status.toLowerCase()}`;
  const statusText =
    {
      RUNNING: "Rodando",
      EXITED: "Finalizado",
      ERROR: "Erro",
    }[env.status] || env.status;

  const createdDate = new Date(env.created_at).toLocaleString("pt-BR");

  return `
        <div class="env-card">
            <div class="env-header">
                <h3>${escapeHtml(env.name)}</h3>
                <span class="status-badge ${statusClass}">${statusText}</span>
            </div>
            
            <div class="env-info">
                <div class="info-row">
                    <span class="info-label">ID:</span>
                    <span class="info-value">${env.id}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">CPU:</span>
                    <span class="info-value">${env.cpu_limit} cores</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Memória:</span>
                    <span class="info-value">${env.memory_mb} MB</span>
                </div>
                <div class="info-row">
                    <span class="info-label">I/O:</span>
                    <span class="info-value">${env.io_weight}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">PID:</span>
                    <span class="info-value">${env.process_id || "N/A"}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Criado:</span>
                    <span class="info-value">${createdDate}</span>
                </div>
            </div>
            
            <div class="env-actions">
                <button class="btn btn-secondary" onclick="showLogs('${
                  env.id
                }')">
                    Logs
                </button>
                ${
                  env.status === "RUNNING"
                    ? `
                    <button class="btn btn-secondary" onclick="stopEnvironment('${env.id}')">
                        Parar
                    </button>
                `
                    : ""
                }
                <button class="btn btn-danger" onclick="deleteEnvironment('${
                  env.id
                }', '${escapeHtml(env.name)}')">
                    Remover
                </button>
            </div>
        </div>
    `;
}

// Ver logs
async function showLogs(envId) {
  currentEnvId = envId;

  const modal = document.getElementById("logsModal");
  const logsContent = document.getElementById("logsContent");

  modal.classList.add("show");
  logsContent.textContent = "Carregando logs...";
  logsContent.classList.add("empty");

  await loadLogs(envId);

  // Auto-refresh de logs a cada 2 segundos
  if (logsInterval) {
    clearInterval(logsInterval);
  }
  logsInterval = setInterval(() => loadLogs(envId), 2000);
}

// Carregar logs
async function loadLogs(envId) {
  try {
    const response = await fetch(`/api/environments/${envId}/logs`);

    if (!response.ok) {
      throw new Error("Erro ao carregar logs");
    }

    const data = await response.json();
    const logsContent = document.getElementById("logsContent");

    if (
      data.logs &&
      data.logs.trim() !== "" &&
      data.logs !== "Nenhum log disponível"
    ) {
      logsContent.textContent = data.logs;
      logsContent.classList.remove("empty");
    } else {
      logsContent.textContent = "Nenhum log disponível";
      logsContent.classList.add("empty");
    }

    // Auto-scroll para o final
    logsContent.scrollTop = logsContent.scrollHeight;
  } catch (error) {
    console.error("Erro ao carregar logs:", error);
    document.getElementById(
      "logsContent"
    ).textContent = `Erro: ${error.message}`;
  }
}

// Fechar modal de logs
function closeLogsModal() {
  const modal = document.getElementById("logsModal");
  modal.classList.remove("show");
  currentEnvId = null;

  if (logsInterval) {
    clearInterval(logsInterval);
    logsInterval = null;
  }
}

// Atualizar logs manualmente
function refreshLogs() {
  if (currentEnvId) {
    loadLogs(currentEnvId);
  }
}

// Parar ambiente
async function stopEnvironment(envId) {
  if (!confirm("Deseja parar este ambiente?")) {
    return;
  }

  try {
    const response = await fetch(`/api/environments/${envId}/stop`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erro ao parar ambiente");
    }

    showNotification("Ambiente parado com sucesso", "success");
    await refreshEnvironments();
  } catch (error) {
    console.error("Erro:", error);
    showNotification(error.message, "error");
  }
}

// Remover ambiente
async function deleteEnvironment(envId, envName) {
  if (
    !confirm(
      `Deseja remover o ambiente "${envName}"?\n\nEsta ação não pode ser desfeita.`
    )
  ) {
    return;
  }

  try {
    const response = await fetch(`/api/environments/${envId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Erro ao remover ambiente");
    }

    showNotification("Ambiente removido com sucesso", "success");
    await refreshEnvironments();
  } catch (error) {
    console.error("Erro:", error);
    showNotification(error.message, "error");
  }
}

// Mostrar notificação
function showNotification(message, type = "success") {
  const container = document.getElementById("notifications");
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;

  container.appendChild(notification);

  setTimeout(() => {
    notification.remove();
  }, 5000);
}

// Escapar HTML
function escapeHtml(text) {
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

// Fechar modal ao clicar fora
window.onclick = function (event) {
  const modal = document.getElementById("logsModal");
  if (event.target === modal) {
    closeLogsModal();
  }
};
