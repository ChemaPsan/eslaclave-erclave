import { getFirebaseConfig } from "./api/config.js";

const FIREBASE_APP_URL = "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";
const FIREBASE_AUTH_URL = "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";

let firebaseModulesPromise = null;
let authInstance = null;

function withTimeout(promise, timeoutMs, message) {
  let timeoutId;
  const timeout = new Promise((_, reject) => {
    timeoutId = setTimeout(() => reject(new Error(message)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timeoutId));
}

export function isFirebaseAuthConfigured() {
  const config = getFirebaseConfig();
  return Boolean(config?.apiKey && config?.authDomain && config?.appId);
}

async function loadFirebaseModules() {
  if (!firebaseModulesPromise) {
    firebaseModulesPromise = Promise.all([import(FIREBASE_APP_URL), import(FIREBASE_AUTH_URL)]);
  }
  return firebaseModulesPromise;
}

export async function getFirebaseAuth() {
  if (!isFirebaseAuthConfigured()) return null;
  if (authInstance) return authInstance;
  const [{ initializeApp, getApps }, { getAuth }] = await loadFirebaseModules();
  const app = getApps().length ? getApps()[0] : initializeApp(getFirebaseConfig());
  authInstance = getAuth(app);
  return authInstance;
}

export async function onAuthChanged(callback) {
  const auth = await getFirebaseAuth();
  if (!auth) return () => {};
  const [, { onAuthStateChanged }] = await loadFirebaseModules();
  return onAuthStateChanged(auth, callback);
}

export async function signInWithEmail(email, password) {
  const auth = await getFirebaseAuth();
  if (!auth) throw new Error("Firebase Auth no esta configurado.");
  const [, { signInWithEmailAndPassword }] = await loadFirebaseModules();
  return signInWithEmailAndPassword(auth, email, password);
}

function getPasswordResetActionSettings() {
  const returnUrl = new URL(window.location.href);
  returnUrl.search = "";
  returnUrl.hash = "";
  return {
    url: returnUrl.toString(),
    handleCodeInApp: false
  };
}

export async function sendPasswordReset(email) {
  const auth = await getFirebaseAuth();
  if (!auth) throw new Error("Firebase Auth no esta configurado.");
  const [, { sendPasswordResetEmail }] = await loadFirebaseModules();
  return sendPasswordResetEmail(auth, email, getPasswordResetActionSettings());
}

export async function signOutUser() {
  const auth = await getFirebaseAuth();
  if (!auth) return;
  const [, { signOut }] = await loadFirebaseModules();
  await signOut(auth);
}

export async function getAuthToken() {
  const auth = await getFirebaseAuth();
  const user = auth?.currentUser;
  return user
    ? withTimeout(user.getIdToken(), 10000, "Firebase tardo demasiado en entregar el token de sesion. Vuelve a iniciar sesion e intenta de nuevo.")
    : "";
}
