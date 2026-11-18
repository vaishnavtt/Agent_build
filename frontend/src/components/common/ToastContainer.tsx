import React from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';

export const ToastContainer: React.FC = () => {
  const { toasts, dismissToast } = useWorkflow();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => {
        let icon = <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />;
        let borderClass = 'border-[#E6E5E2] bg-[#FFFFFF]';

        if (toast.type === 'success') {
          icon = <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />;
          borderClass = 'border-emerald-200 bg-[#FFFFFF]';
        } else if (toast.type === 'error') {
          icon = <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />;
          borderClass = 'border-rose-200 bg-[#FFFFFF]';
        } else if (toast.type === 'warning') {
          icon = <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />;
          borderClass = 'border-amber-200 bg-[#FFFFFF]';
        }

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto p-3.5 rounded-2xl shadow-elevated border ${borderClass} flex items-start justify-between gap-3 animate-in slide-in-from-bottom-2 duration-200`}
          >
            <div className="flex items-start gap-2.5">
              <div className="pt-0.5">{icon}</div>
              <div>
                <p className="text-xs font-semibold text-[#111111]">{toast.title}</p>
                <p className="text-[11px] text-[#8D8D8D] mt-0.5 leading-relaxed">{toast.description}</p>
              </div>
            </div>
            <button
              onClick={() => dismissToast(toast.id)}
              className="text-[#8D8D8D] hover:text-[#111111] p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
};

