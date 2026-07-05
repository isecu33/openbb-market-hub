import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function fmtMoney(value, currency = "EUR", digits = 2) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency,
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function fmtNum(value, digits = 2) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function fmtPct(value, digits = 2) {
  if (value === null || value === undefined || isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${fmtNum(value, digits)}%`;
}

export function pnlColor(value) {
  if (value > 0) return "text-[hsl(var(--gain))]";
  if (value < 0) return "text-[hsl(var(--loss))]";
  return "text-muted-foreground";
}
