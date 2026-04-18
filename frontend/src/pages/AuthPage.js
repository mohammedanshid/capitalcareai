import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Eye, EyeSlash, ArrowLeft } from '@phosphor-icons/react';

export const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false); const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
  const { login, register } = useAuth(); const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    const r = isLogin ? await login(email, password) : (!name.trim() ? (setError('Name required'), setLoading(false), null) : await register(name, email, password));
    setLoading(false);
    if (r?.success) nav('/dashboard'); else if (r) setError(r.error);
  };

  const inputClass = "w-full h-12 bg-white border border-[var(--border)] rounded-2xl px-4 text-sm text-[var(--dark)] placeholder-[var(--muted)] focus:border-[var(--coral)] focus:ring-2 focus:ring-[var(--coral)]/20 outline-none transition-all";

  return (
    <div className="min-h-screen bg-[var(--cream-light)] flex items-center justify-center p-4" data-testid="auth-page">
      <div className="w-full max-w-[400px]">
        <button onClick={() => nav('/')} className="flex items-center gap-1.5 text-sm text-[var(--muted)] hover:text-[var(--dark)] mb-8 transition-colors"><ArrowLeft size={16}/> Back to home</button>
        <div className="cashly-card p-8">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-8 h-8 rounded-full bg-[var(--dark)] flex items-center justify-center"><span className="text-white text-xs font-bold">CC</span></div>
            <span className="text-lg font-bold text-[var(--dark)]">Capital Care AI</span>
          </div>
          <h1 className="text-2xl font-extrabold text-[var(--dark)] mb-1">{isLogin ? 'Welcome back' : 'Create account'}</h1>
          <p className="text-sm text-[var(--muted)] mb-6">{isLogin ? 'Sign in to your dashboard' : 'Start managing your finances for free'}</p>
          <form onSubmit={submit} className="space-y-3.5" data-testid={isLogin ? 'login-form' : 'register-form'}>
            {!isLogin && <input type="text" value={name} onChange={e=>setName(e.target.value)} className={inputClass} placeholder="Full name" data-testid="name-input"/>}
            <input type="email" value={email} onChange={e=>setEmail(e.target.value)} className={inputClass} placeholder="Email address" required data-testid="email-input"/>
            <div className="relative">
              <input type={showPw?'text':'password'} value={password} onChange={e=>setPassword(e.target.value)} className={`${inputClass} pr-12`} placeholder="Password" required data-testid="password-input"/>
              <button type="button" onClick={()=>setShowPw(!showPw)} className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--muted)]" data-testid="toggle-password-visibility">{showPw?<EyeSlash size={18}/>:<Eye size={18}/>}</button>
            </div>
            {error && <div className="bg-[var(--red-light)] rounded-2xl px-4 py-2.5" data-testid="auth-error-message"><p className="text-xs text-[var(--red)]">{error}</p></div>}
            <button type="submit" disabled={loading} className="w-full btn-coral h-12 text-sm disabled:opacity-50" data-testid="auth-submit-button">{loading ? 'Please wait...' : isLogin ? 'Sign in' : 'Create account'}</button>
          </form>
          <p className="mt-5 text-center text-xs text-[var(--muted)]">{isLogin?"Don't have an account? ":"Already have an account? "}<button onClick={()=>{setIsLogin(!isLogin);setError('');}} className="text-[var(--coral)] font-semibold hover:underline" data-testid="toggle-auth-mode-button">{isLogin?'Sign up free':'Sign in'}</button></p>
        </div>
      </div>
    </div>
  );
};
