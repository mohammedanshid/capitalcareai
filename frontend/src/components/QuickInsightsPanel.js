import React, { useState, useEffect } from 'react';
import { Sparkle, Lightning, ArrowRight } from '@phosphor-icons/react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const QuickInsightsPanel = ({ onAnalyze, analyzing, transactionCount }) => {
  const [latest, setLatest] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLatest();
  }, []);

  const fetchLatest = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/api/analyze/latest`, { withCredentials: true });
      if (data.has_analysis) setLatest(data);
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  // Extract first 3 bullet points from insights
  const getQuickTips = (text) => {
    if (!text) return [];
    const bullets = [];
    const lines = text.split('\n');
    for (const line of lines) {
      const m = line.trim().match(/^[-•*]\s+(.+)/);
      if (m && bullets.length < 3) bullets.push(m[1]);
    }
    return bullets;
  };

  const tips = latest ? getQuickTips(latest.insights) : [];

  return (
    <div className="bg-[var(--surface-0)] border border-[var(--border-default)] rounded-xl p-4 sm:p-5 flex flex-col h-full" data-testid="quick-insights-panel">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-7 h-7 rounded-lg bg-[var(--accent-blue-bg)] flex items-center justify-center">
          <Lightning size={14} weight="fill" className="text-[var(--accent-blue)]" />
        </div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Quick Insights</h3>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-solid border-[var(--accent-blue)] border-r-transparent" />
        </div>
      ) : tips.length > 0 ? (
        <div className="flex-1 space-y-3">
          {tips.map((tip, i) => (
            <div key={i} className="flex items-start gap-2.5">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-[var(--surface-2)] text-[var(--text-tertiary)] text-[10px] font-bold flex items-center justify-center mt-0.5">{i + 1}</span>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-3">{tip}</p>
            </div>
          ))}
          {latest?.created_at && (
            <p className="text-[10px] text-[var(--text-tertiary)] mt-2">
              Last analysis: {new Date(latest.created_at).toLocaleDateString()}
            </p>
          )}
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-center py-4">
          <div className="w-10 h-10 rounded-full bg-[var(--accent-blue-bg)] flex items-center justify-center mb-3">
            <Sparkle size={18} weight="fill" className="text-[var(--accent-blue)]" />
          </div>
          <p className="text-xs text-[var(--text-secondary)] mb-1">No insights yet</p>
          <p className="text-[10px] text-[var(--text-tertiary)]">Run your first AI analysis</p>
        </div>
      )}

      <button
        onClick={onAnalyze}
        disabled={analyzing || transactionCount === 0}
        className="mt-4 w-full h-9 rounded-lg bg-[var(--accent-blue)] text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-all hover:bg-[var(--accent-blue-hover)] disabled:opacity-40 disabled:cursor-not-allowed shadow-[0_0_12px_rgba(59,130,246,0.2)]"
        data-testid="sidebar-analyze-button"
      >
        <Sparkle size={14} weight="fill" />
        {analyzing ? 'Analyzing...' : 'Analyze My Finances'}
        {!analyzing && <ArrowRight size={12} />}
      </button>
    </div>
  );
};
