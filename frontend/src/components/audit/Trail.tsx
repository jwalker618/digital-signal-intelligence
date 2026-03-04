"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2, History, ShieldAlert, Cpu } from "lucide-react";

export default function AuditTrail() {
  const [logs, setLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/audit-trail");
        if (res.ok) {
          const data = await res.json();
          setLogs(data);
        }
      } catch (error) {
        console.error("Failed to fetch audit logs", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchLogs();
  }, []);

  if (isLoading) {
    return <div className="flex h-full min-h-[500px] items-center justify-center"><Loader2 className="animate-spin text-blue-500 w-10 h-10" /></div>;
  }

  return (
    <Card className="bg-slate-900 border-slate-800 text-white flex-grow flex flex-col h-full min-h-[600px]">
      <CardHeader className="border-b border-slate-800 pb-4">
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center gap-2">
            <History className="text-blue-500" /> 
            Immutable Audit Ledger
          </CardTitle>
          <Badge variant="outline" className="bg-slate-950 text-slate-300 border-slate-700">
            {logs.length} Recorded Events
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0 overflow-auto">
        <Table>
          <TableHeader className="bg-slate-950">
            <TableRow className="border-slate-800 hover:bg-slate-950">
              <TableHead className="text-slate-400 w-48">Timestamp (UTC)</TableHead>
              <TableHead className="text-slate-400">Actor / Source</TableHead>
              <TableHead className="text-slate-400">Event Type</TableHead>
              <TableHead className="text-slate-400">Target Entity</TableHead>
              <TableHead className="text-slate-400 w-1/3">Compliance Details</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => {
              const isManual = log.type === "Manual Override";
              const date = new Date(log.timestamp);
              
              return (
                <TableRow key={log.id} className="border-slate-800 hover:bg-slate-800/50">
                  <TableCell className="font-mono text-xs text-slate-400 whitespace-nowrap">
                    {date.toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2 text-sm text-slate-200">
                      {isManual ? <ShieldAlert className="w-3 h-3 text-yellow-500" /> : <Cpu className="w-3 h-3 text-blue-500" />}
                      {log.actor}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={isManual ? 'text-yellow-400 border-yellow-400/50 bg-yellow-400/10' : 'text-blue-400 border-blue-400/50 bg-blue-400/10'}>
                      {log.action}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-medium text-slate-300 truncate max-w-[150px]">
                    {log.entity}
                  </TableCell>
                  <TableCell className="text-sm text-slate-400 italic truncate max-w-[300px]" title={log.details}>
                    {log.details}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}