const MUTATION_STARTED_EVENT = "erclave:mutation-started";
const MUTATION_FINISHED_EVENT = "erclave:mutation-finished";

export function installMutationFeedback({ getMessage }) {
  let pendingMutations = 0;
  const temporarilyDisabledButtons = new Set();
  const indicator = document.createElement("div");
  indicator.className = "mutation-feedback";
  indicator.hidden = true;
  indicator.setAttribute("role", "status");
  indicator.setAttribute("aria-live", "polite");
  indicator.setAttribute("aria-atomic", "true");
  indicator.innerHTML = `
    <span class="mutation-feedback__spinner" aria-hidden="true"></span>
    <span class="mutation-feedback__message"></span>
  `;
  document.body.append(indicator);

  const render = () => {
    const isBusy = pendingMutations > 0;
    if (isBusy) {
      document.querySelectorAll("button:not(:disabled)").forEach((button) => {
        button.disabled = true;
        temporarilyDisabledButtons.add(button);
      });
    } else {
      temporarilyDisabledButtons.forEach((button) => {
        if (button.isConnected) button.disabled = false;
      });
      temporarilyDisabledButtons.clear();
    }
    indicator.hidden = !isBusy;
    indicator.querySelector(".mutation-feedback__message").textContent = isBusy ? getMessage() : "";
    document.body.classList.toggle("has-pending-mutation", isBusy);
    if (isBusy) document.body.setAttribute("aria-busy", "true");
    else document.body.removeAttribute("aria-busy");
  };

  window.addEventListener(MUTATION_STARTED_EVENT, () => {
    pendingMutations += 1;
    render();
  });
  window.addEventListener(MUTATION_FINISHED_EVENT, () => {
    pendingMutations = Math.max(0, pendingMutations - 1);
    render();
  });
  window.addEventListener("click", (event) => {
    if (pendingMutations > 0 && !indicator.contains(event.target)) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
  window.addEventListener("keydown", (event) => {
    if (pendingMutations > 0 && ["Enter", " "].includes(event.key)) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
}

export { MUTATION_FINISHED_EVENT, MUTATION_STARTED_EVENT };
