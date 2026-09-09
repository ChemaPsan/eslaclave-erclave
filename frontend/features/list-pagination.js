const DEFAULT_PAGE_SIZE = 25;
const LIST_SELECTORS = [".catalog-grid", ".product-catalog-grid", ".admin-list", ".data-table"];

function listItems(container) {
  return [...container.children].filter((node) => !node.classList.contains("table-head"));
}

export function installListPagination(root, labels, pageSize = DEFAULT_PAGE_SIZE) {
  const containers = [...root.querySelectorAll(LIST_SELECTORS.join(","))];
  containers.forEach((container, containerIndex) => {
    if (container.closest(".standard-report-section")) return;
    const items = listItems(container);
    if (items.length <= pageSize) return;

    let currentPage = 0;
    const pageCount = Math.ceil(items.length / pageSize);
    const navigation = document.createElement("nav");
    navigation.className = "list-pagination";
    navigation.dataset.paginationFor = String(containerIndex);
    navigation.setAttribute("aria-label", labels.navigation);
    navigation.innerHTML = `
      <button class="secondary-action small-action" type="button" data-page-previous>${labels.previous}</button>
      <span aria-live="polite"></span>
      <button class="secondary-action small-action" type="button" data-page-next>${labels.next}</button>
    `;
    container.insertAdjacentElement("afterend", navigation);

    const previous = navigation.querySelector("[data-page-previous]");
    const next = navigation.querySelector("[data-page-next]");
    const summary = navigation.querySelector("span");
    const renderPage = () => {
      const start = currentPage * pageSize;
      const end = Math.min(start + pageSize, items.length);
      items.forEach((item, index) => { item.hidden = index < start || index >= end; });
      previous.disabled = currentPage === 0;
      next.disabled = currentPage === pageCount - 1;
      summary.textContent = labels.summary
        .replace("{from}", String(start + 1))
        .replace("{to}", String(end))
        .replace("{total}", String(items.length));
    };
    previous.addEventListener("click", () => { currentPage -= 1; renderPage(); container.scrollIntoView({ block: "start" }); });
    next.addEventListener("click", () => { currentPage += 1; renderPage(); container.scrollIntoView({ block: "start" }); });
    renderPage();
  });
}
