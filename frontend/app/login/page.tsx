'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch('/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });

    if (res.ok) {
      router.push('/');
      router.refresh();
    } else {
      setError(true);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-100">
      <form onSubmit={handleLogin} className="bg-white p-8 rounded-xl shadow-md border border-slate-200 max-w-sm w-full space-y-4">
        <h1 className="text-xl font-bold text-slate-800 text-center">Strona chroniona</h1>
        <p className="text-sm text-slate-500 text-center">Podaj hasło, aby uzyskać dostęp do symulatora inżynierskiego.</p>
        <div>
          <input
            type="password"
            placeholder="Hasło dostępu"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
          />
        </div>
        {error && <p className="text-red-500 text-xs text-center">Nieprawidłowe hasło!</p>}
        <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition-colors">
          Wejdź do systemu
        </button>
      </form>
    </main>
  );
}
