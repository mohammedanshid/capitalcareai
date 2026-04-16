import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Eye, EyeSlash } from '@phosphor-icons/react';

export const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    let result;
    if (isLogin) {
      result = await login(email, password);
    } else {
      if (!name.trim()) {
        setError('Name is required');
        setLoading(false);
        return;
      }
      result = await register(name, email, password);
    }

    setLoading(false);
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="auth-page">
      {/* Left Side - Image */}
      <div
        className="hidden lg:block lg:w-1/2 bg-cover bg-center relative"
        style={{
          backgroundImage: `url('https://static.prod-images.emergentagent.com/jobs/04c5176c-a459-4d76-8697-f64bc179b7af/images/e3ee49d1216bd2430b9130014eeaa9d9cebbec9c4055e038364806e1b75e95f6.png')`,
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent"></div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-10 bg-[#FDFDFD]">
        <div className="w-full max-w-md">
          <div className="mb-8">
            <h1 className="text-4xl lg:text-5xl font-bold tracking-tighter text-[#09090B] font-['Outfit'] mb-3">
              {isLogin ? 'Welcome Back' : 'Get Started'}
            </h1>
            <p className="text-base text-[#52525B] font-['Manrope']">
              {isLogin ? 'Sign in to manage your finances' : 'Create an account to track your money'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5" data-testid={isLogin ? 'login-form' : 'register-form'}>
            {!isLogin && (
              <div>
                <label htmlFor="name" className="text-sm font-semibold text-[#09090B] mb-2 block font-['Manrope']">
                  Full Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-[#FDFDFD] border border-[#E4E4E7] rounded-lg px-4 py-3 text-base focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] outline-none transition-all font-['Manrope']"
                  placeholder="John Doe"
                  required={!isLogin}
                  data-testid="name-input"
                />
              </div>
            )}

            <div>
              <label htmlFor="email" className="text-sm font-semibold text-[#09090B] mb-2 block font-['Manrope']">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#FDFDFD] border border-[#E4E4E7] rounded-lg px-4 py-3 text-base focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] outline-none transition-all font-['Manrope']"
                placeholder="you@example.com"
                required
                data-testid="email-input"
              />
            </div>

            <div>
              <label htmlFor="password" className="text-sm font-semibold text-[#09090B] mb-2 block font-['Manrope']">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#FDFDFD] border border-[#E4E4E7] rounded-lg px-4 py-3 text-base focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] outline-none transition-all font-['Manrope'] pr-12"
                  placeholder="••••••••"
                  required
                  data-testid="password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-[#A1A1AA] hover:text-[#09090B] transition-colors"
                  data-testid="toggle-password-visibility"
                >
                  {showPassword ? <EyeSlash size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-[#FEE2E2] border border-[#EF4444] rounded-lg p-3" data-testid="auth-error-message">
                <p className="text-sm text-[#991B1B] font-['Manrope']">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#09090B] text-white rounded-lg px-6 py-3 font-semibold tracking-wide transition-all hover:bg-[#27272A] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed font-['Manrope']"
              data-testid="auth-submit-button"
            >
              {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
              }}
              className="text-sm text-[#52525B] hover:text-[#09090B] transition-colors font-['Manrope']"
              data-testid="toggle-auth-mode-button"
            >
              {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
