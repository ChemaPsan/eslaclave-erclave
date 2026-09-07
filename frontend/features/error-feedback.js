import { getApiErrorTone, getLocalizedErrorMessage } from "../i18n/api-errors.js";

export function createErrorFeedback({ getLanguage, notify }) {
  function message(error, fallback = "") {
    return getLocalizedErrorMessage(error, { lang: getLanguage(), fallback });
  }

  function show(error, fallback = "") {
    notify(message(error, fallback), getApiErrorTone(error));
  }

  return Object.freeze({ message, show });
}
