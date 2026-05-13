'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { Loader2 } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const supabase = createClient();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const { error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
    } else {
      router.push('/');
      router.refresh();
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[url('/bg-noise.png')]">
      <div className="w-full max-w-md glass-card p-8">
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl font-bold text-white mb-2">MAK Lead Engine</h1>
          <p className="text-white/60">Autonomous B2B Pipeline</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white/80 mb-1.5" htmlFor="email">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              placeholder="ahad@maksoftware.co"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-white/80 mb-1.5" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary mt-2 flex justify-center items-center"
          >
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
