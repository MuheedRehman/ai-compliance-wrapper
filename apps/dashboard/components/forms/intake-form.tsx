'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import Card from '@/components/card';
import { 
  ShieldCheck, 
  ArrowRight, 
  ArrowLeft, 
  Info,
  CheckCircle2
} from 'lucide-react';

const steps = [
  { id: 'identity', title: 'System Identity' },
  { id: 'actor',   title: 'Actor Role' },
  { id: 'risk',    title: 'Risk Factors' },
  { id: 'review',  title: 'Review & Submit' }
];

export default function IntakeForm() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    title: '',
    is_developer: false,
    is_deployer: false,
    is_prohibited_use: false,
    is_high_risk_annex_iii: false,
    is_safety_component: false,
    has_transparency_obligation: false,
    is_gpai: false
  });

  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, steps.length - 1));
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0));

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.createIntake({
        title: formData.title || 'Untitled Assessment',
        answers: {
          is_developer: formData.is_developer,
          is_deployer: formData.is_deployer,
          is_prohibited_use: formData.is_prohibited_use,
          is_high_risk_annex_iii: formData.is_high_risk_annex_iii,
          is_safety_component: formData.is_safety_component,
          has_transparency_obligation: formData.has_transparency_obligation,
          is_gpai: formData.is_gpai
        }
      });
      router.push(`/intake/${res.id}`);
    } catch (err: any) {
      setError(err.body?.detail || 'Failed to submit assessment');
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch(currentStep) {
      case 0:
        return (
          <div className="space-y-6 animate-fade-in">
            <div className="space-y-4">
              <label className="block text-sm font-semibold text-zinc-300">Assessment Title</label>
              <input 
                type="text" 
                placeholder="e.g. Hiring Tool v2 Assessment"
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all outline-none"
                value={formData.title}
                onChange={e => setFormData({...formData, title: e.target.value})}
              />
              <p className="text-xs text-zinc-500 italic">This name will help you identify the classification result in the registry.</p>
            </div>
          </div>
        );
      case 1:
        return (
          <div className="space-y-6 animate-fade-in">
            <p className="text-sm text-zinc-400">Determine your legal status under the AI Act.</p>
            <div className="grid grid-cols-1 gap-4">
              <button 
                onClick={() => setFormData({...formData, is_developer: !formData.is_developer, is_deployer: false})}
                className={`p-4 rounded-xl border text-left transition-all ${formData.is_developer ? 'bg-indigo-500/10 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.1)]' : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'}`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-2 rounded-lg ${formData.is_developer ? 'bg-indigo-500 text-white' : 'bg-zinc-800 text-zinc-500'}`}>
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                  <span className="font-bold text-sm">Provider (Developer)</span>
                </div>
                <p className="text-xs text-zinc-500 leading-relaxed">You develop an AI system or a general-purpose AI model and place it on the market or put it into service under your own name or trademark.</p>
              </button>

              <button 
                onClick={() => setFormData({...formData, is_deployer: !formData.is_deployer, is_developer: false})}
                className={`p-4 rounded-xl border text-left transition-all ${formData.is_deployer ? 'bg-indigo-500/10 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.1)]' : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'}`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-2 rounded-lg ${formData.is_deployer ? 'bg-indigo-500 text-white' : 'bg-zinc-800 text-zinc-500'}`}>
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                  <span className="font-bold text-sm">Deployer (User)</span>
                </div>
                <p className="text-xs text-zinc-500 leading-relaxed">You use an AI system under your authority in the course of a professional activity (except for personal non-professional use).</p>
              </button>

              <button 
                onClick={() => setFormData({...formData, is_developer: false, is_deployer: false})}
                className={`p-4 rounded-xl border text-left transition-all ${!formData.is_developer && !formData.is_deployer ? 'bg-indigo-500/10 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.1)]' : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'}`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-2 rounded-lg ${!formData.is_developer && !formData.is_deployer ? 'bg-indigo-500 text-white' : 'bg-zinc-800 text-zinc-500'}`}>
                    <ShieldCheck className="h-4 w-4" />
                  </div>
                  <span className="font-bold text-sm">Importer / Distributor</span>
                </div>
                <p className="text-xs text-zinc-500 leading-relaxed">You are an importer or distributor of AI systems in the Union market (as defined in Art 26, 27).</p>
              </button>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-6 animate-fade-in">
            <p className="text-sm text-zinc-400">Select all that apply to your system.</p>
            <div className="space-y-3">
              {[
                { id: 'is_prohibited_use', label: 'Prohibited Use', desc: 'System uses social scoring, biometrics in public spaces for law enforcement, or cognitive behavioral manipulation.' },
                { id: 'is_high_risk_annex_iii', label: 'High-Risk (Annex III)', desc: 'System is used in critical infrastructure, education, employment, or law enforcement (as listed in Annex III).' },
                { id: 'is_safety_component', label: 'Safety Component', desc: 'System is a safety component of a product covered by EU harmonization legislation (e.g. toys, elevators).' },
                { id: 'has_transparency_obligation', label: 'Transparency Risk', desc: 'System interacts with humans (chatbots), generates deepfakes, or generates text (GPAI).' },
                { id: 'is_gpai', label: 'General Purpose AI (GPAI)', desc: 'System is a model that is capable of performing a wide range of distinct tasks.' },
              ].map(q => (
                <button 
                  key={q.id}
                  onClick={() => setFormData({...formData, [q.id]: !formData[q.id as keyof typeof formData]})}
                  className={`w-full p-4 rounded-xl border text-left transition-all flex items-start gap-4 ${formData[q.id as keyof typeof formData] ? 'bg-indigo-500/10 border-indigo-500' : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'}`}
                >
                  <div className={`shrink-0 mt-1 h-5 w-5 rounded border flex items-center justify-center transition-colors ${formData[q.id as keyof typeof formData] ? 'bg-indigo-500 border-indigo-500' : 'bg-zinc-800 border-zinc-700'}`}>
                    {formData[q.id as keyof typeof formData] && <CheckCircle2 className="h-3.5 w-3.5 text-white" />}
                  </div>
                  <div>
                    <span className="font-bold text-sm block mb-1">{q.label}</span>
                    <p className="text-xs text-zinc-500 leading-relaxed">{q.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-6 animate-fade-in">
            <div className="p-4 rounded-xl bg-zinc-900/80 border border-zinc-800">
              <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-4">Summary of Inputs</h4>
              <div className="grid grid-cols-2 gap-y-4 gap-x-8">
                <div>
                  <span className="text-[10px] text-zinc-600 block uppercase font-bold">System Name</span>
                  <span className="text-sm font-medium text-zinc-300">{formData.title || 'Untitled'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-600 block uppercase font-bold">Actor Type</span>
                  <span className="text-sm font-medium text-zinc-300">
                    {formData.is_developer ? 'Provider' : ''} 
                    {formData.is_developer && formData.is_deployer ? ' & ' : ''}
                    {formData.is_deployer ? 'Deployer' : ''}
                    {!formData.is_developer && !formData.is_deployer ? 'Distributor' : ''}
                  </span>
                </div>
              </div>
              <div className="mt-6 pt-6 border-t border-zinc-800/60">
                <span className="text-[10px] text-zinc-600 block uppercase font-bold mb-2">Selected Flags</span>
                <div className="flex flex-wrap gap-2">
                  {formData.is_prohibited_use && <span className="px-2.5 py-1 rounded-md bg-red-500/10 text-red-400 text-[10px] font-bold border border-red-500/20 uppercase tracking-tight">Prohibited</span>}
                  {formData.is_high_risk_annex_iii && <span className="px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 text-[10px] font-bold border border-amber-500/20 uppercase tracking-tight">High Risk</span>}
                  {formData.is_safety_component && <span className="px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 text-[10px] font-bold border border-amber-500/20 uppercase tracking-tight">Safety Comp</span>}
                  {formData.has_transparency_obligation && <span className="px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-400 text-[10px] font-bold border border-blue-500/20 uppercase tracking-tight">Transparency</span>}
                  {formData.is_gpai && <span className="px-2.5 py-1 rounded-md bg-purple-500/10 text-purple-400 text-[10px] font-bold border border-purple-500/20 uppercase tracking-tight">GPAI</span>}
                  {!formData.is_prohibited_use && !formData.is_high_risk_annex_iii && !formData.is_safety_component && !formData.has_transparency_obligation && !formData.is_gpai && (
                    <span className="text-xs text-zinc-600">No specific risk flags selected.</span>
                  )}
                </div>
              </div>
            </div>
            <div className="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 flex gap-3">
              <Info className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
              <p className="text-xs text-zinc-400 leading-relaxed">Submitting this assessment will generate a deterministic classification and obligation path based on current EU AI Act rules (Phase 3D Engine).</p>
            </div>
          </div>
        );
    }
  };

  return (
    <Card className="max-w-2xl mx-auto shadow-2xl">
      {/* Stepper Header */}
      <div className="mb-10">
        <div className="flex items-center justify-between px-4 sm:px-0">
          {steps.map((s, idx) => (
            <div key={s.id} className="flex items-center group">
              <div className="flex flex-col items-center">
                <div className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${idx <= currentStep ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'bg-zinc-800 text-zinc-500'}`}>
                  {idx < currentStep ? <CheckCircle2 className="h-4 w-4" /> : idx + 1}
                </div>
                <span className={`hidden sm:block mt-2 text-[10px] font-bold uppercase tracking-wider ${idx <= currentStep ? 'text-zinc-300' : 'text-zinc-600'}`}>{s.title}</span>
              </div>
              {idx < steps.length - 1 && (
                <div className={`w-12 h-px mx-2 mb-4 ${idx < currentStep ? 'bg-indigo-500' : 'bg-zinc-800'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Body */}
      <div className="min-h-[300px]">
        <h2 className="text-lg font-bold text-white mb-2">{steps[currentStep].title}</h2>
        {renderStep()}
      </div>

      {error && (
        <div className="mt-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">
          {error}
        </div>
      )}

      {/* Footer Actions */}
      <div className="mt-10 flex items-center justify-between border-t border-zinc-800/60 pt-6">
        <button 
          onClick={prevStep}
          disabled={currentStep === 0 || loading}
          className={`flex items-center gap-2 text-xs font-bold uppercase tracking-widest px-4 py-2 rounded-lg transition-colors ${currentStep === 0 ? 'text-zinc-700 cursor-not-allowed' : 'text-zinc-400 hover:text-white'}`}
        >
          <ArrowLeft className="h-3 w-3" /> Back
        </button>
        
        {currentStep === steps.length - 1 ? (
          <button 
            onClick={handleSubmit}
            disabled={loading}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold uppercase tracking-widest px-6 py-2.5 rounded-lg transition-all shadow-lg shadow-indigo-600/20 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : 'Generate Classification'} <ShieldCheck className="h-3.5 w-3.5" />
          </button>
        ) : (
          <button 
            onClick={nextStep}
            className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-bold uppercase tracking-widest px-6 py-2.5 rounded-lg transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            Next <ArrowRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </Card>
  );
}
