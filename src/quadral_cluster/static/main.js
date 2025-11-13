function saveCurrentUser(user) {
  const payload = {
    user_id: user.id,
    socionics_type: user.socionics_type,
    quadra: user.quadra,
  };
  localStorage.setItem("qc_user", JSON.stringify(payload));
}

function loadCurrentUser() {
  const raw = localStorage.getItem("qc_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function renderMessage(containerId, text) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.textContent = text;
}

async function handleProfileSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const email = form.email.value.trim();
  const username = form.username.value.trim();
  const tim = form.tim.value;
  const bio = form.bio.value.trim();

  const payload = {
    email,
    username,
    socionics_type: tim,
    profile: bio ? { bio } : {},
  };

  try {
    const resp = await fetch("/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await resp.json();
    if (!resp.ok) {
      renderMessage("signup-result", `Ошибка: ${resp.status} ${JSON.stringify(data)}`);
      return;
    }

    saveCurrentUser(data);
    renderMessage(
      "signup-result",
      `Профиль создан. ID: ${data.id}, TIM: ${data.socionics_type}, квадра: ${data.quadra}.`,
    );
  } catch (err) {
    renderMessage("signup-result", `Сетевая ошибка: ${err}`);
  }
}

async function fetchOpenClusters() {
  const user = loadCurrentUser();
  const container = document.getElementById("open-clusters");
  if (!container) return;

  container.innerHTML = "";

  if (!user) {
    container.textContent = "Сначала создайте профиль.";
    return;
  }

  const url = `/clusters/open?quadra=${encodeURIComponent(
    user.quadra,
  )}&tim=${encodeURIComponent(user.socionics_type)}&limit=10`;

  try {
    const resp = await fetch(url);
    const data = await resp.json();
    if (!resp.ok) {
      container.textContent = `Ошибка: ${resp.status} ${JSON.stringify(data)}`;
      return;
    }

    if (!Array.isArray(data) || data.length === 0) {
      container.textContent = "Подходящих кластеров пока нет.";
      return;
    }

    data.forEach((cluster) => {
      const card = document.createElement("div");
      card.className = "cluster-card";

      const title = document.createElement("h3");
      title.textContent = `Кластер #${cluster.id} (${cluster.quadra})`;
      card.appendChild(title);

      if (cluster.members && cluster.members.length) {
        const members = document.createElement("div");
        members.className = "cluster-members";
        members.textContent = cluster.members
          .map((m) => `${m.user_id} (${m.socionics_type})`)
          .join(", ");
        card.appendChild(members);
      }

      const btn = document.createElement("button");
      btn.textContent = "Вступить";
      btn.addEventListener("click", () => joinCluster(cluster.id));
      card.appendChild(btn);

      container.appendChild(card);
    });
  } catch (err) {
    container.textContent = `Сетевая ошибка: ${err}`;
  }
}

async function joinCluster(clusterId) {
  const user = loadCurrentUser();
  const container = document.getElementById("open-clusters");
  if (!user || !container) return;

  try {
    const resp = await fetch("/clusters/join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cluster_id: clusterId, user_id: user.user_id }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      container.textContent = `Не удалось вступить: ${resp.status} ${JSON.stringify(data)}`;
      return;
    }
    container.textContent = `Вы присоединились к кластеру #${clusterId}.`;
  } catch (err) {
    container.textContent = `Сетевая ошибка: ${err}`;
  }
}

async function buildCluster() {
  const user = loadCurrentUser();
  if (!user) {
    renderMessage("build-cluster-result", "Сначала создайте профиль.");
    return;
  }

  try {
    const resp = await fetch("/clusters/find_or_create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user.user_id, quadra: user.quadra }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      renderMessage(
        "build-cluster-result",
        `Ошибка: ${resp.status} ${JSON.stringify(data)}`,
      );
      return;
    }

    if (data.ok === false && Array.isArray(data.missing)) {
      renderMessage(
        "build-cluster-result",
        `Не хватает TIM: ${data.missing.join(", ")}`,
      );
      return;
    }

    if (data.ok && data.cluster) {
      const members = (data.cluster.members || [])
        .map((m) => `${m.user_id} (${m.socionics_type})`)
        .join(", ");
      renderMessage(
        "build-cluster-result",
        `Собран кластер #${data.cluster.id}: ${members}`,
      );
      return;
    }

    renderMessage("build-cluster-result", JSON.stringify(data));
  } catch (err) {
    renderMessage("build-cluster-result", `Сетевая ошибка: ${err}`);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("profile-form");
  if (form) {
    form.addEventListener("submit", handleProfileSubmit);
  }

  const btnOpen = document.getElementById("btn-find-open-clusters");
  if (btnOpen) {
    btnOpen.addEventListener("click", fetchOpenClusters);
  }

  const btnBuild = document.getElementById("btn-build-cluster");
  if (btnBuild) {
    btnBuild.addEventListener("click", buildCluster);
  }
});
