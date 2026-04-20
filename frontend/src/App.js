import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LandingPage } from './pages/LandingPage';
import { AuthPage } from './pages/AuthPage';
import { Dashboard } from './pages/Dashboard';
import { TransactionsPage } from './pages/TransactionsPage';
import { GoalsPage } from './pages/GoalsPage';
import { BudgetsPage } from './pages/BudgetsPage';
import { LoansPage } from './pages/LoansPage';
import { CreditCardsPage } from './pages/CreditCardsPage';
import { InvestmentsPage } from './pages/InvestmentsPage';
import { RealEstatePage } from './pages/RealEstatePage';
import { NetWorthPage } from './pages/NetWorthPage';
import { ZeroBudgetPage } from './pages/ZeroBudgetPage';
import { LendBorrowPage } from './pages/LendBorrowPage';
import { DebtPayoffPage } from './pages/DebtPayoffPage';
import { JarsPage } from './pages/JarsPage';
import { SipRdPage } from './pages/SipRdPage';
import { TaxPage } from './pages/TaxPage';
import { PricingPage } from './pages/PricingPage';
import { PaymentSuccessPage } from './pages/PaymentSuccessPage';
import { PlanGate } from './components/PlanGate';
import { Toaster } from 'sonner';
import './App.css';

const Protected = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-[var(--cream-light)]"><div className="h-10 w-10 animate-spin rounded-full border-[3px] border-[var(--coral)] border-r-transparent"/></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<AuthPage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/payment-success" element={<Protected><PaymentSuccessPage /></Protected>} />
          <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
          <Route path="/transactions" element={<Protected><TransactionsPage /></Protected>} />
          <Route path="/goals" element={<Protected><GoalsPage /></Protected>} />
          <Route path="/budgets" element={<Protected><PlanGate feature="budgets"><BudgetsPage /></PlanGate></Protected>} />
          <Route path="/loans" element={<Protected><PlanGate feature="loans"><LoansPage /></PlanGate></Protected>} />
          <Route path="/credit-cards" element={<Protected><PlanGate feature="credit_cards"><CreditCardsPage /></PlanGate></Protected>} />
          <Route path="/investments" element={<Protected><PlanGate feature="investments"><InvestmentsPage /></PlanGate></Protected>} />
          <Route path="/real-estate" element={<Protected><PlanGate feature="real_estate"><RealEstatePage /></PlanGate></Protected>} />
          <Route path="/net-worth" element={<Protected><PlanGate feature="net_worth"><NetWorthPage /></PlanGate></Protected>} />
          <Route path="/zero-budget" element={<Protected><PlanGate feature="zero_budget"><ZeroBudgetPage /></PlanGate></Protected>} />
          <Route path="/lend-borrow" element={<Protected><PlanGate feature="lend_borrow"><LendBorrowPage /></PlanGate></Protected>} />
          <Route path="/debt-payoff" element={<Protected><PlanGate feature="debt_payoff"><DebtPayoffPage /></PlanGate></Protected>} />
          <Route path="/jars" element={<Protected><JarsPage /></Protected>} />
          <Route path="/sip-rd" element={<Protected><PlanGate feature="sip_rd"><SipRdPage /></PlanGate></Protected>} />
          <Route path="/tax" element={<Protected><PlanGate feature="tax_basic"><TaxPage /></PlanGate></Protected>} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}
export default App;
