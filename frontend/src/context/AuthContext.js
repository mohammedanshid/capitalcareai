import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);
const API = process.env.REACT_APP_BACKEND_URL;

const fmtErr = (d) => { if (!d) return 'Something went wrong'; if (typeof d === 'string') return d; if (Array.isArray(d)) return d.map(e => e?.msg || JSON.stringify(e)).join(' '); return String(d); };

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { checkAuth(); }, []);
  const checkAuth = async () => {
    try { const { data } = await axios.get(`${API}/api/auth/me`, { withCredentials: true }); setUser(data); }
    catch { setUser(false); }
    finally { setLoading(false); }
  };

  const login = async (email, password) => {
    try {
      const { data } = await axios.post(`${API}/api/auth/login`, { email, password }, { withCredentials: true });
      // Auto-set persona to individual
      try { await axios.post(`${API}/api/persona/select`, { persona: 'individual' }, { withCredentials: true }); } catch {}
      setUser({ ...data, persona: 'individual' });
      return { success: true };
    } catch (e) { return { success: false, error: fmtErr(e.response?.data?.detail) }; }
  };

  const register = async (name, email, password) => {
    try {
      const { data } = await axios.post(`${API}/api/auth/register`, { name, email, password }, { withCredentials: true });
      try { await axios.post(`${API}/api/persona/select`, { persona: 'individual' }, { withCredentials: true }); } catch {}
      setUser({ ...data, persona: 'individual' });
      return { success: true };
    } catch (e) { return { success: false, error: fmtErr(e.response?.data?.detail) }; }
  };

  const logout = async () => {
    try { await axios.post(`${API}/api/auth/logout`, {}, { withCredentials: true }); } catch {}
    setUser(false);
  };

  return <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>;
};
