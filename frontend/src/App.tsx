import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { AskPage } from './pages/AskPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { AuditPage } from './pages/AuditPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { User } from './types';
import { Shield, HeartPulse } from 'lucide-react';

export function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem('clinquery_user');
      return saved ? JSON.parse(saved) : {
        id: 1,
        name: 'Dr. Sarah Smith, MD',
        email: 's.smith.cardio@hospital.internal',
        role: 'Cardiologist',
      };
    } catch {
      return null;
    }
  });

  const [currentTab, setCurrentTab] = useState<string>('ask');
  const [activeQuestion, setActiveQuestion] = useState<string>('');

  const handleLogin = (user: User) => {
    setCurrentUser(user);
    try {
      localStorage.setItem('clinquery_user', JSON.stringify(user));
    } catch (e) {
      console.error(e);
    }
    setCurrentTab('ask');
  };

  const handleLogout = () => {
    setCurrentUser(null);
    try {
      localStorage.removeItem('clinquery_user');
    } catch (e) {
      console.error(e);
    }
    setCurrentTab('login');
  };

  const handleRerun = (query: string) => {
    setActiveQuestion(query);
    setCurrentTab('ask');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800 selection:bg-sky-100 selection:text-sky-900">
      {/* Top Navigation */}
      <Navbar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          if (tab === 'login') {
            setCurrentTab('login');
          } else {
            setCurrentTab(tab);
          }
        }}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <main className="flex-1 pb-16">
        {currentTab === 'login' && <LoginPage onLogin={handleLogin} />}

        {currentTab === 'dashboard' && (
          <DashboardPage
            onNavigate={(tab) => {
              setCurrentTab(tab);
            }}
          />
        )}

        {currentTab === 'ask' && (
          <AskPage currentUser={currentUser} initialQuestion={activeQuestion} />
        )}

        {currentTab === 'documents' && <DocumentsPage currentUser={currentUser} />}

        {currentTab === 'audit' && <AuditPage onRerunQuery={handleRerun} />}

        {currentTab === 'evaluation' && <EvaluationPage />}
      </main>

      {/* Clinical Enterprise Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <HeartPulse className="w-4 h-4 text-sky-600" />
            <span className="font-semibold text-slate-700">ClinQuery RAG v1.0</span>
            <span>—</span>
            <span>Evidence-Grounded Clinical Retrieval System</span>
          </div>

          <div className="flex items-center space-x-4 text-[11px] text-slate-400">
            <span className="flex items-center gap-1">
              <Shield className="w-3.5 h-3.5 text-emerald-500" />
              HIPAA & Medical Grounding Guardrails Active
            </span>
            <span>•</span>
            <span>Local FastEmbed + Qdrant Vector Search</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
