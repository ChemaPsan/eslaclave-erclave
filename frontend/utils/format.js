export function startOfDay(date) {
  const next = new Date(date);
  next.setHours(0, 0, 0, 0);
  return next;
}

export function diffDays(from, to) {
  return Math.round((to - from) / 86400000);
}

export function formatCurrency(value) {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    maximumFractionDigits: 0
  }).format(value);
}

export function formatNumber(value) {
  return new Intl.NumberFormat("es-MX", {
    maximumFractionDigits: 2
  }).format(value);
}
