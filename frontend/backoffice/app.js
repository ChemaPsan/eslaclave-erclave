import { getApiBaseUrl } from "../api/config.js";
import { onboardTenant } from "../api/backoffice.js";
import { isFirebaseAuthConfigured, onAuthChanged, sendPasswordReset, signInWithEmail, signOutUser } from "../auth.js";


const app = document.getElementById("backofficeApp");
const moduleOptions = [
  { code: "admin", label: "Administracion", required: true },
  { code: "production", label: "Produccion" },
  { code: "inventory", label: "Almacenes" },
  { code: "sales", label: "Ventas" },
  { code: "integrations", label: "Integraciones" }
];

const state = {
  auth: {
    status: isFirebaseAuthConfigured() ? "loading" : "disabled",
    user: null,
    email: "",
    error: "",
    notice: ""
  },
  onboarding: {
    status: "idle",
    error: "",
    result: null
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
        <h1>Alta de tenant</h1>
      </div>
      <div class="session-chip">
        <span>${escapeHtml(userEmail)}</span>
        <button type="button" data-action="logout">Cerrar sesion</button>
      </div>
    </section>

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
  `;

  app.querySelector("[data-action='logout']")?.addEventListener("click", handleLogout);
  app.querySelector("[data-form='tenant-onboarding']")?.addEventListener("submit", handleOnboardingSubmit);
  app.querySelector("[name='commercial_name']")?.addEventListener("input", handleCommercialNameInput);
  app.querySelector("[name='slug']")?.addEventListener("input", (event) => {
    event.currentTarget.dataset.touched = "true";
  });
  app.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", () => copyText(button.dataset.copy || ""));
  });
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
    render();
  }).catch((error) => {
    state.auth = { ...state.auth, status: "error", error: error.message || "Firebase Auth no disponible." };
    render();
  });
}

render();
