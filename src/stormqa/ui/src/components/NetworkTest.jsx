import React, { useState, useEffect } from 'react';
import { Field, Label, Input } from '@headlessui/react';
import { WifiIcon, SignalIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/solid';
import CustomSelect from './CustomSelect';

const NetworkTest = () => {
  const [url, setUrl] = useState('');
  const [profile, setProfile] = useState('4G_LTE');
  const [profilesList, setProfilesList] = useState(['4G_LTE', 'GOOD_WIFI', '3G_SLOW', 'METRO_SPOT']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (window.pywebview) {
        window.pywebview.api.get_network_profiles().then(res => setProfilesList(res));
    }
  }, []);

  const runTest = () => {
    if (!url) return alert("Please enter a Target URL");
    setLoading(true);
    setResult(null);

    if (window.pywebview) {
        window.pywebview.api.run_network_test(url, profile).then(res => {
            setLoading(false);
            setResult(res);
        });
    } else {
        setTimeout(() => {
            setLoading(false);
            setResult({ status: 'success', simulated_delay: 120, real_network_time: 45, total_time: 165 });
        }, 1500);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="text-center space-y-2">
         <div className="inline-flex p-4 rounded-full bg-purple-500/10 shadow-[0_0_20px_rgba(168,85,247,0.3)] mb-4">
            <SignalIcon className="w-12 h-12 text-purple-400" />
         </div>
         <h2 className="text-3xl font-bold text-white">Network Simulation</h2>
         <p className="text-gray-400">Emulate real-world network conditions (Latency, Jitter, Packet Loss).</p>
      </div>

      <div className="glass-card p-8 space-y-6 relative overflow-visible z-20">
         {loading && (
             <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-purple-500 to-transparent animate-shimmer"></div>
         )}

         <div className="flex flex-col md:flex-row gap-6 items-end">
             <Field className="flex-grow w-full md:w-2/3">
                 <Label className="text-xs text-gray-400 ml-1 block mb-1">Target URL</Label>
                 <Input 
                    value={url} 
                    onChange={e => setUrl(e.target.value)} 
                    className="glass-input w-full h-12 text-lg" 
                    placeholder="https://example.com" 
                 />
             </Field>
             <div className="w-full md:w-1/3">
                 <CustomSelect 
                    label="Network Profile" 
                    value={profile} 
                    onChange={setProfile} 
                    options={profilesList}
                 />
             </div>
         </div>

         <button 
            onClick={runTest} 
            disabled={loading}
            className={`w-full h-14 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-3 ${loading ? 'bg-gray-700 cursor-not-allowed' : 'bg-purple-600/80 hover:bg-purple-600 shadow-[0_0_15px_rgba(168,85,247,0.5)]'}`}
         >
            {loading ? (
                <>
                   <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                   Simulating Traffic...
                </>
            ) : (
                <>
                   <WifiIcon className="w-6 h-6" /> Run Diagnostics
                </>
            )}
         </button>
      </div>

      {result && (
          <div className={`glass-card p-6 border-l-4 ${result.status === 'success' ? 'border-l-green-500' : 'border-l-red-500'} animate-in fade-in slide-in-from-bottom-4 relative z-10`}>
              <div className="flex items-start gap-4">
                  {result.status === 'success' ? <CheckCircleIcon className="w-10 h-10 text-green-400 mt-1" /> : <ExclamationTriangleIcon className="w-10 h-10 text-red-400 mt-1" />}
                  <div className="flex-1">
                      <h3 className="text-xl font-bold text-white mb-2">{result.status === 'success' ? 'Connection Established' : 'Connection Failed'}</h3>
                      {result.status === 'success' ? (
                          <div className="grid grid-cols-2 gap-4 mt-4">
                              <div className="bg-black/20 p-3 rounded-lg"><div className="text-xs text-gray-500">Simulated Latency</div><div className="text-xl font-mono text-purple-300">{result.simulated_delay} ms</div></div>
                              <div className="bg-black/20 p-3 rounded-lg"><div className="text-xs text-gray-500">Real Network Time</div><div className="text-xl font-mono text-blue-300">{parseFloat(result.real_network_time).toFixed(2)} ms</div></div>
                              <div className="bg-black/20 p-3 rounded-lg col-span-2"><div className="text-xs text-gray-500">Total Round Trip</div><div className="text-2xl font-bold text-white">{parseFloat(result.total_time || 0).toFixed(0)} ms</div></div>
                          </div>
                      ) : (
                          <p className="text-red-300 bg-red-500/10 p-4 rounded-lg mt-2 font-mono text-sm">{result.message}</p>
                      )}
                  </div>
              </div>
          </div>
      )}
    </div>
  );
};

export default NetworkTest;