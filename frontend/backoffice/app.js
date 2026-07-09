import { getApiBaseUrl } from "../api/config.js";
import { deleteBackofficeTenant, listBackofficeTenants, listBackofficeUsage, onboardTenant, setBackofficeTenantStatus } from "../api/backoffice.js";
import { isFirebaseAuthConfigured, onAuthChanged, sendPasswordReset, signInWithEmail, signOutUser } from "../auth.js";


const app = document.getElementById("backofficeApp");
const moduleOptions = [
  { code: "admin", label: "Administracion", required: true },
  { code: "production", label: "Produccion" },
  { code: "inventory", label: "Almacenes" },
  { code: "sales", label: "Ventas" },
  { code: "integrations", label: "Integraciones" }
];
const defaultUsageToDate = new Date().toISOString().slice(0, 10);
const defaultUsageFromDate = new Date(Date.now() - 29 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

const state = {
  activeTab: localStorage.getItem("erclave-backoffice-tab") || "onboarding",
  auth: {
    status: isFirebaseAuthConfigured() ? "loading" : "disabled",
    user: null,
    email: "",
    error: "",
    notice: ""
  },
  access: {
    status: "idle",
    error: ""
  },
  onboarding: {
    status: "idle",
    error: "",
    result: null
  },
  tenantAdmin: {
    status: "idle",
    search: "",
    error: "",
    tenants: [],
    actionTenantId: ""
  },
  usage: {
    status: "idle",
    fromDate: defaultUsageFromDate,
    toDate: defaultUsageToDate,
    tenantId: "",
    error: "",
    rows: [],
    summary: {
      tenants: 0,
      days: 0,
      active_users: 0,
      api_requests: 0,
      storage_mb: "0",
      estimated_cost_mxn: "0"
    }
  }
};


function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function slugify(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}


function createLocalId(prefix, value) {
  const base = slugify(value).replaceAll("-", "_") || "default";
  return `${prefix}_${base}`.slice(0, 40);
}


function readFormValue(formData, key) {
  return String(formData.get(key) || "").trim();
}


function formatNumber(value) {
  return Number(value || 0).toLocaleString("es-MX");
}


function formatMoney(value) {
  return Number(value || 0).toLocaleString("es-MX", { style: "currency", currency: "MXN" });
}


function buildOnboardingPayload(form) {
  const formData = new FormData(form);
  const commercialName = readFormValue(formData, "commercial_name");
  const legalName = readFormValue(formData, "legal_name") || commercialName;
  const ownerEmail = readFormValue(formData, "owner_email").toLowerCase();
  const ownerName = readFormValue(formData, "owner_name");
  const branchName = readFormValue(formData, "branch_name");
  const legalEntityName = readFormValue(formData, "legal_entity_name") || legalName;
  const legalEntityId = legalEntityName ? createLocalId("rso", legalEntityName) : "";
  const branchId = branchName ? createLocalId("suc", branchName) : "";
  const modules = moduleOptions
    .filter((item) => item.required || formData.get(`module_${item.code}`) === "on")
    .map((item) => ({
      module_code: item.code,
      status: "active",
      limits: {},
      source: "manual"
    }));

  return {
    slug: readFormValue(formData, "slug") || slugify(commercialName),
    commercial_name: commercialName,
    legal_name: legalName,
    plan_id: readFormValue(formData, "plan_id") || "manual",
    source: {
      type: "backoffice",
      id: `manual-${Date.now()}`
    },
    owner: {
      email: ownerEmail,
      display_name: ownerName,
      status: "invited",
      branch_ids: branchId ? [branchId] : ["*"]
    },
    organization_profile: {
      corporate: {
        commercial_name: commercialName,
        legal_name: legalName,
        tax_id: readFormValue(formData, "tax_id"),
        phone: readFormValue(formData, "corporate_phone"),
        contact_name: ownerName,
        contact_email: ownerEmail,
        contact_phone: readFormValue(formData, "owner_phone"),
        contact_position: readFormValue(formData, "owner_position") || "Administrador principal"
      },
      legal_entities: legalEntityName
        ? [
            {
              id: legalEntityId,
              legal_name: legalEntityName,
              tax_id: readFormValue(formData, "tax_id"),
              fiscal_regime: readFormValue(formData, "fiscal_regime"),
              cfdi_usage: readFormValue(formData, "cfdi_usage"),
              fiscal_address: readFormValue(formData, "fiscal_address"),
              contact_name: ownerName,
              contact_email: ownerEmail,
              contact_phone: readFormValue(formData, "owner_phone"),
              contact_position: readFormValue(formData, "owner_position") || "Administrador principal",
              status: "active"
            }
          ]
        : [],
      branches: branchName
        ? [
            {
              id: branchId,
              name: branchName,
              code: readFormValue(formData, "branch_code"),
              legal_entity_id: legalEntityId || null,
              address: readFormValue(formData, "branch_address"),
              phone: readFormValue(formData, "branch_phone"),
              status: "active"
            }
          ]
        : []
    },
    modules
  };
}


function renderAuthScreen() {
  const isLoading = state.auth.status === "loading";
  app.innerHTML = `
    <section class="auth-layout">
      <div class="auth-panel">
        <p class="eyebrow">ERClave Backoffice</p>
        <h1>Operacion interna EsLaClave</h1>
        <p class="subcopy">Acceso reservado para administradores internos. Desde aqui se crean tenants, owner inicial, modulos contratados e invitacion Firebase.</p>
      </div>
      <form class="login-card" data-form="login">
        <h2>Iniciar sesion</h2>
        ${state.auth.error ? `<p class="error-box">${escapeHtml(state.auth.error)}</p>` : ""}
        ${state.auth.notice ? `<p class="notice-box">${escapeHtml(state.auth.notice)}</p>` : ""}
        <label>
          <span>Correo interno</span>
          <input name="email" type="email" autocomplete="email" value="${escapeHtml(state.auth.email)}" required ${isLoading ? "disabled" : ""}>
        </label>
        <label>
          <span>Contrasena</span>
          <input name="password" type="password" autocomplete="current-password" required ${isLoading ? "disabled" : ""}>
        </label>
        <button class="primary-button" type="submit" ${isLoading ? "disabled" : ""}>Entrar</button>
        <button class="link-button" type="button" data-action="reset" ${isLoading ? "disabled" : ""}>Recuperar contrasena</button>
      </form>
    </section>
  `;
  app.querySelector("[data-form='login']")?.addEventListener("submit", handleLogin);
  app.querySelector("[data-action='reset']")?.addEventListener("click", handleReset);
}


function renderBackoffice() {
  const userEmail = state.auth.user?.email || "";
  const result = state.onboarding.result;
  app.innerHTML = `
    <section class="topbar">
      <div>
        <p class="eyebrow">Backoffice</p>
        <h1>Backoffice ERClave</h1>
      </div>
      <div class="session-chip">
        <span>${escapeHtml(userEmail)}</span>
        <button type="button" data-action="logout">Cerrar sesion</button>
      </div>
    </section>

    ${renderBackofficeTabs()}
    ${state.activeTab === "onboarding" ? `
    <section class="work-area">
      <form class="tenant-form" data-form="tenant-onboarding">
        <header class="section-header">
          <div>
            <p class="eyebrow">Provisioning interno</p>
            <h2>Nuevo cliente</h2>
          </div>
          <span class="api-pill">${escapeHtml(getApiBaseUrl())}</span>
        </header>

        ${state.onboarding.error ? `<p class="error-box">${escapeHtml(state.onboarding.error)}</p>` : ""}

        <div class="form-grid">
          <label>
            <span>Nombre comercial</span>
            <input name="commercial_name" required placeholder="Cliente Nuevo">
          </label>
          <label>
            <span>Slug</span>
            <input name="slug" placeholder="cliente-nuevo">
          </label>
          <label>
            <span>Razon social principal</span>
            <input name="legal_name" placeholder="Cliente Nuevo S.A. de C.V.">
          </label>
          <label>
            <span>RFC</span>
            <input name="tax_id" placeholder="XAXX010101000">
          </label>
          <label>
            <span>Plan</span>
            <input name="plan_id" value="qa-demo">
          </label>
          <label>
            <span>Telefono corporativo</span>
            <input name="corporate_phone" placeholder="+52 55 0000 0000">
          </label>
        </div>

        <div class="form-section">
          <h3>Owner inicial</h3>
          <div class="form-grid">
            <label>
              <span>Nombre</span>
              <input name="owner_name" required placeholder="Admin Cliente">
            </label>
            <label>
              <span>Email</span>
              <input name="owner_email" type="email" required placeholder="admin@cliente.com">
            </label>
            <label>
              <span>Telefono</span>
              <input name="owner_phone" placeholder="+52 55 0000 0000">
            </label>
            <label>
              <span>Puesto</span>
              <input name="owner_position" placeholder="Direccion administrativa">
            </label>
          </div>
        </div>

        <div class="form-section">
          <h3>Fiscal y sucursal inicial</h3>
          <div class="form-grid">
            <label>
              <span>Entidad fiscal</span>
              <input name="legal_entity_name" placeholder="Cliente Nuevo S.A. de C.V.">
            </label>
            <label>
              <span>Regimen fiscal</span>
              <input name="fiscal_regime" placeholder="601 General de Ley Personas Morales">
            </label>
            <label>
              <span>Uso CFDI default</span>
              <input name="cfdi_usage" placeholder="G03 Gastos en general">
            </label>
            <label>
              <span>Direccion fiscal</span>
              <input name="fiscal_address" placeholder="Direccion fiscal">
            </label>
            <label>
              <span>Sucursal inicial</span>
              <input name="branch_name" placeholder="Matriz">
            </label>
            <label>
              <span>Codigo sucursal</span>
              <input name="branch_code" placeholder="MTZ">
            </label>
            <label>
              <span>Telefono sucursal</span>
              <input name="branch_phone" placeholder="+52 55 0000 0000">
            </label>
            <label>
              <span>Direccion sucursal</span>
              <input name="branch_address" placeholder="Direccion operativa">
            </label>
          </div>
        </div>

        <div class="form-section compact">
          <h3>Modulos iniciales</h3>
          <div class="module-grid">
            ${moduleOptions.map((item) => `
              <label class="module-check">
                <input type="checkbox" name="module_${item.code}" ${item.required ? "checked disabled" : ""}>
                <span>${escapeHtml(item.label)}</span>
              </label>
            `).join("")}
          </div>
        </div>

        <footer class="form-actions">
          <button class="primary-button" type="submit" ${state.onboarding.status === "loading" ? "disabled" : ""}>Crear tenant</button>
        </footer>
      </form>

      <aside class="result-panel">
        <h2>Resultado</h2>
        ${result ? renderResult(result) : `<p class="empty-state">Cuando el alta termine veras el tenant, owner, modulos e invitacion generada.</p>`}
      </aside>
    </section>
    ` : state.activeTab === "tenant-admin" ? renderTenantAdminPanel() : renderUsagePanel()}
  `;

  app.querySelector("[data-action='logout']")?.addEventListener("click", handleLogout);
  app.querySelectorAll("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => setBackofficeTab(button.dataset.tab));
  });
  app.querySelector("[data-form='tenant-onboarding']")?.addEventListener("submit", handleOnboardingSubmit);
  app.querySelector("[name='commercial_name']")?.addEventListener("input", handleCommercialNameInput);
  app.querySelector("[name='slug']")?.addEventListener("input", (event) => {
    event.currentTarget.dataset.touched = "true";
  });
  app.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", () => copyText(button.dataset.copy || ""));
  });
  bindTenantAdminActions();
  bindUsageActions();
}


function renderAccessGate() {
  const userEmail = state.auth.user?.email || "";
  const isDenied = state.access.status === "denied";
  app.innerHTML = `
    <section class="topbar">
      <div>
        <p class="eyebrow">Backoffice</p>
        <h1>Acceso interno</h1>
      </div>
      <div class="session-chip">
        <span>${escapeHtml(userEmail)}</span>
        <button type="button" data-action="logout">Cerrar sesion</button>
      </div>
    </section>

    <section class="auth-layout compact-auth">
      <div class="login-card">
        <p class="eyebrow">${isDenied ? "Acceso restringido" : "Validando acceso"}</p>
        <h2>${isDenied ? "Tu cuenta no tiene permisos de backoffice" : "Revisando lista interna"}</h2>
        <p class="${isDenied ? "error-box" : "notice-box"}">
          ${isDenied
            ? escapeHtml(state.access.error || "Este portal esta reservado para administradores internos de EsLaClave.")
            : "Estamos validando que tu correo este autorizado para operar tenants."}
        </p>
        ${isDenied ? `<p class="empty-state">La creacion como owner de un tenant no otorga acceso al backoffice.</p>` : ""}
      </div>
    </section>
  `;
  app.querySelector("[data-action='logout']")?.addEventListener("click", handleLogout);
}


function renderBackofficeTabs() {
  return `
    <nav class="backoffice-tabs" aria-label="Secciones de backoffice">
      <button type="button" data-tab="onboarding" class="${state.activeTab === "onboarding" ? "active" : ""}">Alta de tenant</button>
      <button type="button" data-tab="tenant-admin" class="${state.activeTab === "tenant-admin" ? "active" : ""}">Administracion de tenants</button>
      <button type="button" data-tab="usage" class="${state.activeTab === "usage" ? "active" : ""}">Uso y costos</button>
    </nav>
  `;
}


function renderTenantAdminPanel() {
  const tenants = state.tenantAdmin.tenants || [];
  const isLoading = state.tenantAdmin.status === "loading";
  return `
    <section class="tenant-admin-layout">
      <section class="tenant-admin-panel">
        <header class="section-header">
          <div>
            <p class="eyebrow">Administracion interna</p>
            <h2>Tenants</h2>
          </div>
          <span class="api-pill">${escapeHtml(getApiBaseUrl())}</span>
        </header>

        <form class="tenant-searchbar" data-form="tenant-search">
          <label>
            <span>Buscar por nombre comercial, slug o razon social</span>
            <input name="search" type="search" value="${escapeHtml(state.tenantAdmin.search)}" placeholder="cliente, slug o razon social">
          </label>
          <button class="secondary-button inline" type="submit" ${isLoading ? "disabled" : ""}>Buscar</button>
          <button class="secondary-button inline" type="button" data-action="refresh-tenants" ${isLoading ? "disabled" : ""}>Actualizar</button>
        </form>

        ${state.tenantAdmin.error ? `<p class="error-box">${escapeHtml(state.tenantAdmin.error)}</p>` : ""}
        ${isLoading ? `<p class="notice-box">Cargando tenants...</p>` : ""}

        <div class="tenant-table">
          <div class="tenant-table-head">
            <span>Tenant</span>
            <span>Owner</span>
            <span>Estado</span>
            <span>Modulos</span>
            <span>Acciones</span>
          </div>
          ${tenants.map(renderTenantRow).join("")}
        </div>
        ${!isLoading && !tenants.length ? `<p class="empty-state">No hay tenants que coincidan con la busqueda.</p>` : ""}
      </section>

      <aside class="result-panel">
        <h2>Operacion segura</h2>
        <p class="empty-state">Suspender bloquea el acceso de los usuarios del tenant. Eliminar borra configuracion, roles, membresias, modulos y datos administrativos del tenant; solo elimina identidad Firebase si el usuario ya no pertenece a ningun otro tenant.</p>
      </aside>
    </section>
  `;
}


function renderUsagePanel() {
  const rows = state.usage.rows || [];
  const summary = state.usage.summary || {};
  const isLoading = state.usage.status === "loading";
  return `
    <section class="tenant-admin-layout">
      <section class="tenant-admin-panel">
        <header class="section-header">
          <div>
            <p class="eyebrow">Medicion SaaS</p>
            <h2>Uso y costos</h2>
          </div>
          <span class="api-pill">${escapeHtml(getApiBaseUrl())}</span>
        </header>

        <form class="usage-filterbar" data-form="usage-search">
          <label>
            <span>Desde</span>
            <input name="from_date" type="date" value="${escapeHtml(state.usage.fromDate)}">
          </label>
          <label>
            <span>Hasta</span>
            <input name="to_date" type="date" value="${escapeHtml(state.usage.toDate)}">
          </label>
          <label>
            <span>Tenant ID</span>
            <input name="tenant_id" value="${escapeHtml(state.usage.tenantId)}" placeholder="Todos">
          </label>
          <button class="secondary-button inline" type="submit" ${isLoading ? "disabled" : ""}>Consultar</button>
          <button class="secondary-button inline" type="button" data-action="refresh-usage" ${isLoading ? "disabled" : ""}>Actualizar</button>
        </form>

        ${state.usage.error ? `<p class="error-box">${escapeHtml(state.usage.error)}</p>` : ""}
        ${isLoading ? `<p class="notice-box">Cargando metricas...</p>` : ""}

        <div class="usage-summary-grid">
          <div class="result-card"><span>Tenants</span><strong>${formatNumber(summary.tenants)}</strong></div>
          <div class="result-card"><span>Dias</span><strong>${formatNumber(summary.days)}</strong></div>
          <div class="result-card"><span>Usuarios activos</span><strong>${formatNumber(summary.active_users)}</strong></div>
          <div class="result-card"><span>Requests API</span><strong>${formatNumber(summary.api_requests)}</strong></div>
          <div class="result-card"><span>Storage MB</span><strong>${formatNumber(summary.storage_mb)}</strong></div>
          <div class="result-card"><span>Costo estimado</span><strong>${formatMoney(summary.estimated_cost_mxn)}</strong></div>
        </div>

        <div class="usage-table">
          <div class="usage-table-head">
            <span>Fecha</span>
            <span>Tenant</span>
            <span>Usuarios</span>
            <span>Requests</span>
            <span>Storage</span>
            <span>Costo</span>
          </div>
          ${rows.map(renderUsageRow).join("")}
        </div>
        ${!isLoading && !rows.length ? `<p class="empty-state">No hay metricas de uso para el rango seleccionado.</p>` : ""}
      </section>

      <aside class="result-panel">
        <h2>Criterio de medicion</h2>
        <p class="empty-state">La tabla muestra agregados diarios por tenant desde admin.tenant_usage_daily. Este primer corte es de consulta; la ingesta queda reservada para jobs internos o integraciones controladas.</p>
      </aside>
    </section>
  `;
}


function renderUsageRow(row) {
  return `
    <article class="usage-row">
      <div>
        <strong>${escapeHtml(row.usage_date)}</strong>
        <small>${escapeHtml(row.source || "sin fuente")}</small>
      </div>
      <div>
        <strong>${escapeHtml(row.tenant_name)}</strong>
        <small>${escapeHtml(row.tenant_slug)} - ${escapeHtml(row.tenant_id)}</small>
      </div>
      <div><span>${formatNumber(row.active_users)}</span></div>
      <div><span>${formatNumber(row.api_requests)}</span></div>
      <div><span>${formatNumber(row.storage_mb)} MB</span></div>
      <div><span>${formatMoney(row.estimated_cost_mxn)}</span></div>
    </article>
  `;
}


function renderTenantRow(tenant) {
  const isBusy = state.tenantAdmin.actionTenantId === tenant.id;
  const isSuspended = tenant.status === "suspended";
  const modules = (tenant.modules || []).join(", ") || "Sin modulos";
  return `
    <article class="tenant-row">
      <div>
        <strong>${escapeHtml(tenant.commercial_name)}</strong>
        <span>${escapeHtml(tenant.slug)} - ${escapeHtml(tenant.legal_name || "Sin razon social")}</span>
        <small>${escapeHtml(tenant.id)} - Plan ${escapeHtml(tenant.plan_id || "sin plan")}</small>
      </div>
      <div>
        <span>${escapeHtml(tenant.owner_email || "Sin owner")}</span>
        <small>${Number(tenant.active_memberships || 0)} activos / ${Number(tenant.total_memberships || 0)} usuarios</small>
      </div>
      <div>
        <span class="status-pill ${escapeHtml(tenant.status)}">${escapeHtml(tenant.status)}</span>
        <small>${Number(tenant.legal_entities_count || 0)} razones - ${Number(tenant.branches_count || 0)} sucursales</small>
      </div>
      <div>
        <span>${escapeHtml(modules)}</span>
      </div>
      <div class="tenant-actions">
        <button class="secondary-button inline" type="button" data-action="toggle-tenant-status" data-tenant-id="${escapeHtml(tenant.id)}" data-status="${isSuspended ? "active" : "suspended"}" ${isBusy ? "disabled" : ""}>
          ${isSuspended ? "Reactivar" : "Suspender"}
        </button>
        <button class="secondary-button inline danger" type="button" data-action="delete-tenant" data-tenant-id="${escapeHtml(tenant.id)}" data-name="${escapeHtml(tenant.commercial_name)}" ${isBusy ? "disabled" : ""}>
          Eliminar
        </button>
      </div>
    </article>
  `;
}


function renderResult(result) {
  const invitation = result.invitation || {};
  return `
    <div class="result-stack">
      <div class="result-card">
        <span>Tenant</span>
        <strong>${escapeHtml(result.tenant?.commercial_name)}</strong>
        <small>${escapeHtml(result.tenant?.id)} - ${escapeHtml(result.tenant?.status)}</small>
      </div>
      <div class="result-card">
        <span>Owner</span>
        <strong>${escapeHtml(result.owner?.email)}</strong>
        <small>${escapeHtml(result.owner?.status)} - ${(result.owner?.roles || []).join(", ")}</small>
      </div>
      <div class="result-card">
        <span>Modulos</span>
        <strong>${escapeHtml((result.entitlements || []).map((item) => item.module_code).join(", "))}</strong>
      </div>
      <div class="result-card">
        <span>Invitacion</span>
        <strong>${invitation.email_sent ? "Correo enviado" : invitation.delivery || "Pendiente"}</strong>
        <small>${escapeHtml(invitation.email || "")}</small>
        ${invitation.reset_link ? `<button class="secondary-button" type="button" data-copy="${escapeHtml(invitation.reset_link)}">Copiar link</button>` : ""}
      </div>
    </div>
  `;
}


function render() {
  if (!isFirebaseAuthConfigured()) {
    app.innerHTML = `
      <section class="auth-layout">
        <div class="login-card">
          <h1>Firebase no configurado</h1>
          <p class="error-box">Configura <code>frontend/backoffice/env.js</code> con Firebase Auth para usar el backoffice.</p>
        </div>
      </section>
    `;
    return;
  }
  if (!state.auth.user) {
    renderAuthScreen();
    return;
  }
  if (state.access.status !== "authorized") {
    renderAccessGate();
    return;
  }
  renderBackoffice();
}


function handleLogin(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const email = readFormValue(formData, "email");
  const password = readFormValue(formData, "password");
  state.auth = { ...state.auth, status: "loading", email, error: "", notice: "" };
  render();
  signInWithEmail(email, password).catch((error) => {
    state.auth = { ...state.auth, status: "signed_out", user: null, email, error: error.message || "No se pudo iniciar sesion.", notice: "" };
    render();
  });
}


function handleReset() {
  const emailInput = app.querySelector("[name='email']");
  const email = String(emailInput?.value || state.auth.email || "").trim();
  if (!email) {
    state.auth = { ...state.auth, error: "Escribe el correo interno para enviar recuperacion.", notice: "" };
    render();
    return;
  }
  state.auth = { ...state.auth, status: "loading", email, error: "", notice: "" };
  render();
  sendPasswordReset(email)
    .then(() => {
      state.auth = { ...state.auth, status: "signed_out", notice: `Se envio recuperacion a ${email}.`, error: "" };
      render();
    })
    .catch((error) => {
      state.auth = { ...state.auth, status: "signed_out", error: error.message || "No se pudo enviar recuperacion.", notice: "" };
      render();
    });
}


function handleLogout() {
  signOutUser().catch(() => null);
}


function verifyBackofficeAccess() {
  state.access = { status: "checking", error: "" };
  render();
  listBackofficeTenants("", 1)
    .then((tenants) => {
      state.access = { status: "authorized", error: "" };
      state.tenantAdmin = { ...state.tenantAdmin, status: "ready", tenants, error: "", actionTenantId: "" };
      render();
      if (state.activeTab === "tenant-admin") loadTenantAdmin();
      if (state.activeTab === "usage") loadUsage();
    })
    .catch((error) => {
      state.access = {
        status: "denied",
        error: error.message || "Tu usuario no esta autorizado para usar ERClave Backoffice."
      };
      state.tenantAdmin = { ...state.tenantAdmin, status: "idle", tenants: [], error: "", actionTenantId: "" };
      render();
    });
}


function setBackofficeTab(tab) {
  state.activeTab = tab;
  localStorage.setItem("erclave-backoffice-tab", tab);
  render();
  if (tab === "tenant-admin" && state.tenantAdmin.status === "idle") loadTenantAdmin();
  if (tab === "usage" && state.usage.status === "idle") loadUsage();
}


function loadTenantAdmin(search = state.tenantAdmin.search) {
  state.tenantAdmin = { ...state.tenantAdmin, status: "loading", search, error: "" };
  render();
  listBackofficeTenants(search)
    .then((tenants) => {
      state.tenantAdmin = { ...state.tenantAdmin, status: "ready", tenants, error: "", actionTenantId: "" };
      render();
    })
    .catch((error) => {
      state.tenantAdmin = { ...state.tenantAdmin, status: "error", error: error.message || "No se pudieron cargar tenants.", actionTenantId: "" };
      render();
    });
}


function bindTenantAdminActions() {
  app.querySelector("[data-form='tenant-search']")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    loadTenantAdmin(readFormValue(formData, "search"));
  });
  app.querySelector("[data-action='refresh-tenants']")?.addEventListener("click", () => loadTenantAdmin());
  app.querySelectorAll("[data-action='toggle-tenant-status']").forEach((button) => {
    button.addEventListener("click", () => updateTenantStatus(button.dataset.tenantId, button.dataset.status));
  });
  app.querySelectorAll("[data-action='delete-tenant']").forEach((button) => {
    button.addEventListener("click", () => removeTenant(button.dataset.tenantId, button.dataset.name));
  });
}


function bindUsageActions() {
  app.querySelector("[data-form='usage-search']")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    loadUsage({
      fromDate: readFormValue(formData, "from_date"),
      toDate: readFormValue(formData, "to_date"),
      tenantId: readFormValue(formData, "tenant_id")
    });
  });
  app.querySelector("[data-action='refresh-usage']")?.addEventListener("click", () => loadUsage());
}


function loadUsage(filters = {}) {
  const nextFilters = {
    fromDate: filters.fromDate ?? state.usage.fromDate,
    toDate: filters.toDate ?? state.usage.toDate,
    tenantId: filters.tenantId ?? state.usage.tenantId
  };
  state.usage = { ...state.usage, ...nextFilters, status: "loading", error: "" };
  render();
  listBackofficeUsage(nextFilters)
    .then((response) => {
      state.usage = {
        ...state.usage,
        status: "ready",
        rows: response.data || [],
        summary: response.summary || state.usage.summary,
        error: ""
      };
      render();
    })
    .catch((error) => {
      state.usage = { ...state.usage, status: "error", error: error.message || "No se pudieron cargar metricas de uso." };
      render();
    });
}


function updateTenantStatus(tenantId, status) {
  state.tenantAdmin = { ...state.tenantAdmin, actionTenantId: tenantId, error: "" };
  render();
  setBackofficeTenantStatus(tenantId, status)
    .then(() => loadTenantAdmin())
    .catch((error) => {
      state.tenantAdmin = { ...state.tenantAdmin, actionTenantId: "", error: error.message || "No se pudo actualizar el tenant." };
      render();
    });
}


function removeTenant(tenantId, name) {
  const confirmed = window.confirm(`Eliminar permanentemente el tenant ${name}? Esta accion borra sus datos administrativos y accesos.`);
  if (!confirmed) return;
  state.tenantAdmin = { ...state.tenantAdmin, actionTenantId: tenantId, error: "" };
  render();
  deleteBackofficeTenant(tenantId)
    .then(() => loadTenantAdmin())
    .catch((error) => {
      state.tenantAdmin = { ...state.tenantAdmin, actionTenantId: "", error: error.message || "No se pudo eliminar el tenant." };
      render();
    });
}


function handleCommercialNameInput(event) {
  const slugInput = app.querySelector("[name='slug']");
  if (slugInput && !slugInput.dataset.touched) slugInput.value = slugify(event.target.value);
}


function handleOnboardingSubmit(event) {
  event.preventDefault();
  const payload = buildOnboardingPayload(event.currentTarget);
  state.onboarding = { status: "loading", error: "", result: state.onboarding.result };
  render();
  onboardTenant(payload)
    .then((result) => {
      state.onboarding = { status: "idle", error: "", result };
      render();
    })
    .catch((error) => {
      state.onboarding = { status: "error", error: error.message || "No se pudo crear el tenant.", result: state.onboarding.result };
      render();
    });
}


function copyText(value) {
  if (!value) return;
  navigator.clipboard?.writeText(value).catch(() => null);
}


if (isFirebaseAuthConfigured()) {
  onAuthChanged((user) => {
    state.auth = {
      status: user ? "signed_in" : "signed_out",
      user,
      email: user?.email || state.auth.email || "",
      error: "",
      notice: state.auth.notice || ""
    };
    state.access = { status: user ? "checking" : "idle", error: "" };
    render();
    if (user) verifyBackofficeAccess();
  }).catch((error) => {
    state.auth = { ...state.auth, status: "error", error: error.message || "Firebase Auth no disponible." };
    render();
  });
}

render();
