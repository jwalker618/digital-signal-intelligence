"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, AlertCircle, Clock, ShieldAlert, CheckCircle, XCircle, FileEdit } from "lucide-react";

export default function ReferralQueue() {
  const [referrals, setReferrals] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // State for the Slide-Out Drawer
  const [selectedReferral, setSelectedReferral] = useState<any | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [underwriterNotes, setUnderwriterNotes] = useState("");

  useEffect(() => {
    const fetchReferrals = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/referral-queue");
        if (res.ok) {
          const data = await res.json();
          setReferrals(data);
        }
      } catch (error) {
        console.error("Failed to fetch referrals", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchReferrals();
  }, []);

  const openReviewDrawer = (referral: any) => {
    setSelectedReferral(referral);
    setUnderwriterNotes(""); // Clear previous notes
    setIsDrawerOpen(true);
  };

  const handleAction = (action: 'Approve' | 'Decline' | 'Modify') => {
    // In a real app, this would send a POST request to update the database
    console.log(`Action: ${action} on Referral ${selectedReferral?.id} with notes: ${underwriterNotes}`);
    
    // Optimistically remove from queue and close drawer
    setReferrals(referrals.filter(r => r.id !== selectedReferral.id));
    setIsDrawerOpen(false);
  };

  if (isLoading) {
    return <div className="flex h-full min-h-[500px] items-center justify-center"><Loader2 className="animate-spin text-blue-500 w-10 h-10" /></div>;
  }

  return (
    <>
      {/* THE MAIN QUEUE TABLE */}
      <Card className="bg-slate-900 border-slate-800 text-white flex-grow flex flex-col h-full min-h-[600px]">
        <CardHeader className="border-b border-slate-800 pb-4">
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="text-yellow-500" /> 
              Action Required: Referral Queue
            </CardTitle>
            <Badge variant="outline" className="bg-slate-950 text-slate-300 border-slate-700">
              {referrals.length} Cases Pending
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="p-0 overflow-auto">
          {referrals.length === 0 ? (
            <div className="flex h-64 items-center justify-center text-slate-500">No pending referrals. Inbox zero!</div>
          ) : (
            <Table>
              <TableHeader className="bg-slate-950">
                <TableRow className="border-slate-800 hover:bg-slate-950">
                  <TableHead className="text-slate-400">Entity</TableHead>
                  <TableHead className="text-slate-400">Priority</TableHead>
                  <TableHead className="text-slate-400 w-1/3">AI Referral Reasons</TableHead>
                  <TableHead className="text-slate-400 text-right">Premium Impact</TableHead>
                  <TableHead className="text-slate-400 text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {referrals.map((ref) => {
                  const isHighPriority = ref.priority < 3;
                  const reasons = typeof ref.reasons === 'string' ? JSON.parse(ref.reasons) : ref.reasons;

                  return (
                    <TableRow key={ref.id} className="border-slate-800 hover:bg-slate-800/50">
                      <TableCell className="font-medium text-slate-200">
                        {ref.entity_name}
                        <div className="text-xs text-slate-500 uppercase mt-1">{ref.coverage} • Tier {ref.tier}</div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={isHighPriority ? 'text-red-400 border-red-400' : 'text-yellow-400 border-yellow-400'}>
                          {isHighPriority ? <AlertCircle className="w-3 h-3 mr-1" /> : <Clock className="w-3 h-3 mr-1" />}
                          P{ref.priority}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-slate-400">
                        <ul className="list-disc list-inside space-y-1">
                          {reasons?.slice(0, 2).map((r: string, i: number) => <li key={i} className="truncate">{r}</li>)}
                          {reasons?.length > 2 && <li className="text-slate-500 italic">+{reasons.length - 2} more flags</li>}
                        </ul>
                      </TableCell>
                      <TableCell className="text-right font-mono text-slate-300">
                        ${ref.premium?.toLocaleString() || 0}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button size="sm" onClick={() => openReviewDrawer(ref)} className="bg-blue-600 hover:bg-blue-700 text-white">Review Case</Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* THE SLIDE-OUT REVIEW DRAWER */}
      <Sheet open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
        <SheetContent className="bg-slate-950 border-l border-slate-800 text-slate-50 sm:max-w-xl overflow-y-auto">
          <SheetHeader className="mb-6 border-b border-slate-800 pb-4">
            <SheetTitle className="text-2xl font-bold text-white flex items-center justify-between">
              {selectedReferral?.entity_name}
              <Badge className="bg-yellow-500/20 text-yellow-500 border-yellow-500/50 uppercase">
                {selectedReferral?.decision}
              </Badge>
            </SheetTitle>
            <SheetDescription className="text-slate-400">
              {selectedReferral?.coverage?.toUpperCase()} • Recommended Tier: {selectedReferral?.tier} • Baseline Premium: <span className="text-green-400 font-mono">${selectedReferral?.premium?.toLocaleString()}</span>
            </SheetDescription>
          </SheetHeader>

          {/* Core Referral Reasons */}
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4" /> AI Referral Triggers
              </h3>
              <ul className="space-y-3">
                {(typeof selectedReferral?.reasons === 'string' ? JSON.parse(selectedReferral?.reasons) : selectedReferral?.reasons || []).map((reason: string, idx: number) => (
                  <li key={idx} className="bg-slate-900 p-3 rounded-md border border-slate-800 text-slate-300 text-sm leading-relaxed">
                    {reason}
                  </li>
                ))}
              </ul>
            </div>

            {/* Required Audit Input */}
            <div>
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <FileEdit className="w-4 h-4" /> Underwriter Rationale
              </h3>
              <Textarea 
                placeholder="Enter justification for overriding or declining this risk (Required for Audit Trail)..." 
                className="bg-slate-900 border-slate-800 text-slate-200 placeholder:text-slate-600 min-h-[120px]"
                value={underwriterNotes}
                onChange={(e) => setUnderwriterNotes(e.target.value)}
              />
            </div>
          </div>

          {/* Action Footer */}
          <SheetFooter className="mt-8 pt-4 border-t border-slate-800 flex-col sm:flex-row gap-3">
            <Button variant="outline" className="flex-1 bg-transparent border-red-900 text-red-400 hover:bg-red-950 hover:text-red-300" onClick={() => handleAction('Decline')} disabled={!underwriterNotes}>
              <XCircle className="w-4 h-4 mr-2" /> Decline Risk
            </Button>
            <Button variant="outline" className="flex-1 bg-transparent border-yellow-700 text-yellow-400 hover:bg-yellow-900 hover:text-yellow-300" onClick={() => handleAction('Modify')} disabled={!underwriterNotes}>
              <FileEdit className="w-4 h-4 mr-2" /> Modify Terms
            </Button>
            <Button className="flex-1 bg-green-600 hover:bg-green-700 text-white" onClick={() => handleAction('Approve')} disabled={!underwriterNotes}>
              <CheckCircle className="w-4 h-4 mr-2" /> Approve Override
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </>
  );
}