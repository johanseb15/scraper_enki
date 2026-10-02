// Presentation only: preserve the API amount without doing monetary arithmetic.
export function formatDecisionMoney(value: number | null | undefined, currency = "ARS") {
  if (value == null) return "—";
  const amount = value.toLocaleString("es-AR", {
    minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
    maximumFractionDigits: 2,
  });
  if (currency === "ARS") return `$${amount}`;
  if (currency === "USD") return `${amount} USD`;
  return `${amount} · moneda sin confirmar`;
}
