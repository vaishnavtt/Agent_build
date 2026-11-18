import React from 'react';
import { WorkflowProvider, useWorkflow } from './context/WorkflowContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { HelpModal } from './components/layout/HelpModal';
import { ToastContainer } from './components/common/ToastContainer';
import { DashboardPage } from './components/dashboard/DashboardPage';
import { CreateAgentPage } from './components/create/CreateAgentPage';
import { WorkflowEditorPage } from './components/editor/WorkflowEditorPage';
import { WorkflowValidationPage } from './components/validation/WorkflowValidationPage';
import { ExecutionMonitorPage } from './components/activity/ExecutionMonitorPage';
import { ExecutionHistoryPage } from './components/history/ExecutionHistoryPage';
import { MyAgentsPage } from './components/agents/MyAgentsPage';
import { TemplatesPage } from './components/templates/TemplatesPage';
import { SettingsPage } from './components/settings/SettingsPage';

const AppContent: React.FC = () => {
  const { currentPage } = useWorkflow();

  const renderActiveView = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage />;
      case 'create-agent':
        return <CreateAgentPage />;
      case 'editor':
        return <WorkflowEditorPage />;
      case 'validation':
        return <WorkflowValidationPage />;
      case 'activity':
        return <ExecutionMonitorPage />;
      case 'history':
        return <ExecutionHistoryPage />;
      case 'my-agents':
        return <MyAgentsPage />;
      case 'templates':
        return <TemplatesPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DashboardPage />;
    }
  };

  const isEditor = currentPage === 'editor';

  return (
    <div className="min-h-screen bg-[#FFFFFF] text-[#111111] font-sans antialiased flex flex-col">
      {/* Persistent Left Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="lg:pl-64 flex flex-col flex-1 min-h-screen">
        {/* Main Header */}
        <Header />

        {/* Dynamic Page Views */}
        <main className={`flex-1 ${isEditor ? 'overflow-hidden' : 'p-4 sm:p-6 lg:p-8'}`}>
          {renderActiveView()}
        </main>
      </div>

      {/* Global Modals & Notifications */}
      <HelpModal />
      <ToastContainer />
    </div>
  );
};

export function App() {
  return (
    <WorkflowProvider>
      <AppContent />
    </WorkflowProvider>
  );
}

export default App;
