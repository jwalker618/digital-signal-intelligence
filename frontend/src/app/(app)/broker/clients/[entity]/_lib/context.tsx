"use client";

import { createContext, useContext } from "react";
import type { ClientWorkbenchResponse } from "@/types/portal";

/**
 * Client-workbench data is fetched once in the layout and shared to all 10
 * tabs via context — no per-tab refetch. Tabs read `useClientWorkbench()`.
 */
export const ClientWorkbenchContext = createContext<ClientWorkbenchResponse | null>(
  null,
);

export function useClientWorkbench(): ClientWorkbenchResponse | null {
  return useContext(ClientWorkbenchContext);
}
