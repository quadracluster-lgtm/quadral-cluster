const storageKey = "qc_user";

function saveUser(user) {
  localStorage.setItem(storageKey, JSON.stringify(user));
}

function getUser() {
  const raw = localStorage.getItem(storageKey);
  return raw ? JSON.parse(raw) : null;
}

function renderSignupSuccess(container, data) {
  container.textContent = `Профиль создан: ID ${data.user_id}, TIM ${data.socionics_type}, квадра ${data.quadra}`;
}

function renderError(container, message) {
  container.textContent = message;
}

async function handleSignupSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const resultContainer = document.getElementById("signup-result");
  resultContainer.textContent = "Отправляем данные...";

  const payload = {
    email: form.email.value.trim(),
    username: form.username.value.trim(),
    socionics_type: form.tim.value,
    profile: {
      bio: form.bio.value.trim() || null,
    },
  };

  try {
    const response = await fetch("/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || "Не удалось создать профиль");
    }

    renderSignupSuccess(resultContainer, data);
    saveUser({
      user_id: data.user_id,
      socionics_type: data.socionics_type,
      quadra: data.quadra,
    });
  } catch (error) {
    renderError(resultContainer, error.message || "Ошибка соединения");
  }
}

function createClusterCard(cluster) {
  const card = document.createElement("div");
  card.className = "cluster-card";

  const title = document.createElement("h3");
  title.textContent = `Кластер #${cluster.cluster_id} — квадра ${cluster.quadra}`;
  card.appendChild(title);

  if (cluster.members?.length) {
    const list = document.createElement("ul");
    list.className = "cluster-members";
    cluster.members.forEach((member) => {
      const li = document.createElement("li");
      const tim = member.socionics_type || member.tim || "?";
      const username = member.username || member.user_id || "Участник";
      li.textContent = `${username} (${tim})`;
      list.appendChild(li);
    });
    card.appendChild(list);
  }

  const button = document.createElement("button");
  button.textContent = "Вступить";
  button.dataset.clusterId = cluster.cluster_id;
  button.addEventListener("click", () => handleJoinCluster(cluster.cluster_id));
  card.appendChild(button);

  return card;
}

async function loadOpenClusters() {
  const resultContainer = document.getElementById("open-clusters");
  const user = getUser();

  if (!user) {
    renderError(resultContainer, "Сначала создайте профиль");
    return;
  }

  resultContainer.textContent = "Загружаем доступные кластеры...";
  const params = new URLSearchParams({
    quadra: user.quadra,
    tim: user.socionics_type,
    limit: "10",
  });

  try {
    const response = await fetch(`/clusters/open?${params.toString()}`);
    const data = await response.json().catch(() => []);
    if (!response.ok) {
      throw new Error(data.detail || "Не удалось получить кластеры");
    }

    resultContainer.textContent = "";
    if (!data.length) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Нет доступных кластеров. Попробуйте собрать новый.";
      resultContainer.appendChild(empty);
      return;
    }

    data.forEach((cluster) => {
      resultContainer.appendChild(createClusterCard(cluster));
    });
  } catch (error) {
    renderError(resultContainer, error.message || "Ошибка соединения");
  }
}

async function handleJoinCluster(clusterId) {
  const resultContainer = document.getElementById("open-clusters");
  const user = getUser();
  if (!user) {
    renderError(resultContainer, "Сначала создайте профиль");
    return;
  }

  try {
    const response = await fetch("/clusters/join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cluster_id: clusterId, user_id: user.user_id }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || "Не удалось вступить в кластер");
    }

    renderError(resultContainer, `Вы присоединились к кластеру #${clusterId}`);
    await loadOpenClusters();
  } catch (error) {
    renderError(resultContainer, error.message || "Ошибка соединения");
  }
}

async function handleBuildCluster() {
  const resultContainer = document.getElementById("build-cluster-result");
  const user = getUser();
  if (!user) {
    renderError(resultContainer, "Сначала создайте профиль");
    return;
  }

  resultContainer.textContent = "Пробуем собрать кластер...";
  try {
    const response = await fetch("/clusters/find_or_create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user.user_id, quadra: user.quadra }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || "Не удалось собрать кластер");
    }

    if (data.ok) {
      const membersList = (data.members || [])
        .map((member) => `${member.username || member.user_id} (${member.socionics_type || member.tim})`)
        .join(", ");
      resultContainer.textContent = `Кластер #${data.cluster_id}: ${membersList}`;
    } else if (Array.isArray(data.missing) && data.missing.length) {
      resultContainer.textContent = `Не хватает TIM: ${data.missing.join(", ")}`;
    } else {
      resultContainer.textContent = "Кластер пока не собран";
    }
  } catch (error) {
    renderError(resultContainer, error.message || "Ошибка соединения");
  }
}

function init() {
  const signupForm = document.getElementById("signup-form");
  signupForm?.addEventListener("submit", handleSignupSubmit);

  document
    .getElementById("btn-find-open-clusters")
    ?.addEventListener("click", loadOpenClusters);

  document
    .getElementById("btn-build-cluster")
    ?.addEventListener("click", handleBuildCluster);
}

window.addEventListener("DOMContentLoaded", init);
