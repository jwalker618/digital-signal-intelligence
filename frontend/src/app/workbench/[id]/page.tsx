// src/app/workbench/[id]/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, ShieldAlert, Activity, ChevronRight, Server, Loader2 } from 'lucide-react';
import { Submission } from '@/types/dsi';
import { SubmissionApi } from '@/lib/api';
import OverrideModal from '@/components/workbench/OverrideModal';

export default function UnderwriterWorkbench({ params }: { params: { id: string } }) {
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOverrideOpen, setIsOverrideOpen] = useState(false);
  const handleOverrideSuccess = () => {
    // Re-fetch the submission to show the updated, overriden state
    SubmissionApi.getById(params.id).then(setSubmission);
  };

  // FETCH LIVE DATA FROM FASTAPI
  useEffect(() => {
    const fetchSubmission = async () => {
      try {
        setIsLoading(true);
        const data = await SubmissionApi.getById(params.id);
        setSubmission(data);
      } catch (err) {
        setError("Failed to load submission data from the DSI Engine.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchSubmission();
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        <span className="ml-3 text-slate-600 font-medium">Running DSI 14-Step Workflow...</span>
      </div>
    );
  }

  if (error || !submission || !submission.latest_model_version) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <div className="text-red-500 flex items-center gap-2">
          <ShieldAlert className="w-6 h-6" />
          <span className="font-semibold">{error || "Model Version unavailable."}</span>
        </div>
      </div>
    );
  }

  const mv = submission.latest_model_version;

  return (
    <div className="flex h-screen bg-slate-50">
      
      {/* LEFT PANE: Decision & Overview */}
      <div className="w-1/3 bg-white border-r border-slate-200 p-6 flex flex-col shadow-sm z-10">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-800">{submission.entity_name}</h1>
          <a href={`https://${submission.discovered_domain}`} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-sm">
            {submission.discovered_domain}
          </a>
          <div className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
            Coverage: {submission.coverage.toUpperCase()}
          </div>
        </div>

        <div className="bg-slate-50 rounded-lg p-5 border border-slate-200 mb-6">
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Pricing Decision</h2>
          
          <div className="flex items-end gap-2 mb-2">
            <span className="text-4xl font-bold text-slate-900">${mv.final_premium.toLocaleString()}</span>
            <span className="text-sm text-slate-500 mb-1">/ year</span>
          </div>

          <div className="flex items-center gap-4 mt-6">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-semibold ${
              mv.decision === 'approve' ? 'bg-green-100 text-green-700' : 
              mv.decision === 'refer' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
            }`}>
              {mv.decision === 'approve' && <CheckCircle className="w-4 h-4" />}
              {mv.decision === 'refer' && <AlertCircle className="w-4 h-4" />}
              {mv.decision === 'decline' && <ShieldAlert className="w-4 h-4" />}
              {mv.decision.toUpperCase()}
            </div>
            <div className="text-sm font-medium text-slate-600">
              Tier {mv.final_tier} ({mv.tier_label})
            </div>
          </div>
        </div>

        {/* ... Rest of the Left Pane UI ... */}
        
        <button className="mt-auto w-full bg-blue-600 text-white font-semibold py-2.5 rounded-lg hover:bg-blue-700 transition-colors">
          Bind Quote
        </button>
        <button 
          onClick={() => setIsOverrideOpen(true)}
          className="mt-3 w-full bg-white text-slate-700 border border-slate-300 font-semibold py-2.5 rounded-lg hover:bg-slate-50 transition-colors"
        >
          Override & Capture Telemetry
        </button>
      </div>

      {/* RIGHT PANE: Signal Cascade & Assessment Layers */}
      <div className="w-2/3 p-8 overflow-y-auto">
        <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          Three-Layer Assessment
        </h2>

        {/* Dynamic rendering of Signal Conditions from the Backend */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-6">
          <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex justify-between items-center cursor-pointer">
            <div>
              <h3 className="font-semibold text-slate-800">Triggered Signal Conditions</h3>
              <p className="text-sm text-slate-500">Modifiers and Flags applied to this risk</p>
            </div>
          </div>
          
          <div className="p-0">
            {mv.signal_conditions.length === 0 ? (
               <div className="px-6 py-4 text-sm text-slate-500">No special conditions triggered.</div>
            ) : (
              mv.signal_conditions.map((sig, idx) => (
                <div key={idx} className="px-6 py-4 border-b border-slate-100 flex items-center justify-between hover:bg-slate-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <Server className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-700">{sig.note}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                        sig.action === 'modifier' ? 'bg-blue-100 text-blue-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {sig.action.toUpperCase()}
                    </span>
                    {sig.applied_modifier && (
                      <span className="text-sm font-medium text-slate-500 w-24 text-right">
                        {(sig.applied_modifier * 100).toFixed(0)}% Impact
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
      {/* Modals */}
      {submission && mv && (
        <OverrideModal 
          isOpen={isOverrideOpen}
          onClose={() => setIsOverrideOpen(false)}
          submissionId={submission.submission_id}
          currentPremium={mv.final_premium}
          currentTier={mv.final_tier}
          onSuccess={handleOverrideSuccess}
        />
      )}
    </div>
  );
}