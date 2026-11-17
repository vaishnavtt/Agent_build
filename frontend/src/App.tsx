import { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './components/Dashboard';

export function App() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [checkingHealth, setCheckingHealth] = useState<boolean>(false);

  const checkBackendHealth = useCallback(async () => {
    setCheckingHealth(true);
    try {
      // Primary check via Vite dev proxy (/api/v1/health) or fallback to direct port 8000
      let response: Response;
      try {
        response = await fetch('/api/v1/health', { method: 'GET' });
      } catch {
        response = await fetch('http://localhost:8000/api/v1/health', { method: 'GET' });
      }

      if (response.ok) {
        const data = await response.json();
        setBackendOnline(data.status === 'ok');
      } else {
        setBackendOnline(false);
      }
    } catch {
      setBackendOnline(false);
    } finally {
      setCheckingHealth(false);
    }
  }, []);

  useEffect(() => {
    checkBackendHealth();
  }, [checkBackendHealth]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      <Navbar
        backendOnline={backendOnline}
        onRefreshHealth={checkBackendHealth}
        checkingHealth={checkingHealth}
      />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Dashboard />
      </main>
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-600">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 AgentForge AI Team. All rights reserved.</p>
          <p className="font-mono text-slate-500">React • Vite • TypeScript • Tailwind CSS • React Flow • FastAPI</p>
        </div>
      </footer>
    </div>
  );
}

export default App;

