import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { KPICards } from '../components/KPICards';
import { PrimaryLineChart } from '../components/PrimaryLineChart';
import { QuickInsightsPanel } from '../components/QuickInsightsPanel';
import { TransactionForm } from '../components/TransactionForm';
import { TransactionList } from '../components/TransactionList';
import { ChartsSection } from '../components/ChartsSection';
import { AIInsightsModal } from '../components/AIInsightsModal';
import { BottomNav } from '../components/BottomNav';
import { SignOut, Sparkle, Moon, Sun, DownloadSimple, Target } from '@phosphor-icons/react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [summary, setSummary] = useState({
    total_income: 0, total_expenses: 0, balance: 0, cash_flow: 0, transaction_count: 0,
    sparkline_income: [], sparkline_expenses: [], sparkline_profit: [], sparkline_cashflow: [],
    trend_income: 0, trend_expenses: 0, trend_profit: 0, trend_cashflow: 0,
    monthly_series: [],
  });
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [aiInsights, setAiInsights] = useState(null);
  const [budgetAlerts, setBudgetAlerts] = useState([]);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [summaryRes, transactionsRes, budgetsRes] = await Promise.all([
        axios.get(`${API_URL}/api/dashboard/summary`, { withCredentials: true }),
        axios.get(`${API_URL}/api/transactions`, { withCredentials: true }),
        axios.get(`${API_URL}/api/budgets`, { withCredentials: true }),
      ]);
      setSummary(summaryRes.data);
      setTransactions(transactionsRes.data);
      setBudgetAlerts(budgetsRes.data.filter(b => b.status === 'warning' || b.status === 'exceeded'));
    } catch (error) { console.error('Failed to fetch:', error); }
    finally { setLoading(false); }
  };

  const handleAnalyze = async () => {
    if (transactions.length === 0) { alert('Add some transactions first!'); return; }
    setAiAnalyzing(true); setShowAIModal(true);
    try {
      const { data } = await axios.post(`${API_URL}/api/analyze`, {}, { withCredentials: true });
      setAiInsights(data);
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to analyze');
      setShowAIModal(false);
    } finally { setAiAnalyzing(false); }
  };

  const handleExport = async (format) => {
    try {
      const response = await axios.get(`${API_URL}/api/export/${format}`, { withCredentials: true, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a'); link.href = url;
      link.setAttribute('download', `financial_report.${format}`);
      document.body.appendChild(link); link.click(); link.remove();
    } catch { alert('Export failed'); }
  };

  return (
    <div className="min-h-screen bg-[var(--surface-1)] pb-20 md:pb-0" data-testid="dashboard-page">
      {/* ── Top Bar ── */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[var(--nav-bg)] border-b border-[var(--border-default)]">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <h1 className="text-lg font-bold tracking-tight text-[var(--text-primary)]">
            Finance<span className="text-[var(--accent-blue)]">.</span>
          </h1>
          <div className="flex items-center gap-1.5 sm:gap-2">
            <nav className="hidden md:flex items-center gap-0.5 mr-2">
              {[{ label: 'Categories', path: '/categories' }, { label: 'Budgets', path: '/budgets' }, { label: 'Recurring', path: '/recurring' }].map(item => (
                <button key={item.path} onClick={() => navigate(item.path)}
                  className="px-3 py-1.5 rounded-md text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)] transition-all"
                  data-testid={`nav-${item.label.toLowerCase()}`}>{item.label}</button>
              ))}
            </nav>
            <div className="relative group hidden md:block">
              <button className="p-2 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)] transition-all" data-testid="export-button"><DownloadSimple size={18} /></button>
              <div className="absolute right-0 top-full mt-1 w-36 bg-[var(--surface-0)] border border-[var(--border-default)] rounded-xl shadow-[var(--shadow-lg)] opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 overflow-hidden">
                <button onClick={() => handleExport('csv')} className="w-full text-left px-4 py-2.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)] transition-colors" data-testid="export-csv-button">Export CSV</button>
                <button onClick={() => handleExport('pdf')} className="w-full text-left px-4 py-2.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)] transition-colors" data-testid="export-pdf-button">Export PDF</button>
              </div>
            </div>
            <button onClick={toggleTheme} className="p-2 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)] transition-all" data-testid="theme-toggle">
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button onClick={logout} className="p-2 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)] transition-all" data-testid="logout-button" title="Sign out"><SignOut size={18} /></button>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-6">
        {loading ? (
          <div className="flex items-center justify-center py-24">
            <div className="h-10 w-10 animate-spin rounded-full border-[3px] border-solid border-[var(--accent-blue)] border-r-transparent" />
          </div>
        ) : (
          <div className="space-y-5">
            {/* Row 0: Greeting + mobile analyze */}
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[var(--text-tertiary)] mb-0.5">Welcome back,</p>
                <h2 className="text-lg sm:text-xl font-bold text-[var(--text-primary)] tracking-tight">{user?.name || 'User'}</h2>
              </div>
              <button onClick={handleAnalyze} disabled={aiAnalyzing || transactions.length === 0}
                className="sm:hidden flex items-center gap-1.5 h-9 px-4 rounded-lg bg-[var(--accent-blue)] text-white text-sm font-semibold shadow-[0_0_12px_rgba(59,130,246,0.2)] disabled:opacity-40"
                data-testid="analyze-finances-button-mobile">
                <Sparkle size={14} weight="fill" /> Analyze
              </button>
            </div>

            {/* Budget Alerts */}
            {budgetAlerts.length > 0 && (
              <div className="bg-[#FEF3C7] dark:bg-yellow-900/20 border border-[#FCD34D] dark:border-yellow-700/40 rounded-xl px-4 py-3" data-testid="budget-alerts">
                <div className="flex items-center gap-2 mb-1">
                  <Target size={16} weight="fill" className="text-[#D97706]" />
                  <p className="text-xs font-semibold text-[#92400E] dark:text-yellow-400">Budget Alerts</p>
                </div>
                {budgetAlerts.map(b => (
                  <p key={b.id} className="text-xs text-[#92400E] dark:text-yellow-300 ml-6">{b.category}: {b.percentage}% used</p>
                ))}
              </div>
            )}

            {/* Row 1: 4 KPI Cards */}
            <KPICards summary={summary} />

            {/* Row 2: Line Chart + AI Insights Sidebar */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-5">
              <div className="lg:col-span-8">
                <PrimaryLineChart monthlySeries={summary.monthly_series} />
              </div>
              <div className="lg:col-span-4">
                <QuickInsightsPanel onAnalyze={handleAnalyze} analyzing={aiAnalyzing} transactionCount={transactions.length} />
              </div>
            </div>

            {/* Row 3: Pie + Bar breakdown charts */}
            <ChartsSection transactions={transactions} />

            {/* Row 4: Add Transaction */}
            <TransactionForm onTransactionAdded={fetchData} />

            {/* Row 5: Transaction List */}
            <TransactionList transactions={transactions} onTransactionDeleted={fetchData} />
          </div>
        )}
      </main>

      <BottomNav onExport={handleExport} />

      {showAIModal && (
        <AIInsightsModal isOpen={showAIModal} onClose={() => setShowAIModal(false)} insights={aiInsights} loading={aiAnalyzing} />
      )}
    </div>
  );
};
