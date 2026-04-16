/**
 * Shared formatting utilities used across all tabs.
 *
 * These are the canonical formatters. Column-driven primitives
 * (ContributionTable, ExpandableGroupTable) apply them via
 * `StandardTableColumn.format`.
 */

export const formatText = (
  text: string | null | undefined,
  textCase: "normal" | "upper" | "lower" | "capitalize" = "normal",
  fallback: string = "n/a",
): string => {
  if (!text) return fallback;

  const formatted = text.replace(/_/g, " ");

  switch (textCase) {
    case "upper":
      return formatted.toUpperCase();
    case "lower":
      return formatted.toLowerCase();
    case "capitalize":
      return formatted.charAt(0).toUpperCase() + formatted.slice(1).toLowerCase();
    default:
      return formatted;
  }
};

export const formatNumber = (
  value: number | null | undefined,
  decimal: number = 0,
  fallback: string = "0",
): string => {
  if (!value) return fallback;

  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: decimal,
    minimumFractionDigits: decimal,
  }).format(value);
};

export const formatCurrency = (
  value: number | null | undefined,
  decimal: number = 0,
  currencyCode: string = "USD",
  fallback: string = "0",
): string => {
  if (value === null || value === undefined || value === 0) {
    return fallback;
  }

  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currencyCode,
      maximumFractionDigits: decimal,
      minimumFractionDigits: decimal,
    }).format(value);
  } catch {
    return value.toLocaleString();
  }
};

export const formatPercent = (
  value: number | null | undefined,
  decimal: number = 0,
  fallback: string = "0",
): string => {
  if (!value) return fallback;

  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: decimal,
    minimumFractionDigits: decimal,
  }).format(value);
};

export const formatDate = (
  dateString: string | null | undefined,
  locale: string = "en-GB",
  fallback: string = "n/a",
): string => {
  if (!dateString) return fallback;

  const date = new Date(dateString);
  if (isNaN(date.getTime())) return fallback;

  return new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
};
