import React, { useState } from 'react';
import { Field, Label, Input } from '@headlessui/react';
import { CircleStackIcon, MagnifyingGlassIcon, FireIcon } from '@heroicons/react/24/outline';

const DbTest = () => {
  const [mode, setMode] = useState('discovery'); // discovery | flood
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState(null);

  const runDbTest = () => {
      if(!url) return alert("Enter Base URL");
      setLoading(true);
      setLogs([]);
      setResult(null);

      // شبیه‌سازی لاگ برای حس بهتر
      setLogs(prev => [...prev, `> Initializing ${mode} module...`, `> Target: ${url}`]);

      if(window.pywebview) {
          window.pywebview.api.run_db_test(url, mode).then(res => {
              setLoading(false);
              setResult(res);
              if(mode === 'discovery') {
                  setLogs(prev => [...prev, `> Scan complete. Found ${res.count} endpoints.`]);
              } else {
                  setLogs(prev => [...prev, `> Flood complete.`, `> Held: ${res.held_successfully}`, `> Dropped: ${res.dropped_or_timeout}`]);
              }
          });
      } else {
          // Demo mode
          setTimeout(() => {
              setLoading(false);
              setResult({ count: 2, endpoints_found: ['/api/users', '/api/admin'] });
          }, 2000);
      }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
       {/* Header */}
       <div className="flex items-center gap-4 mb-8">
           <div className="p-3 bg-blue-500/10 rounded-xl">
               <CircleStackIcon className="w-8 h-8 text-blue-400" />
           </div>
           <div>
               <h2 className="text-2xl font-bold text-white">Database Stress Tool</h2>
               <p className="text-gray-400 text-sm">Discover exposed endpoints or stress connection pools.</p>
           </div>
       </div>

       {/* Tabs */}
       <div className="flex bg-black/20 p-1 rounded-xl w-fit">
           <button 
             onClick={() => setMode('discovery')}
             className={`px-6 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${mode === 'discovery' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
           >
               <MagnifyingGlassIcon className="w-4 h-4" /> Discovery
           </button>
           <button 
             onClick={() => setMode('connection_flood')}
             className={`px-6 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${mode === 'connection_flood' ? 'bg-red-600 text-white shadow-lg shadow-red-500/30' : 'text-gray-400 hover:text-white'}`}
           >
               <FireIcon className="w-4 h-4" /> Connection Flood
           </button>
       </div>

       {/* Input Area */}
       <div className="glass-card p-6 flex gap-4 items-end">
           <Field className="flex-1">
               <Label className="text-xs text-gray-500 ml-1">Database API Base URL</Label>
               <Input 
                 value={url}
                 onChange={e => setUrl(e.target.value)}
                 className="glass-input w-full mt-1 h-12" 
                 placeholder={mode === 'discovery' ? "e.g. http://localhost:8000" : "e.g. http://localhost:8000/api/heavy-query"}
               />
           </Field>
           <button 
             onClick={runDbTest}
             disabled={loading}
             className={`h-12 px-8 rounded-lg font-bold border border-white/10 transition-all ${mode === 'discovery' ? 'bg-blue-600/80 hover:bg-blue-600' : 'bg-red-600/80 hover:bg-red-600'} disabled:opacity-50 disabled:cursor-not-allowed`}
           >
               {loading ? 'Running...' : (mode === 'discovery' ? 'SCAN' : 'ATTACK')}
           </button>
       </div>

       {/* Terminal Output */}
       <div className="glass-panel p-0 overflow-hidden rounded-xl min-h-[300px] flex flex-col">
           <div className="bg-black/40 px-4 py-2 text-xs font-mono text-gray-500 border-b border-white/5 flex justify-between">
               <span>TERMINAL OUTPUT</span>
               <span>{mode.toUpperCase()}_MODE</span>
           </div>
           <div className="p-4 font-mono text-sm space-y-1 flex-1 overflow-y-auto max-h-[400px]">
               {logs.map((log, i) => <div key={i} className="text-gray-400">{log}</div>)}
               
               {/* Result Display inside Terminal */}
               {result && mode === 'discovery' && (
                   <div className="mt-4 space-y-1">
                       {result.endpoints_found.length > 0 ? (
                           result.endpoints_found.map(ep => (
                               <div key={ep} className="text-green-400">
                                   [+] Found Endpoint: <span className="text-white underline">{ep}</span>
                               </div>
                           ))
                       ) : (
                           <div className="text-yellow-500">[-] No standard endpoints found.</div>
                       )}
                   </div>
               )}

               {result && mode === 'connection_flood' && (
                   <div className="mt-4 grid grid-cols-2 gap-4 max-w-sm">
                       <div className="bg-green-500/10 p-2 rounded border border-green-500/20">
                           <div className="text-green-500 text-xs">HELD</div>
                           <div className="text-xl text-white">{result.held_successfully}</div>
                       </div>
                       <div className="bg-red-500/10 p-2 rounded border border-red-500/20">
                           <div className="text-red-500 text-xs">DROPPED</div>
                           <div className="text-xl text-white">{result.dropped_or_timeout}</div>
                       </div>
                   </div>
               )}
           </div>
       </div>
    </div>
  );
};

export default DbTest;