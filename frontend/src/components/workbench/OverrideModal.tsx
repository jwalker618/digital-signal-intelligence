// src/components/workbench/OverrideModal.tsx
'use client';

import React, { useState } from 'react';
import { X, AlertTriangle, Loader2, Save } from 'lucide-react';
import { WorkflowApi, TelemetryPayload } from '@/lib/api';
import { DecisionType } from '@/types/dsi';

interface OverrideModalProps {
  isOpen: boolean;
  onClose: () => void;
  submissionId: string;
  currentPremium: number;
  currentTier: number;
  onSuccess: () => void;
}

const REASON_CODES = [
  { value: 'UNOBSERVED_RISK', label: 'Unobserved Risk / Missing Signal' },
  { value: 'COMMERCIAL_RELATIONSHIP', label: 'Commercial Relationship / Accommodation' },
  { value: 'COMPETITIVE_PRESSURE', label: 'Competitive Pricing Pressure' },
  { value: 'DATA_ERROR', label: 'Underlying Data Error / False Positive' },
  { value: 'BROKER_NEGOTIATION', label: 'Broker Negotiation' }
];

export default function OverrideModal({ 
  isOpen, 
  onClose, 
  submissionId, 
  currentPremium, 
  currentTier,
  onSuccess 
}: OverrideModalProps) {
  const [decision, setDecision] = useState<DecisionType>('approve');
  const [tier, setTier] = useState<number>(currentTier);
  const [premium, setPremium] = useState<number>(currentPremium);
  const [reasonCode, setReasonCode] = useState<string>('UNOBSERVED_RISK');
  const [notes, setNotes] = useState<string>('');
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) {
      setError("Notes are required for an override.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      const payload: TelemetryPayload = {
        decision,
        override_tier: tier !== currentTier ? tier : undefined,
        override_premium: premium !== currentPremium ? premium : undefined,
        reason_code: reasonCode,
        notes: notes
      };

      // Submit the telemetry to the DSI backend
      await WorkflowApi.submitOverride(submissionId, payload);
      
      onSuccess();
      onClose();
    } catch (err) {
      setError("Failed to submit override. Please check the connection.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden border border-slate-200">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            Override Model Recommendation
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-md border border-red-200">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 mb-5">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">New Decision</label>
              <select 
                value={decision} 
                onChange={(e) => setDecision(e.target.value as DecisionType)}
                className="w-full border border-slate-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="approve">Approve</option>
                <option value="refer">Refer</option>
                <option value="decline">Decline</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Override Tier</label>
              <input 
                type="number" 
                min="1" max="5" 
                value={tier} 
                onChange={(e) => setTier(Number(e.target.value))}
                className="w-full border border-slate-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="mb-5">
            <label className="block text-sm font-semibold text-slate-700 mb-1">Override Premium ($)</label>
            <input 
              type="number" 
              value={premium} 
              onChange={(e) => setPremium(Number(e.target.value))}
              className="w-full border border-slate-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="mb-5">
            <label className="block text-sm font-semibold text-slate-700 mb-1">Reason Code (Telemetry)</label>
            <select 
              value={reasonCode} 
              onChange={(e) => setReasonCode(e.target.value)}
              className="w-full border border-slate-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-slate-50"
            >
              {REASON_CODES.map(code => (
                <option key={code.value} value={code.value}>{code.label}</option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-700 mb-1">Justification / Notes</label>
            <textarea 
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g., Client uses a legacy mainframe not exposed to public internet. Not picked up by current signal extractors."
              className="w-full border border-slate-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            />
          </div>

          {/* Footer Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
            <button 
              type="button" 
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-300 rounded-md hover:bg-slate-50"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 flex items-center gap-2 disabled:opacity-70"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Capture & Override
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}