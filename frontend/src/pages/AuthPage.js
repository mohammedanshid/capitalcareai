import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { Eye, EyeSlash, Moon, Sun } from '@phosphor-icons/react';

export const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false); const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
  const { login, register } = useAuth(); const { theme, toggleTheme } = useTheme(); const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    const r = isLogin ? await login(email, password) : (!name.trim() ? (setError('Name required'), setLoading(false), null) : await register(name, email, password));
    setLoading(false);
    if (r?.success) nav('/persona'); else if (r) setError(r.error);
  };

  return (
    <div className="min-h-screen flex" data-testid="auth-page">
      <div className="hidden lg:flex lg:w-[45%] bg-gradient-to-br from-[#0F172A] to-[#1E293B] relative overflow-hidden items-end p-12 pb-16">
        <div className="absolute inset-0 opacity-20" style={{backgroundImage:"url('https://images.unsplash.com/photo-1760865245986-2d863b76a847?w=800')", backgroundSize:'cover'}} />
        <div className="relative z-10">
          <h2 className="text-4xl font-extrabold text-white tracking-tight leading-tight mb-3 font-['Outfit']">Your money,<br/>your way.</h2>
          <p className="text-white/50 text-sm max-w-xs">Three powerful dashboards for Individuals, Shop Owners, and Chartered Accountants.</p>
        </div>
      </div>
      <div className="w-full lg:w-[55%] flex items-center justify-center p-6 sm:p-10 bg-[var(--p-bg)]">
        <div className="w-full max-w-[380px]">
          <div className="flex justify-end mb-6">
            <button onClick={toggleTheme} className="p-2 rounded-lg text-[var(--p-text-muted)] hover:text-[var(--p-text)] hover:bg-[var(--p-border-subtle)] transition-all" data-testid="theme-toggle-auth">
              {theme === 'dark' ? <Sun size={18}/> : <Moon size={18}/>}
            </button>
          </div>
          <p className="text-xs font-semibold text-[var(--p-primary)] tracking-widest uppercase mb-2">Capital Care AI</p>
          <h1 className="text-3xl font-extrabold tracking-tight text-[var(--p-text)] font-['Outfit'] mb-1">{isLogin ? 'Welcome back' : 'Create account'}</h1>
          <p className="text-sm text-[var(--p-text-secondary)] mb-6">{isLogin ? 'Sign in to your account' : 'Start managing your finances'}</p>
          <form onSubmit={submit} className="space-y-3.5" data-testid={isLogin ? 'login-form' : 'register-form'}>
            {!isLogin && <div><label className="block text-xs font-medium text-[var(--p-text)] mb-1">Name</label><input type="text" value={name} onChange={e=>setName(e.target.value)} className="w-full h-10 bg-[var(--p-surface)] border border-[var(--p-border)] rounded-lg px-3 text-sm text-[var(--p-text)] placeholder-[var(--p-text-muted)] focus:border-[var(--p-primary)] focus:ring-2 focus:ring-[var(--p-primary)]/20 outline-none" placeholder="Your name" data-testid="name-input"/></div>}
            <div><label className="block text-xs font-medium text-[var(--p-text)] mb-1">Email</label><input type="email" value={email} onChange={e=>setEmail(e.target.value)} className="w-full h-10 bg-[var(--p-surface)] border border-[var(--p-border)] rounded-lg px-3 text-sm text-[var(--p-text)] placeholder-[var(--p-text-muted)] focus:border-[var(--p-primary)] focus:ring-2 focus:ring-[var(--p-primary)]/20 outline-none" placeholder="you@example.com" required data-testid="email-input"/></div>
            <div><label className="block text-xs font-medium text-[var(--p-text)] mb-1">Password</label><div className="relative"><input type={showPw?'text':'password'} value={password} onChange={e=>setPassword(e.target.value)} className="w-full h-10 bg-[var(--p-surface)] border border-[var(--p-border)] rounded-lg px-3 pr-10 text-sm text-[var(--p-text)] placeholder-[var(--p-text-muted)] focus:border-[var(--p-primary)] focus:ring-2 focus:ring-[var(--p-primary)]/20 outline-none" placeholder="••••••••" required data-testid="password-input"/><button type="button" onClick={()=>setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--p-text-muted)]" data-testid="toggle-password-visibility">{showPw?<EyeSlash size={16}/>:<Eye size={16}/>}</button></div></div>
            {error && <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2" data-testid="auth-error-message"><p className="text-xs text-red-600 dark:text-red-400">{error}</p></div>}
            <button type="submit" disabled={loading} className="w-full h-10 bg-[var(--p-text)] text-[var(--p-bg)] rounded-lg text-sm font-semibold hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50" data-testid="auth-submit-button">{loading ? 'Please wait...' : isLogin ? 'Sign in' : 'Create account'}</button>
          </form>
          <p className="mt-5 text-center text-xs text-[var(--p-text-muted)]">{isLogin?"Don't have an account? ":"Already have an account? "}<button onClick={()=>{setIsLogin(!isLogin);setError('');}} className="text-[var(--p-primary)] font-medium hover:underline" data-testid="toggle-auth-mode-button">{isLogin?'Sign up':'Sign in'}</button></p>
        </div>
      </div>
    </div>
  );
};
