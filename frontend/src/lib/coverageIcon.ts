import { FileCheck, ShieldCheck, Users, type LucideIcon } from "lucide-react";

/**
 * Per-coverage-line glyph (revised pack uses line-specific icons).
 * PI / E&O → FileCheck, D&O / management liability → Users, else the
 * default ShieldCheck. Shared by client + broker coverage views.
 */
export function lineIcon(line: string): LucideIcon {
  const l = line.toLowerCase();
  if (/pi|professional|e&o|errors/.test(l)) return FileCheck;
  if (/d&o|directors|management/.test(l)) return Users;
  return ShieldCheck;
}
