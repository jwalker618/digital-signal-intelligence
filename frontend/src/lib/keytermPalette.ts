import type { CSSProperties } from "react";

import {
  LucideIcon,
  CloudAlert,
  ShieldCheck,
  ShieldQuestionMark,
  ShieldX,
} from "lucide-react";

export interface PaletteEntry {
  color: string;
  icon?: LucideIcon;
}

export const accentVars = (color: string): CSSProperties =>
  ({ "--accent": `var(--${color})` }) as CSSProperties;

export function getPalette(
  palette: Record<string, PaletteEntry>,
  key: string,
): PaletteEntry {
  const fallback = { 
      color: "generate-text-maybe", 
      icon: CloudAlert 
  };

  if (!key) return fallback;

  return palette[key.toLowerCase()] ?? fallback;
}

export interface KeyTermVisual {
  color: string;
  icon: LucideIcon;
}

export const KEYTERM: Record<string, KeyTermVisual> = {

  approve: { color: "generate-text-good",   icon: ShieldCheck },
  refer:   { color: "generate-text-maybe",  icon: ShieldQuestionMark },
  decline: { color: "generate-text-bad",    icon: ShieldX },
  pending: { color: "generate-text-maybe",  icon: ShieldQuestionMark },

};
