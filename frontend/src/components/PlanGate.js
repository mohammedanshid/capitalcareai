import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { hasAccess, requiredPlanFor } from '../utils/plan';
import { UpgradeModal } from './UpgradeModal';
import { Lock } from '@phosphor-icons/react';

// Page-level guard: wraps a route and shows upgrade modal if user lacks access.
export const PlanGate = ({ feature, children }) => {
  const { user } = useAuth();
  const nav = useNavigate();
  const [open, setOpen] = React.useState(true);
  const plan = user?.plan || 'free';
  if (hasAccess(plan, feature)) return children;
  const required = requiredPlanFor(feature);
  const close = () => { setOpen(false); nav('/dashboard'); };
  return (
    <div className="min-h-screen bg-[var(--cream-light)] flex items-center justify-center px-4" data-testid="plan-gate-screen">
      <div className="max-w-md w-full text-center">
        <div className="w-20 h-20 rounded-3xl mx-auto flex items-center justify-center mb-5" style={{ background: required === 'elite' ? 'linear-gradient(135deg, #FFD700, #FFA500)' : 'linear-gradient(135deg, #F4845F, #e06b47)' }}>
          <Lock size={40} weight="fill" className="text-white" />
        </div>
        <h1 className="text-2xl font-bold text-[var(--dark)]">Locked Feature</h1>
        <p className="text-sm text-[var(--muted)] mt-2">Upgrade to unlock this feature. Click below to continue.</p>
        <button onClick={() => setOpen(true)} className="mt-5 btn-coral px-6 py-3" data-testid="plan-gate-open">See upgrade options</button>
      </div>
      <UpgradeModal open={open} onClose={close} feature={feature} requiredPlan={required} />
    </div>
  );
};
