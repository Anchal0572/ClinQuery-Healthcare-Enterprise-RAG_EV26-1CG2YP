import React from 'react';
import { Stethoscope, HelpCircle, FileText, History, LayoutDashboard, UserCheck, LogOut, BarChart3 } from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  currentUser: User | null;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  currentUser,
  onLogout,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'ask', label: 'Ask ClinQuery', icon: HelpCircle },
    { id: 'documents', label: 'Documents & Ingestion', icon: FileText },
    { id: 'audit', label: 'Audit Log & History', icon: History },
    { id: 'evaluation', label: 'Evaluation & Benchmark', icon: BarChart3 },
  ];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div
            className="flex items-center space-x-3 cursor-pointer"
            onClick={() => onSelectTab('dashboard')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-sky-500/20">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-1.5">
                ClinQuery
                <span className="text-xs bg-sky-100 text-sky-800 font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider">
                  RAG
                </span>
              </span>
              <p className="text-[11px] text-slate-400 font-medium leading-none">
                Clinical Retrieval You Can Rely On
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-sky-50 text-sky-700 shadow-sm border border-sky-100'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-sky-600' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* User profile & session */}
          <div className="flex items-center space-x-3">
            {currentUser ? (
              <div className="flex items-center space-x-2 pl-3 border-l border-slate-200">
                <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-700 font-semibold text-xs">
                  {currentUser.name
                    .split(' ')
                    .map((n) => n[0])
                    .join('')
                    .slice(0, 2)}
                </div>
                <div className="text-left hidden sm:block">
                  <div className="text-xs font-semibold text-slate-800 leading-tight">
                    {currentUser.name}
                  </div>
                  <div className="text-[10px] text-slate-400 font-medium capitalize">
                    {currentUser.role}
                  </div>
                </div>
                <button
                  onClick={onLogout}
                  title="Switch Clinical User"
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md hover:bg-rose-50 transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => onSelectTab('login')}
                className="text-xs font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 px-3 py-1.5 rounded-lg border border-sky-200 transition"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
