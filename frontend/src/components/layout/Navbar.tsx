import React, { useState } from 'react';
import { Sprout, Menu, X, CheckCircle2, AlertTriangle, MapPin } from 'lucide-react';
import { useFarm } from '../../context/FarmContext';

export type TabId = 'dashboard' | 'setup' | 'recommendations' | 'details' | 'simulator';

interface NavbarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
  const { profile, backendOnline, isConfigured } = useFarm();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems: { id: TabId; label: string }[] = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'setup', label: 'Farm Setup' },
    { id: 'recommendations', label: 'Recommendations' },
    { id: 'details', label: 'Crop Details' },
    { id: 'simulator', label: 'What-If Simulator' },
  ];

  const handleSelect = (id: TabId) => {
    onTabChange(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => handleSelect('dashboard')}>
            <div className="w-10 h-10 rounded-xl bg-emerald-700 flex items-center justify-center text-white shadow-sm">
              <Sprout className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xl font-extrabold tracking-tight text-slate-900">SWAMITRA</span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 tracking-wide uppercase">
                  Agri-AI
                </span>
              </div>
              <p className="text-[11px] text-slate-500 hidden sm:block font-medium">
                Agricultural Decision-Support System
              </p>
            </div>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleSelect(item.id)}
                  className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-all ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200/60 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Status Badges */}
          <div className="hidden lg:flex items-center gap-3">
            {/* Active Farm Quick Indicator */}
            {isConfigured && profile ? (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 font-medium">
                <MapPin className="w-3.5 h-3.5 text-emerald-700" />
                <span className="truncate max-w-[130px]">{profile.name || profile.locationName}</span>
                <span className="text-slate-400">({profile.farm_area_ha} ha)</span>
              </div>
            ) : (
              <button
                onClick={() => handleSelect('setup')}
                className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 underline"
              >
                + Configure Farm
              </button>
            )}

            {/* Backend status */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                backendOnline
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : 'bg-rose-50 text-rose-800 border-rose-200'
              }`}
              title={backendOnline ? 'FastAPI Backend Online' : 'FastAPI Backend Offline'}
            >
              {backendOnline ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>API Connected</span>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                  <span>API Offline</span>
                </>
              )}
            </div>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              aria-label="Toggle Menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-4 space-y-1 shadow-lg">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className={`w-full text-left px-3.5 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                  isActive
                    ? 'bg-emerald-50 text-emerald-800 font-bold'
                    : 'text-slate-700 hover:bg-slate-50'
                }`}
              >
                {item.label}
              </button>
            );
          })}

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>
              Status:{' '}
              <strong className={backendOnline ? 'text-emerald-700' : 'text-rose-600'}>
                {backendOnline ? 'Connected' : 'Offline'}
              </strong>
            </span>
            {profile && <span className="truncate">{profile.locationName}</span>}
          </div>
        </div>
      )}
    </header>
  );
};
