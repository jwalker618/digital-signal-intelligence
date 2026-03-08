"use client";

import { useEffect } from "react";
import { useDsiStore } from "@/store/dsiStore";
import { Shield, Terminal } from "lucide-react";

export default function AuditLogTab() {
  const { activeSubmission, auditLogs, fetchHistory } = useDsiStore();

  useEffect(() => {
    if (activeSubmission?.submission_code) {
      fetchHistory(activeSubmission.submission_code);
    }
  }, [activeSubmission, fetchHistory]);

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500 pb-12 pt-4">
      <div className="flex items-center gap-3 border-b border-dsi-outline/20 pb-4">
        <Shield className="w-5 h-5 text-dsi-selected" />
        <h2 className="text-lg font-bold tracking-wide">Immutable Ledger</h2>
      </div>

      <div className="border border-dsi-outline/20 rounded-xl overflow-hidden bg-dsi-background/30">
        <div className="overflow-x-auto w-full">
          <table className="w-full text-left border-collapse whitespace-nowrap text-sm">
            <thead>
              <tr className="border-b border-dsi-outline/20 text-dsi-selected font-semibold uppercase tracking-wider text-xs bg-dsi-background/50">
                <th className="py-3 px-4 w-48">Timestamp</th>
                <th className="py-3 px-4 w-48">Event Type</th>
                <th className="py-3 px-4 w-32">Action</th>
                <th className="py-3 px-4">Details</th>
              </tr>
            </thead>
            <tbody className="font-mono text-xs">
              {auditLogs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-8 text-center text-dsi-selected opacity-50">
                    No audit records found for this entity.
                  </td>
                </tr>
              ) : (
                auditLogs.map((log) => (
                  <tr key={log.id} className="border-b border-dsi-outline/10 hover:bg-dsi-selected/5 transition-colors">
                    <td className="py-3 px-4 opacity-70">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <span className="bg-dsi-selected/10 text-dsi-selected px-2 py-1 rounded">
                        {log.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-dsi-selected font-bold">
                      {log.event_action}
                    </td>
                    <td className="py-3 px-4 opacity-80 truncate max-w-xl" title={JSON.stringify(log.details)}>
                      <div className="flex items-center gap-2">
                        <Terminal className="w-3 h-3 opacity-50 shrink-0" />
                        <span className="truncate">{JSON.stringify(log.details)}</span>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}