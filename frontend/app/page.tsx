'use client';

import { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function Home() {
  const [isSimulating, setIsSimulating] = useState(false);
  const [backendData, setBackendData] = useState<any[]>([]);
  const [currentEpochIndex, setCurrentEpochIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(500);

  const [simParams, setSimParams] = useState({
    liczba_wysp: 5,
    wielkosc_wyspy: 40,
    liczba_epok: 100,
    co_ile_kolonizacja: 10,
    tempo_mutacji: 0.03,
    szansa_na_mutacje: 0.2,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying && currentEpochIndex < backendData.length - 1) {
      timer = setTimeout(() => {
        setCurrentEpochIndex(prev => prev + 1);
      }, playbackSpeed);
    } else if (currentEpochIndex >= backendData.length - 1 && !isSimulating) {
      setIsPlaying(false);
    }
    return () => clearTimeout(timer);
  }, [isPlaying, currentEpochIndex, backendData.length, playbackSpeed, isSimulating]);

  const handleParamChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setSimParams(prev => ({
      ...prev,
      [name]: parseFloat(value)
    }));
  };

  const startSimulation = async () => {
    setIsSimulating(true);
    setBackendData([]);
    setCurrentEpochIndex(0);
    setIsPlaying(true);
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/symulacja`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(simParams), 
        signal: abortControllerRef.current.signal
      });

      if (!response.body) throw new Error('Brak strumienia');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let isDone = false;
      while (!isDone) {
        const { value, done } = await reader.read();
        if (done) {
          isDone = true;
          break;
        }
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '');
            if (dataStr.trim()) {
              const data = JSON.parse(dataStr);
              setBackendData(prev => [...prev, data]);
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error("Błąd symulacji:", error);
      }
    } finally {
      setIsSimulating(false);
    }
  };

  const stopSimulation = () => {
    if (abortControllerRef.current) abortControllerRef.current.abort();
    setIsPlaying(false);
    setIsSimulating(false);
  };

  const currentData = backendData[currentEpochIndex] || null;
  const chartData = backendData.slice(0, currentEpochIndex + 1);
  const latestProfile = [...chartData].reverse().find(d => d.profil_psychologiczny)?.profil_psychologiczny;

  return (
    <main className="min-h-screen p-4 md:p-8 bg-slate-100 font-sans text-slate-900">
      <div className="max-w-6xl mx-auto space-y-6">
        
        <header className="flex justify-between items-end border-b border-slate-300 pb-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-800">Dylemat Więźnia</h1>
            <p className="text-slate-500">Symulacja Ewolucyjna w Modelu Wyspowym</p>
          </div>
          <div className="text-right">
            <span className="text-sm text-slate-500 block mb-1">Pobrano epok: {backendData.length} z {simParams.liczba_epok}</span>
            {!isSimulating ? (
              <button onClick={startSimulation} className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors shadow-md">
                Uruchom Symulację
              </button>
            ) : (
              <button onClick={stopSimulation} className="bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-6 rounded-lg transition-colors shadow-md animate-pulse">
                Przerwij API
              </button>
            )}
          </div>
        </header>

        
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            ⚙️ Parametry Środowiska
            {isSimulating && <span className="text-xs font-normal text-amber-600 bg-amber-100 px-2 py-1 rounded-full">Zablokowane w trakcie symulacji</span>}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-600 flex justify-between">
                <span>Liczba Epok:</span> <span>{simParams.liczba_epok}</span>
              </label>
              <input type="range" name="liczba_epok" min="10" max="500" step="10" value={simParams.liczba_epok} onChange={handleParamChange} disabled={isSimulating} className="w-full cursor-pointer disabled:opacity-50" />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-600 flex justify-between">
                <span>Populacja (na wyspę):</span> <span>{simParams.wielkosc_wyspy}</span>
              </label>
              <input type="range" name="wielkosc_wyspy" min="10" max="100" step="5" value={simParams.wielkosc_wyspy} onChange={handleParamChange} disabled={isSimulating} className="w-full cursor-pointer disabled:opacity-50" />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-600 flex justify-between">
                <span>Liczba Wysp:</span> <span>{simParams.liczba_wysp}</span>
              </label>
              <input type="range" name="liczba_wysp" min="2" max="10" step="1" value={simParams.liczba_wysp} onChange={handleParamChange} disabled={isSimulating} className="w-full cursor-pointer disabled:opacity-50" />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-600 flex justify-between">
                <span>Cykl Kolonizacji (co X epok):</span> <span>{simParams.co_ile_kolonizacja}</span>
              </label>
              <input type="range" name="co_ile_kolonizacja" min="2" max="50" step="1" value={simParams.co_ile_kolonizacja} onChange={handleParamChange} disabled={isSimulating} className="w-full cursor-pointer disabled:opacity-50" />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-600 flex justify-between">
                <span>Szansa na Mutację Wagi:</span> <span>{(simParams.szansa_na_mutacje * 100).toFixed(0)}%</span>
              </label>
              <input type="range" name="szansa_na_mutacje" min="0.01" max="0.5" step="0.01" value={simParams.szansa_na_mutacje} onChange={handleParamChange} disabled={isSimulating} className="w-full cursor-pointer disabled:opacity-50" />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-semibold text-slate-600 flex justify-between">
                <span>Tempo Mutacji (Siła szumu):</span> <span>{simParams.tempo_mutacji.toFixed(3)}</span>
              </label>
              <input type="range" name="tempo_mutacji" min="0.005" max="0.1" step="0.005" value={simParams.tempo_mutacji} onChange={handleParamChange} disabled={isSimulating} className="w-full cursor-pointer disabled:opacity-50" />
            </div>

          </div>
        </div>

      
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex flex-wrap items-center gap-6">
          <button onClick={() => setIsPlaying(!isPlaying)} disabled={backendData.length === 0} className="w-24 bg-slate-800 text-white py-2 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50">
            {isPlaying ? 'Pauza' : 'Odtwarzaj'}
          </button>
          
          <div className="flex-1 flex items-center gap-4">
            <span className="text-sm font-semibold w-32">Tempo UI: {playbackSpeed}ms</span>
            <input type="range" min="20" max="1000" step="20" value={playbackSpeed} onChange={(e) => setPlaybackSpeed(Number(e.target.value))} className="flex-1 cursor-pointer" />
          </div>

          <div className="text-xl font-mono font-bold w-32 text-right text-blue-600">
            Epoka {currentData?.epoka || 0}
          </div>
        </div>

       
        <div className={`grid gap-4 ${simParams.liczba_wysp > 5 ? 'grid-cols-2 md:grid-cols-3 lg:grid-cols-5' : 'grid-cols-2 md:grid-cols-' + simParams.liczba_wysp}`}>
          {currentData?.statystyki_wysp.map((wyspa: any) => {
            const isWinner = currentData.zdarzenie_kolonizacji?.zwyciezca === wyspa.id;
            const isLoser = currentData.zdarzenie_kolonizacji?.przegrany === wyspa.id;
            
            return (
              <div key={wyspa.id} className={`relative p-4 rounded-xl border-2 transition-all duration-300 ${isWinner ? 'border-green-500 bg-green-50 scale-105 shadow-lg z-10' : isLoser ? 'border-red-500 bg-red-50 scale-95 opacity-80' : 'border-slate-200 bg-white'}`}>
                {isWinner && <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-full shadow-sm">KOLONIZATOR</span>}
                {isLoser && <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full shadow-sm">WYMARŁA</span>}
                
                <h3 className="text-center font-bold mb-2">Wyspa {wyspa.id}</h3>
                <div className="text-sm space-y-1">
                  <div className="flex justify-between border-b border-slate-100 pb-1">
                    <span className="text-slate-500">Fitness:</span>
                    <span className="font-mono">{wyspa.fitness}</span>
                  </div>
                  <div className="flex justify-between pt-1">
                    <span className="text-slate-500">Współpraca:</span>
                    <span className={`font-mono font-bold ${wyspa.wspolpraca_procent > 50 ? 'text-green-600' : 'text-orange-500'}`}>
                      {wyspa.wspolpraca_procent}%
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-12">
    
          <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 className="text-lg font-semibold mb-4">Dynamika Ewolucji (Współpraca %)</h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="epoka" tick={{fontSize: 12}} tickMargin={10} />
                  <YAxis domain={[0, 100]} tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                  <Legend />
                  <Line type="monotone" dataKey="wspolpraca_procent_globalna" name="Globalna Współpraca (%)" stroke="#3b82f6" strokeWidth={3} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col">
            <h2 className="text-lg font-semibold mb-4">Profil Psychologiczny</h2>
            {latestProfile ? (
              <div className="flex-1 space-y-3 text-sm font-mono bg-slate-900 text-green-400 p-4 rounded-lg overflow-x-auto shadow-inner">
                <div className="flex justify-between"><span>AllC:</span> <span>{latestProfile.AllC}</span></div>
                <div className="flex justify-between"><span>AllD:</span> <span>{latestProfile.AllD}</span></div>
                <div className="flex justify-between"><span>Grudger:</span> <span>{latestProfile.Grudger}</span></div>
                <div className="flex justify-between"><span>Alternator:</span> <span>{latestProfile.Alternator}</span></div>
                <div className="flex justify-between"><span>Joss:</span> <span>{latestProfile.Joss}</span></div>
                <div className="flex justify-between"><span>Sneaky:</span> <span>{latestProfile.SneakyPacifist}</span></div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center border-2 border-dashed border-slate-200 rounded-lg text-slate-400 text-sm p-4 text-center">
                Profil uaktualni się po 10. epoce z bufora...
              </div>
            )}
          </div>
        </div>

      </div>
    </main>
  );
}