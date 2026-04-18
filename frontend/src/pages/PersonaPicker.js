import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { User, Storefront, ChartBar, Moon, Sun, ArrowRight } from '@phosphor-icons/react';

const personas = [
  { id: 'individual', label: 'Individual', desc: 'Track spending, grow savings', icon: User, color: '#1D9E75', path: '/individual',
    img: 'https://images.unsplash.com/photo-1760865245986-2d863b76a847?w=600&q=60' },
  { id: 'shop_owner', label: 'Shop Owner', desc: 'Manage daily cash & sales', icon: Storefront, color: '#EF9F27', path: '/shop',
    img: 'https://images.unsplash.com/photo-1759004929774-cd6d6958f995?w=600&q=60' },
  { id: 'ca', label: 'Accountant (CA)', desc: 'Handle all your clients', icon: ChartBar, color: '#185FA5', path: '/ca',
    img: 'https://images.unsplash.com/photo-1761132492441-0884052f0f4e?w=600&q=60' },
];

export const PersonaPicker = () => {
  const { user, setPersona } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const nav = useNavigate();

  const pick = async (p) => {
    await setPersona(p.id);
    nav(p.path);
  };

  // Only auto-redirect if user navigated here naturally (not switching)
  const [switching, setSwitching] = React.useState(false);
  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('switch') === '1') { setSwitching(true); return; }
    if (user?.persona && !switching) {
      const p = personas.find(x => x.id === user.persona);
      if (p) nav(p.path, { replace: true });
    }
  }, [user, nav, switching]);

  return (
    <div className="min-h-screen bg-[var(--p-bg)] flex flex-col items-center justify-center p-6" data-testid="persona-picker">
      <div className="absolute top-4 right-4">
        <button onClick={toggleTheme} className="p-2 rounded-lg text-[var(--p-text-muted)] hover:text-[var(--p-text)] hover:bg-[var(--p-border-subtle)] transition-all" data-testid="theme-toggle-persona">
          {theme==='dark'?<Sun size={18}/>:<Moon size={18}/>}
        </button>
      </div>
      <div className="text-center mb-10">
        <p className="text-xs font-semibold tracking-widest uppercase text-[var(--p-text-muted)] mb-2">Capital Care AI</p>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--p-text)] font-['Outfit'] mb-2">Your money, your way</h1>
        <p className="text-sm text-[var(--p-text-secondary)]">Choose how you manage your finances</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-5 w-full max-w-3xl">
        {personas.map(p => (
          <button key={p.id} onClick={() => pick(p)}
            className="group relative overflow-hidden bg-[var(--p-surface)] border border-[var(--p-border)] rounded-2xl p-6 text-left transition-all hover:shadow-lg hover:border-transparent hover:ring-2 active:scale-[0.98]"
            style={{ '--ring-color': p.color }}
            data-testid={`persona-${p.id}`}
          >
            <div className="absolute inset-0 opacity-[0.07] group-hover:opacity-[0.12] transition-opacity" style={{backgroundImage:`url('${p.img}')`, backgroundSize:'cover'}} />
            <div className="relative z-10">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4" style={{ backgroundColor: `${p.color}15` }}>
                <p.icon size={24} weight="duotone" style={{ color: p.color }} />
              </div>
              <h3 className="text-lg font-bold text-[var(--p-text)] font-['Outfit'] mb-1">{p.label}</h3>
              <p className="text-xs text-[var(--p-text-secondary)] mb-4">{p.desc}</p>
              <div className="flex items-center gap-1 text-xs font-semibold" style={{ color: p.color }}>
                Get started <ArrowRight size={14} />
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
