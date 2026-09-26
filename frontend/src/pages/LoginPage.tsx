import React, { useState } from 'react';
import { Stethoscope, UserCheck, Shield, Award, ArrowRight } from 'lucide-react';
import { User } from '../types';

interface LoginPageProps {
  onLogin: (user: User) => void;
}

const PRESET_CLINICIANS: User[] = [
  { id: 1, name: 'Dr. Sarah Smith, MD', email: 's.smith.cardio@hospital.internal', role: 'CLINICAL' },
  { id: 2, name: 'Alex Rivera (Facilities Lead)', email: 'a.rivera.ops@hospital.internal', role: 'OPERATIONS' },
  { id: 3, name: 'Chief Elena Vance, MD', email: 'e.vance.cmo@hospital.internal', role: 'ADMIN' },
  { id: 4, name: 'Dr. David Chen, PharmD', email: 'd.chen.pharmacy@hospital.internal', role: 'CLINICAL' },
];

export const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const [customName, setCustomName] = useState('');
  const [customEmail, setCustomEmail] = useState('');
  const [customRole, setCustomRole] = useState<'CLINICAL' | 'OPERATIONS' | 'ADMIN'>('CLINICAL');

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customName.trim()) return;
    const user: User = {
      id: Math.floor(Math.random() * 9000) + 1000,
      name: customName.trim(),
      email: customEmail.trim() || `${customName.toLowerCase().replace(/\s+/g, '.') }@hospital.internal`,
      role: customRole,
    };
    onLogin(user);
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-xl border border-slate-200">
        <div className="text-center">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center text-white shadow-lg shadow-sky-500/30">
            <Stethoscope className="w-8 h-8" />
          </div>
          <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">
            ClinQuery Decision Support
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Select a verified clinical staff profile or enter credentials to start.
          </p>
        </div>

        {/* Preset Clinicians */}
        <div className="space-y-2.5">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">
            Quick Clinical Profiles (Demo)
          </span>
          {PRESET_CLINICIANS.map((clinician) => (
            <button
              key={clinician.id}
              onClick={() => onLogin(clinician)}
              className="w-full text-left p-3.5 rounded-xl border border-slate-200 hover:border-sky-400 hover:bg-sky-50/50 transition-all flex items-center justify-between group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-full bg-slate-100 group-hover:bg-white text-slate-700 font-semibold text-xs flex items-center justify-center border border-slate-200">
                  {clinician.name
                    .split(' ')
                    .map((n) => n[0])
                    .join('')
                    .slice(0, 2)}
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-900 group-hover:text-sky-900">
                    {clinician.name}
                  </div>
                  <div className="text-xs text-slate-500 font-medium">
                    {clinician.role}
                  </div>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-sky-600 group-hover:translate-x-0.5 transition-all" />
            </button>
          ))}
        </div>

        {/* Divider */}
        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-3 text-slate-400 font-semibold">Or enter custom</span>
          </div>
        </div>

        {/* Custom Login Form */}
        <form onSubmit={handleCustomSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name & Title</label>
            <input
              type="text"
              required
              placeholder="e.g. Dr. Jennifer Taylor, MD"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Access Role & Permission</label>
            <select
              value={customRole}
              onChange={(e) => setCustomRole(e.target.value as any)}
              className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:outline-none bg-white font-medium"
            >
              <option value="CLINICAL">CLINICAL — Access to guidelines, protocols, SOPs</option>
              <option value="OPERATIONS">OPERATIONS — Facilities & non-clinical ops</option>
              <option value="ADMIN">ADMIN — Full system access & governance</option>
            </select>
          </div>
          <button
            type="submit"
            className="w-full mt-2 py-2.5 px-4 bg-sky-600 hover:bg-sky-700 text-white font-semibold text-sm rounded-lg shadow-md transition"
          >
            Enter ClinQuery System
          </button>
        </form>

        <div className="text-center text-[11px] text-slate-400 flex items-center justify-center space-x-1">
          <Shield className="w-3.5 h-3.5 text-emerald-600" />
          <span>HIPAA & Audit-compliant Clinical Trial / Hackathon Sandbox</span>
        </div>
      </div>
    </div>
  );
};
