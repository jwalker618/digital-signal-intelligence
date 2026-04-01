/**
 * Shared formatting utilities used across all tabs.
 */

import { fallbackModeToFallbackField } from "next/dist/lib/fallback";

export const formatNum = (num: number | null | undefined, decimals = 1): string =>
  num != null ? Number(num).toFixed(decimals) : "-";

export const formatDollar = (num: number | null | undefined): string =>
  num != null ? `$${Number(num).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "-";

export const formatPct = (num: number | null | undefined): string =>
  num != null ? `${(Number(num) * 100).toFixed(0)}%` : "-";

export const formatKey = (key: string): string =>
  key.replace(/_/g, ' ').toUpperCase();

export const formatText = (
  text: string | null | undefined,
  textCase: "normal" | "upper" | "lower" | "capitalize" = "normal",
  fallback: string = "n/a",
): string => {
  // 1. Safety check (handling null, undefined, or empty strings)
  if (!text) return fallback;

  // 2. Replace underscores with spaces (common for database keys/enums)
  let formatted = text.replace(/_/g, ' ');

  // 3. Handle casing logic
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
  fallback: string = "0"
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
  fallback: string = "0"
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
  } catch (error) {
    console.error("Invalid currency code:", currencyCode);
    return `${value.toLocaleString()}`;
  }
};

export const formatPercent = (
  value: number | null | undefined, 
  decimal: number = 0,
  fallback: string = "0"
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
  fallback: string = "n/a"
): string => {
  if (!dateString) return fallback;

  const date = new Date(dateString);

  // Check if the string actually resulted in a valid date
  if (isNaN(date.getTime())) {
    return fallback;
  }

  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  }).format(date);
};