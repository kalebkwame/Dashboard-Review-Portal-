const API_BASE = window.location.origin;
let token = localStorage.getItem("portal_token");
let currentUser = null;

const loginView = document.querySelector("#loginView");
const appView = document.querySelector("#appView");
const logoutButton = document.querySelector("#logoutButton");

const SECTION_SAMPLE_DATA = {
  "Sales Overview": {
    chart: "line",
    headline: "$1.28M",
    change: "+18.4% vs prior period",
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    values: [820, 910, 860, 1040, 1120, 1280]
  },
  "Customer Retention": {
    chart: "bar",
    headline: "92.4%",
    change: "+3.1 pts quarter over quarter",
    labels: ["Enterprise", "Mid-market", "Small business", "Self-service"],
    values: [96, 93, 89, 84]
  },
  "Revenue by Region": {
    chart: "pie",
    headline: "$1.28M",
    change: "Top region: North America",
    labels: ["North America", "Europe", "Asia Pacific", "Latin America"],
    values: [520, 310, 270, 180]
  },
  "Marketing Trend": {
    chart: "line",
    headline: "42.8K",
    change: "+24.6% qualified leads",
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    values: [24, 27, 31, 29, 38, 43]
  },
  "Revenue Growth": {
    chart: "bar",
    headline: "+18.4%",
    change: "Year-over-year growth",
    labels: ["Q1", "Q2", "Q3", "Q4"],
    values: [12, 15, 17, 18]
  },
  "Finance KPIs": {
    chart: "bar",
    headline: "38.2%",
    change: "Operating margin",
    labels: ["Operating margin", "Gross margin", "EBITDA", "Cash reserve"],
    values: [38, 62, 29, 71]
  }
};

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(API_BASE + path, { ...options, headers });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail)) {
        message = body.detail.map(item => item.msg || item.message).filter(Boolean).join("; ");
      }
    } catch (_) {}
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

let registering = false;
let bootstrappingAdmin = false;

async function register() {
  const name = document.querySelector("#registerName").value.trim();
  const email = document.querySelector("#email").value.trim();
  const password = document.querySelector("#password").value;
  const error = document.querySelector("#loginError");
  error.textContent = "";

  try {
    await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password, role: "viewer" })
    });
    registering = false;
    document.querySelector("#registerFields").classList.add("hidden");
    document.querySelector("#authTitle").textContent = "Sign in";
    document.querySelector("#loginButton").textContent = "Login";
    document.querySelector("#toggleRegisterButton").textContent = "Create an account";
    await login();
  } catch (err) {
    error.textContent = err.message;
  }
}

async function bootstrapAdmin() {
  const name = document.querySelector("#registerName").value.trim();
  const email = document.querySelector("#email").value.trim();
  const password = document.querySelector("#password").value;
  const setupKey = document.querySelector("#adminSetupKey").value;
  const error = document.querySelector("#loginError");
  error.textContent = "";

  try {
    await api("/auth/bootstrap-admin", {
      method: "POST",
      body: JSON.stringify({ name, email, password, setup_key: setupKey })
    });
    await login();
  } catch (err) {
    error.textContent = err.message;
  }
}

async function login() {
  const email = document.querySelector("#email").value;
  const password = document.querySelector("#password").value;
  const error = document.querySelector("#loginError");
  error.textContent = "";

  try {
    const result = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    token = result.access_token;
    localStorage.setItem("portal_token", token);
    await startApp();
  } catch (err) {
    error.textContent = err.message;
  }
}

async function startApp() {
  try {
    currentUser = await api("/auth/me");
  } catch (_) {
    logout();
    return;
  }

  loginView.classList.add("hidden");
  appView.classList.remove("hidden");
  logoutButton.classList.remove("hidden");

  document.querySelector("#accountDetails").textContent = `${currentUser.name} · ${currentUser.role}`;
  if (currentUser.role === "analyst" || currentUser.role === "admin") {
    document.querySelector("#createDashboardButton").classList.remove("hidden");
    document.querySelector("#shareButton").classList.remove("hidden");
  }
  if (currentUser.role === "admin") {
    document.querySelector("#createSectionButton").classList.remove("hidden");
    document.querySelector("#deleteDashboardButton").classList.remove("hidden");
    document.querySelector("#manageUsersButton").classList.remove("hidden");
  }

  await loadDashboards();
  if (currentUser.role === "admin") await loadUsers();
}

function logout() {
  token = null;
  currentUser = null;
  localStorage.removeItem("portal_token");
  appView.classList.add("hidden");
  logoutButton.classList.add("hidden");
  loginView.classList.remove("hidden");
  document.querySelector("#accountDetails").textContent = "";
  document.querySelector("#createDashboardButton").classList.add("hidden");
  document.querySelector("#createSectionButton").classList.add("hidden");
  document.querySelector("#shareButton").classList.add("hidden");
  document.querySelector("#deleteDashboardButton").classList.add("hidden");
  document.querySelector("#manageUsersButton").classList.add("hidden");
  document.querySelector("#userManagementPanel").classList.add("hidden");
}

async function loadDashboards() {
  const dashboards = await api("/dashboards");
  const select = document.querySelector("#dashboardSelect");
  if (!dashboards.length) {
    select.innerHTML = "";
    document.querySelector("#dashboardTitle").textContent = "No dashboards yet";
    document.querySelector("#sectionsGrid").innerHTML = "";
    document.querySelector("#deleteDashboardButton").classList.add("hidden");
    return;
  }
  select.innerHTML = dashboards.map(d => `<option value="${d.id}">${d.name}</option>`).join("");
  await loadDashboard(dashboards[0].id);
}

async function loadDashboard(dashboardId) {
  const dashboard = await api(`/dashboards/${dashboardId}`);
  document.querySelector("#dashboardTitle").textContent = dashboard.name;

  const sections = await api("/sections");
  const ownedSections = sections.filter(section => section.dashboard_id === Number(dashboardId));
  const grid = document.querySelector("#sectionsGrid");
  grid.innerHTML = "";

  for (const section of ownedSections) {
    await renderSection(section);
  }
}

function renderChart(section) {
  const persistedData = section.chart_labels?.length && section.chart_values?.length ? {
    chart: section.chart_type,
    headline: section.chart_headline || "",
    change: section.chart_change || "",
    labels: section.chart_labels,
    values: section.chart_values
  } : null;

  const data = persistedData || SECTION_SAMPLE_DATA[section.name] || {
    chart: section.chart_type,
    headline: "Sample metric",
    change: "Period to date",
    labels: ["Week 1", "Week 2", "Week 3", "Week 4"],
    values: [62, 68, 74, 81]
  };

  if (data.chart === "pie") {
    const total = data.values.reduce((sum, value) => sum + value, 0);
    const colors = ["#315fbd", "#78a99b", "#e9a23b", "#e56b6f"];
    let start = 0;
    const segments = data.values.map((value, index) => {
      const degrees = (value / total) * 360;
      const segment = `${colors[index]} ${start}deg ${start + degrees}deg`;
      start += degrees;
      return segment;
    }).join(", ");

    return `<div class="chart chart-pie-wrap">
      <div class="chart-pie" style="background:conic-gradient(${segments})">
        <div class="chart-pie-center"><strong>${data.headline}</strong><span>revenue</span></div>
      </div>
      <div class="chart-legend">
        ${data.labels.map((label, index) => `<div><span style="background:${colors[index]}"></span>${label} <b>$${data.values[index]}K</b></div>`).join("")}
      </div>
    </div>`;
  }

  if (data.chart === "line") {
    const width = 260;
    const height = 120;
    const padding = 16;
    const max = Math.max(...data.values) * 1.12;
    const min = Math.min(...data.values) * 0.85;
    const points = data.values.map((value, index) => {
      const x = padding + index * ((width - padding * 2) / (data.values.length - 1));
      const y = height - padding - ((value - min) / (max - min)) * (height - padding * 2);
      return `${x},${y}`;
    }).join(" ");

    const circles = data.values.map((value, index) => {
      const x = padding + index * ((width - padding * 2) / (data.values.length - 1));
      const y = height - padding - ((value - min) / (max - min)) * (height - padding * 2);
      return `<circle cx="${x}" cy="${y}" r="4"><title>${data.labels[index]}: $${value}K</title></circle>`;
    }).join("");

    return `<div class="chart chart-line">
      <div class="chart-summary"><strong>${data.headline}</strong><span>${data.change}</span></div>
      <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${section.name} monthly trend">
        <line x1="16" y1="104" x2="244" y2="104"/>
        <polyline points="${points}"/>
        ${circles}
      </svg>
      <div class="chart-axis">${data.labels.map(label => `<span>${label}</span>`).join("")}</div>
    </div>`;
  }

  const max = Math.max(...data.values);
  return `<div class="chart chart-bar">
    <div class="chart-summary"><strong>${data.headline}</strong><span>${data.change}</span></div>
    <div class="bar-grid" style="--bar-count:${data.values.length}">
      ${data.values.map((value, index) => `
        <div class="bar-column">
          <span class="bar-value">${value}%</span>
          <div class="bar-track"><div class="bar-fill" style="--bar-height:${Math.max((value / max) * 78, 8)}px"></div></div>
          <span class="bar-label">${data.labels[index]}</span>
        </div>`).join("")}
    </div>
  </div>`;
}

async function createShareLink() {
  const dashboardId = document.querySelector("#dashboardSelect").value;
  const result = await api(`/dashboards/${dashboardId}/share`, {
    method: "POST",
    body: JSON.stringify({ expires_in_hours: 24 })
  });
  const url = `${window.location.origin}/shared/${result.token}`;
  document.querySelector("#shareResult").innerHTML = `Share link: <a href="${url}" target="_blank">${url}</a>`;
}

async function renderSection(section) {
  const reviews = await api(`/sections/${section.id}/reviews`);
  const card = document.createElement("article");
  card.className = "card section-card";

  card.innerHTML = `
    <div class="section-heading">
      <div><h3>${section.name}</h3><span>${section.chart_type} chart</span></div>
      <div class="section-heading-actions">
        <strong class="review-count">${reviews.length} ${reviews.length === 1 ? "review" : "reviews"}</strong>
        ${currentUser.role === "admin" ? `<button type="button" class="edit-section-button" data-section-id="${section.id}">Edit</button><button type="button" class="delete-section-button" data-section-id="${section.id}">Delete</button>` : ""}
      </div>
    </div>
    ${renderChart(section)}
    <div class="reviews">
      ${reviews.length ? reviews.map(review => `
        <div class="review">
          <div class="review-header">
            <strong>${review.reviewer_name}</strong>
            <span class="rating-badge">${review.rating}/5</span>
          </div>
          <p>${review.comment}</p>
        </div>`).join("") : `<p class="empty-reviews">No comments yet. Share your thoughts below.</p>`}
    </div>
    <div class="review-form">
      <label>Your name</label>
      <input class="review-name" value="${currentUser.name}">
      <label>Rating</label>
      <select class="review-rating">
        <option value="5">5 - Excellent</option>
        <option value="4">4 - Good</option>
        <option value="3">3 - Average</option>
        <option value="2">2 - Poor</option>
        <option value="1">1 - Very poor</option>
      </select>
      <label>Comment</label>
      <textarea class="review-comment" placeholder="What do you think about this information?"></textarea>
      <p class="error review-error"></p>
      <button class="submit-review" data-section-id="${section.id}">Submit review</button>
    </div>`;

  document.querySelector("#sectionsGrid").appendChild(card);

  card.querySelectorAll(".delete-section-button").forEach(button => {
    button.addEventListener("click", async () => {
      if (!confirm(`Delete section "${section.name}" and all of its reviews?`)) return;
      try {
        await api(`/sections/${section.id}`, { method: "DELETE" });
        await loadDashboard(document.querySelector("#dashboardSelect").value);
      } catch (err) {
        window.alert(err.message);
      }
    });
  });

  card.querySelectorAll(".edit-section-button").forEach(button => {
    button.addEventListener("click", () => {
      document.querySelector("#editSectionId").value = section.id;
      document.querySelector("#editSectionName").value = section.name;
      document.querySelector("#editSectionChart").value = section.chart_type;
      document.querySelector("#editSectionHeadline").value = section.chart_headline || "";
      document.querySelector("#editSectionChange").value = section.chart_change || "";
      document.querySelector("#editSectionLabels").value = (section.chart_labels || []).join(", ");
      document.querySelector("#editSectionValues").value = (section.chart_values || []).join(", ");
      document.querySelector("#sectionEditModal").classList.remove("hidden");
    });
  });

  card.querySelector(".submit-review").addEventListener("click", async event => {
    const sectionId = event.currentTarget.dataset.sectionId;
    const error = card.querySelector(".review-error");
    error.textContent = "";

    try {
      await api(`/sections/${sectionId}/reviews`, {
        method: "POST",
        body: JSON.stringify({
          reviewer_name: card.querySelector(".review-name").value,
          rating: Number(card.querySelector(".review-rating").value),
          comment: card.querySelector(".review-comment").value
        })
      });
      await loadDashboard(document.querySelector("#dashboardSelect").value);
    } catch (err) {
      error.textContent = err.message;
    }
  });
}

async function loadUsers() {
  const users = await api("/auth/users");
  const list = document.querySelector("#userList");
  list.innerHTML = users.map(user => `
    <div class="user-row">
      <div class="user-info">
        <strong>${user.name}</strong>
        <span>${user.email}</span>
      </div>
      <select class="user-role-select" data-user-id="${user.id}" ${user.id === currentUser.id ? "disabled" : ""}>
        <option value="viewer" ${user.role === "viewer" ? "selected" : ""}>Viewer</option>
        <option value="analyst" ${user.role === "analyst" ? "selected" : ""}>Analyst</option>
        <option value="admin" ${user.role === "admin" ? "selected" : ""}>Admin</option>
      </select>
      ${user.id === currentUser.id
        ? `<button type="button" class="delete-user-button" data-user-id="${user.id}" data-user-name="${user.name}">Delete my account</button>`
        : `<button type="button" class="delete-user-button" data-user-id="${user.id}" data-user-name="${user.name}">Delete</button>`}
    </div>`).join("");

  list.querySelectorAll(".user-role-select").forEach(select => {
    select.addEventListener("change", async event => {
      const roleSelect = event.currentTarget;
      roleSelect.disabled = true;
      try {
        await api(`/auth/users/${roleSelect.dataset.userId}/role`, {
          method: "PATCH",
          body: JSON.stringify({ role: roleSelect.value })
        });
        document.querySelector("#userManagementMessage").textContent = "User role updated.";
      } catch (err) {
        document.querySelector("#userManagementMessage").textContent = err.message;
      }
      roleSelect.disabled = false;
    });
  });

  list.querySelectorAll(".delete-user-button").forEach(button => {
    button.addEventListener("click", async event => {
      const userId = event.currentTarget.dataset.userId;
      const userName = event.currentTarget.dataset.userName;

      if (confirm(`Delete user "${userName}"?`)) {
        try {
          await api(`/auth/users/${userId}`, { method: "DELETE" });
          if (Number(userId) === currentUser.id) {
            logout();
            return;
          }
          await loadUsers();
          document.querySelector("#userManagementMessage").textContent = "User deleted.";
        } catch (err) {
          document.querySelector("#userManagementMessage").textContent = err.message;
        }
      }
    });
  });
}

document.querySelector("#loginButton").addEventListener("click", () => {
  if (bootstrappingAdmin) bootstrapAdmin();
  else if (registering) register();
  else login();
});

document.querySelector("#toggleRegisterButton").addEventListener("click", () => {
  bootstrappingAdmin = false;
  document.querySelector("#adminSetupFields").classList.add("hidden");
  registering = !registering;
  document.querySelector("#registerFields").classList.toggle("hidden", !registering);
  document.querySelector("#authTitle").textContent = registering ? "Create account" : "Sign in";
  document.querySelector("#loginButton").textContent = registering ? "Register" : "Login";
  document.querySelector("#toggleRegisterButton").textContent = registering ? "Back to sign in" : "Create an account";
  document.querySelector("#loginError").textContent = "";
});

document.querySelector("#forgotPasswordButton").addEventListener("click", async () => {
  const email = document.querySelector("#email").value.trim();
  const error = document.querySelector("#loginError");
  error.textContent = "";

  if (!email) {
    error.textContent = "Enter your email first.";
    return;
  }

  try {
    const reset = await api("/auth/password-reset/request", {
      method: "POST",
      body: JSON.stringify({ email })
    });
    if (reset) {
      const url = `${window.location.origin}/reset-password/${reset.token}`;
      error.innerHTML = `Reset link: <a href="${url}" target="_blank">${url}</a>`;
    } else {
      error.textContent = "If that account exists, a reset link has been generated.";
    }
  } catch (err) {
    error.textContent = err.message;
  }
});

document.querySelector("#bootstrapAdminButton").addEventListener("click", () => {
  registering = false;
  bootstrappingAdmin = true;
  document.querySelector("#registerFields").classList.remove("hidden");
  document.querySelector("#adminSetupFields").classList.remove("hidden");
  document.querySelector("#authTitle").textContent = "Create first admin";
  document.querySelector("#loginButton").textContent = "Create admin";
  document.querySelector("#toggleRegisterButton").textContent = "Create an account";
  document.querySelector("#loginError").textContent = "";
});

document.querySelector("#createDashboardButton").addEventListener("click", () => {
  document.querySelector("#dashboardCreateForm").classList.toggle("hidden");
});

document.querySelector("#manageUsersButton").addEventListener("click", async () => {
  const panel = document.querySelector("#userManagementPanel");
  panel.classList.toggle("hidden");
  if (!panel.classList.contains("hidden")) {
    try {
      await loadUsers();
    } catch (err) {
      document.querySelector("#userManagementMessage").textContent = err.message;
    }
  }
});

document.querySelector("#createSectionButton").addEventListener("click", () => {
  document.querySelector("#sectionCreateForm").classList.toggle("hidden");
});

document.querySelector("#dashboardCreateForm").addEventListener("submit", async event => {
  event.preventDefault();
  try {
    await api("/dashboards", {
      method: "POST",
      body: JSON.stringify({
        name: document.querySelector("#newDashboardName").value,
        description: document.querySelector("#newDashboardDescription").value
      })
    });
    event.target.reset();
    event.target.classList.add("hidden");
    await loadDashboards();
  } catch (err) {
    window.alert(err.message);
  }
});

document.querySelector("#sectionCreateForm").addEventListener("submit", async event => {
  event.preventDefault();
  const labels = document.querySelector("#newSectionLabels").value.split(",").map(value => value.trim()).filter(Boolean);
  const values = document.querySelector("#newSectionValues").value.split(",").map(value => Number(value.trim())).filter(Number.isFinite);

  try {
    await api("/sections", {
      method: "POST",
      body: JSON.stringify({
        dashboard_id: Number(document.querySelector("#dashboardSelect").value),
        name: document.querySelector("#newSectionName").value,
        chart_type: document.querySelector("#newSectionChart").value,
        chart_headline: document.querySelector("#newSectionHeadline").value,
        chart_change: document.querySelector("#newSectionChange").value,
        chart_labels: labels,
        chart_values: values
      })
    });
    event.target.reset();
    event.target.classList.add("hidden");
    await loadDashboard(document.querySelector("#dashboardSelect").value);
  } catch (err) {
    window.alert(err.message);
  }
});

document.querySelector("#logoutButton").addEventListener("click", logout);
document.querySelector("#dashboardSelect").addEventListener("change", event => loadDashboard(event.target.value));
document.querySelector("#shareButton").addEventListener("click", createShareLink);
document.querySelector("#deleteDashboardButton").addEventListener("click", async () => {
  const select = document.querySelector("#dashboardSelect");
  const dashboardId = Number(select.value);
  const dashboardName = select.options[select.selectedIndex]?.text || "this dashboard";

  if (!dashboardId || !window.confirm(`Delete "${dashboardName}" and all of its sections and reviews?`)) {
    return;
  }

  try {
    await api(`/dashboards/${dashboardId}`, { method: "DELETE" });
    await loadDashboards();
  } catch (err) {
    window.alert(err.message);
  }
});

document.querySelector("#adminInvitationForm").addEventListener("submit", async event => {
  event.preventDefault();
  const email = document.querySelector("#adminInvitationEmail").value.trim();
  const result = document.querySelector("#adminInvitationResult");

  try {
    const invitation = await api("/auth/admin-invitations", {
      method: "POST",
      body: JSON.stringify({ email })
    });
    const url = `${window.location.origin}/admin/invite/${invitation.token}`;
    result.classList.remove("hidden");
    result.innerHTML = `One-time admin link for ${invitation.email}:<br><a href="${url}" target="_blank">${url}</a><br><small>Expires after 24 hours or after first use.</small>`;
  } catch (err) {
    result.classList.remove("hidden");
    result.textContent = err.message;
  }
});

document.querySelector("#cancelSectionEdit").addEventListener("click", () => {
  document.querySelector("#sectionEditModal").classList.add("hidden");
});

document.querySelector("#sectionEditModal").addEventListener("click", event => {
  if (event.target === event.currentTarget) event.currentTarget.classList.add("hidden");
});

document.querySelector("#sectionEditForm").addEventListener("submit", async event => {
  event.preventDefault();
  const labels = document.querySelector("#editSectionLabels").value.split(",").map(value => value.trim()).filter(Boolean);
  const values = document.querySelector("#editSectionValues").value.split(",").map(value => Number(value.trim())).filter(Number.isFinite);
  const sectionId = document.querySelector("#editSectionId").value;

  try {
    await api(`/sections/${sectionId}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: document.querySelector("#editSectionName").value,
        chart_type: document.querySelector("#editSectionChart").value,
        chart_headline: document.querySelector("#editSectionHeadline").value,
        chart_change: document.querySelector("#editSectionChange").value,
        chart_labels: labels,
        chart_values: values
      })
    });
    document.querySelector("#sectionEditModal").classList.add("hidden");
    await loadDashboard(document.querySelector("#dashboardSelect").value);
  } catch (err) {
    window.alert(err.message);
  }
});

if (token) startApp();
