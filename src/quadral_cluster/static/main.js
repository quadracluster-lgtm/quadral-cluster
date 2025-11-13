const CURRENT_USER_KEY = "quadral_cluster_user";
const TIM_TO_QUADRA = {
  ILE: "alpha",
  SEI: "alpha",
  ESE: "alpha",
  LII: "alpha",
  SLE: "beta",
  IEI: "beta",
  EIE: "beta",
  LSI: "beta",
  SEE: "gamma",
  ESI: "gamma",
  LIE: "gamma",
  ILI: "gamma",
  IEE: "delta",
  EII: "delta",
  LSE: "delta",
  SLI: "delta",
};

function getApiBaseUrl() {
  return "";
}

function timToQuadra(tim) {
  return TIM_TO_QUADRA[tim] ?? null;
}

function saveCurrentUser(user) {
  if (!user) return;
  const payload = {
    user_id: user.id ?? user.user_id,
    socionics_type: user.socionics_type,
    quadra: user.quadra ?? timToQuadra(user.socionics_type),
  };
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(payload));
}

function loadCurrentUser() {
  try {
    const raw = localStorage.getItem(CURRENT_USER_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (error) {
    console.warn("Failed to parse current user", error);
    return null;
  }
}

function renderMessage(container, text, type = "info") {
  if (!container) return;
  container.textContent = text;
  container.classList.remove("msg-info", "msg-error", "msg-success");
  const className =
      type === "error"
        ? "msg-error"
        : type === "success"
          ? "msg-success"
          : "msg-info";
  container.classList.add(className);
}

async function handleProfileSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const resultContainer = document.getElementById("signup-result");
  const formData = new FormData(form);
  const email = (formData.get("email") || "").trim();
  const username = (formData.get("username") || "").trim();
  const tim = (formData.get("tim") || "IEE").trim();
  const bio = (formData.get("bio") || "").trim();

  const payload = {
    socionics_type: tim,
    profile: {},
  };
  if (email) payload.email = email;
  if (username) payload.username = username;
  if (bio) payload.profile.bio = bio;

  try {
    renderMessage(resultContainer, "Сохраняем профиль…", "info");
    const response = await fetch(`${getApiBaseUrl()}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = data?.detail || data?.message || response.statusText;
      throw new Error(detail || "Ошибка при создании профиля");
    }
    saveCurrentUser(data);
    renderMessage(
      resultContainer,
      `Профиль создан. ID: ${data.id}, TIM: ${data.socionics_type}, квадра: ${data.quadra}.`,
      "success",
    );
    form.reset();
  } catch (error) {
    renderMessage(resultContainer, error.message || "Не удалось создать профиль", "error");
  }
}

function ensureCurrentQuadra(user) {
  if (!user) return null;
  if (user.quadra) return user.quadra;
  const resolved = timToQuadra(user.socionics_type);
  if (resolved) {
    user.quadra = resolved;
    saveCurrentUser(user);
  }
  return resolved;
}

async function loadOpenClusters() {
  const container = document.getElementById("open-clusters");
  const currentUser = loadCurrentUser();
  if (!currentUser) {
    renderMessage(container, "Сначала создайте профиль", "info");
    return;
  }
  const quadra = ensureCurrentQuadra(currentUser);
  const tim = currentUser.socionics_type;
  if (!quadra || !tim) {
    renderMessage(container, "Не удалось определить квадру, обновите профиль", "error");
    return;
  }

  renderMessage(container, "Ищем подходящие кластеры…", "info");
  try {
    const params = new URLSearchParams({ quadra, tim });
    const response = await fetch(`${getApiBaseUrl()}/clusters/open?${params.toString()}`);
    const data = await response.json();
    if (!Array.isArray(data) || data.length === 0) {
      renderMessage(container, "Пока нет подходящих кластеров", "info");
      return;
    }
    container.textContent = "";
    data.forEach((cluster) => {
      container.appendChild(renderClusterCard(cluster));
    });
  } catch (error) {
    renderMessage(container, error.message || "Ошибка загрузки кластеров", "error");
  }
}

function renderClusterCard(cluster) {
  const card = document.createElement("div");
  card.className = "cluster-card";
  const members = Array.isArray(cluster.members) ? cluster.members : [];
  card.innerHTML = `
    <h3>Кластер #${cluster.cluster_id}</h3>
    <p>Квадра: ${cluster.quadra}</p>
    <p>Участники:</p>
    <ul class="cluster-members">
      ${members.length ? members.map((m) => `<li>${m.user_id} (${m.socionics_type})</li>`).join("") : "<li>Пока пусто</li>"}
    </ul>
    <button data-cluster-id="${cluster.cluster_id}">Вступить</button>
  `;
  return card;
}

async function handleClusterJoin(clusterId) {
  const container = document.getElementById("open-clusters");
  const currentUser = loadCurrentUser();
  if (!currentUser) {
    renderMessage(container, "Сначала создайте профиль", "info");
    return;
  }
  try {
    const response = await fetch(`${getApiBaseUrl()}/clusters/join`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cluster_id: Number(clusterId), user_id: currentUser.user_id }),
    });
    if (response.status === 409) {
      renderMessage(container, "Слот для этого TIM уже занят", "error");
      return;
    }
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = data?.detail || data?.reason || response.statusText;
      throw new Error(detail || "Не удалось вступить в кластер");
    }
    renderMessage(container, `Вы присоединились к кластеру #${clusterId}`, "success");
  } catch (error) {
    renderMessage(container, error.message || "Не удалось вступить в кластер, попробуйте позже", "error");
  }
}

async function handleBuildCluster() {
  const container = document.getElementById("build-cluster-result");
  const currentUser = loadCurrentUser();
  if (!currentUser) {
    renderMessage(container, "Сначала создайте профиль", "info");
    return;
  }
  const quadra = ensureCurrentQuadra(currentUser);
  if (!quadra) {
    renderMessage(container, "Не удалось определить квадру, обновите профиль", "error");
    return;
  }
  try {
    renderMessage(container, "Подбираем участников…", "info");
    const response = await fetch(`${getApiBaseUrl()}/clusters/find_or_create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: currentUser.user_id, quadra }),
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = data?.detail || data?.reason || response.statusText;
      throw new Error(detail || "Ошибка подбора кластера");
    }
    if (data.ok && data.members) {
      const membersList = data.members
        .map((member) => `<li>${member.user_id} (${member.socionics_type})</li>`)
        .join("");
      container.innerHTML = `
        <p class="msg-success">Кластер собран! ID: ${data.cluster_id}</p>
        <ul>${membersList}</ul>
      `;
      return;
    }
    if (!data.ok && Array.isArray(data.missing) && data.missing.length) {
      renderMessage(container, `Не хватает TIM: ${data.missing.join(", ")}`, "info");
      return;
    }
    renderMessage(container, "Сервис пока не может собрать кластер", "info");
  } catch (error) {
    renderMessage(container, error.message || "Ошибка при сборке кластера", "error");
  }
}

function initPage() {
  const profileForm = document.getElementById("profile-form");
  if (profileForm) {
    profileForm.addEventListener("submit", handleProfileSubmit);
  }
  const openClustersBtn = document.getElementById("btn-find-open-clusters");
  if (openClustersBtn) {
    openClustersBtn.addEventListener("click", loadOpenClusters);
  }
  const openClustersContainer = document.getElementById("open-clusters");
  if (openClustersContainer) {
    openClustersContainer.addEventListener("click", (event) => {
      const target = event.target;
      if (target instanceof HTMLElement && target.dataset.clusterId) {
        handleClusterJoin(target.dataset.clusterId);
      }
    });
  }
  const buildClusterBtn = document.getElementById("btn-build-cluster");
  if (buildClusterBtn) {
    buildClusterBtn.addEventListener("click", handleBuildCluster);
  }
}

document.addEventListener("DOMContentLoaded", initPage);
