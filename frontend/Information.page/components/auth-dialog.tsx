'use client'

import { useState } from 'react';
import { login, register } from '@/lib/authService';

type AuthDialogProps = {
  onClose: () => void;
  onSuccess: () => void;
};

export function AuthDialog({ onClose, onSuccess }: AuthDialogProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(email, password);
        await login(email, password);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#172a2a]/35 p-4 backdrop-blur-sm"
         onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <section className="w-full max-w-sm rounded-[26px] border border-[#e4dbcf] bg-[#fffdf9] p-6 shadow-2xl">
        <h2 className="text-2xl font-semibold tracking-tight text-[#263d39]">
          {isLogin ? 'Log in' : 'Create an account'}
        </h2>
        {error && <p className="mt-3 rounded-xl bg-[#f8eee4] p-3 text-sm text-[#8e4e3b]">{error}</p>}
        <form onSubmit={handleSubmit} className="mt-5 grid gap-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#48574f]">Email</label>
            <input 
              type="email" 
              required 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              className="w-full rounded-xl border border-[#ded8ce] px-3 py-2.5 text-sm outline-none focus:border-[#bd9b58] focus:ring-2 focus:ring-[#e9d9b4]/50" 
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#48574f]">Password</label>
            <input 
              type="password" 
              required 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              className="w-full rounded-xl border border-[#ded8ce] px-3 py-2.5 text-sm outline-none focus:border-[#bd9b58] focus:ring-2 focus:ring-[#e9d9b4]/50" 
            />
          </div>
          <button 
            type="submit" 
            disabled={loading}
            className="mt-2 rounded-xl bg-[#17352f] px-5 py-3 text-sm font-semibold text-[#f5d282] transition hover:bg-[#285248] disabled:opacity-50"
          >
            {loading ? 'Processing...' : isLogin ? 'Log In' : 'Sign Up'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-[#68756e]">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button type="button" onClick={() => setIsLogin(!isLogin)} className="font-semibold text-[#a17a35]">
            {isLogin ? 'Sign up' : 'Log in'}
          </button>
        </p>
      </section>
    </div>
  );
}
