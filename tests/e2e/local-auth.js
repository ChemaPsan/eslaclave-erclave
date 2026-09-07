const FIREBASE_APP_URL = "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";
const FIREBASE_AUTH_URL = "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";

const firebaseAppStub = `
  const apps = [];
  export function getApps() { return apps; }
  export function initializeApp(config) { const app = { config }; apps.push(app); return app; }
`;

const firebaseAuthStub = `
  const auth = { currentUser: null, emulatorUrl: "http://127.0.0.1:9099" };
  let authListener = null;
  export function getAuth() { return auth; }
  export function connectAuthEmulator(instance, url) { instance.emulatorUrl = url.replace(/\\/$/, ""); }
  export function onAuthStateChanged(instance, callback) {
    authListener = callback;
    queueMicrotask(() => callback(instance.currentUser));
    return () => { if (authListener === callback) authListener = null; };
  }
  export async function signInWithEmailAndPassword(instance, email, password) {
    const response = await fetch(instance.emulatorUrl + "/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo-api-key", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password, returnSecureToken: true })
    });
    const payload = await response.json();
    if (!response.ok) {
      const error = new Error("Firebase emulator rejected the credentials.");
      error.code = "auth/invalid-credential";
      throw error;
    }
    const user = { email: payload.email || email, displayName: payload.displayName || "", getIdToken: async () => payload.idToken };
    instance.currentUser = user;
    authListener?.(user);
    return { user };
  }
  export async function signOut(instance) { instance.currentUser = null; authListener?.(null); }
  export async function sendPasswordResetEmail() { return undefined; }
`;

async function installLocalAuth(page) {
  await page.route(FIREBASE_APP_URL, (route) => route.fulfill({
    status: 200,
    contentType: "application/javascript",
    headers: { "access-control-allow-origin": "*" },
    body: firebaseAppStub
  }));
  await page.route(FIREBASE_AUTH_URL, (route) => route.fulfill({
    status: 200,
    contentType: "application/javascript",
    headers: { "access-control-allow-origin": "*" },
    body: firebaseAuthStub
  }));
  await page.addInitScript(() => {
    localStorage.clear();
    localStorage.setItem("erclave-lang", "es");
    localStorage.setItem("erclave-api-mode", "api");
    localStorage.setItem("erclave-inventory-api-mode", "api");
    const bases = {
      "erclave-api-base-url": "http://127.0.0.1:8000",
      "erclave-production-api-base-url": "http://127.0.0.1:8002",
      "erclave-inventory-api-base-url": "http://127.0.0.1:8004",
      "erclave-hr-api-base-url": "http://127.0.0.1:8006",
      "erclave-sales-api-base-url": "http://127.0.0.1:8008",
      "erclave-purchasing-api-base-url": "http://127.0.0.1:8010",
      "erclave-maintenance-api-base-url": "http://127.0.0.1:8012"
    };
    Object.entries(bases).forEach(([key, value]) => localStorage.setItem(key, value));
  });
}

async function signInAsLocalAdmin(page) {
  await page.goto("/");
  await page.locator("[data-form='auth-email'] [name='email']").fill("admin.qa@erclave.local");
  await page.locator("[data-form='auth-email'] [name='password']").fill("LocalDemo123!");
  await page.locator("[data-form='auth-email'] [type='submit']").click();
  await page.locator("#authGate").waitFor({ state: "hidden" });
  await page.locator("#contextUser").filter({ hasText: "admin.qa@erclave.local" }).waitFor();
}

module.exports = { installLocalAuth, signInAsLocalAdmin };
