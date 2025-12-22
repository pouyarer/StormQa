import React, { useState } from 'react';
import { Field, Label, Input } from '@headlessui/react';
import { ChatBubbleLeftRightIcon, PaperAirplaneIcon, ServerIcon } from '@heroicons/react/24/outline';

const WebSocketTest = () => {
  const [url, setUrl] = useState('ws://localhost:8765');
  const [message, setMessage] = useState('Hello StormQA');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const runTest = () => {
    if (!url) return alert("Enter WS URL");
    setLoading(true);
    setResult(null);

    if (window.pywebview) {
        window.pywebview.api.run_ws_test(url, message).then(res => {
            setLoading(false);
            setResult(res);
        });
    } else {
        // Demo Mode
        setTimeout(() => {
            setLoading(false);
            setResult({
                status: "success",
                sent: 10, received: 10, avg_latency: 45.5, errors: 0,
                logs: ["✅ Connected", "📩 Recv: Pong (45ms)", "🏁 Test Completed"]
            });
        }, 2000);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-10">
        <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-purple-500/10 rounded-xl">
                <ChatBubbleLeftRightIcon className="w-8 h-8 text-purple-400" />
            </div>
            <div>
                <h2 className="text-2xl font-bold text-white">WebSocket Stress</h2>
                <p className="text-gray-400 text-sm">Real-time bi-directional communication test.</p>
            </div>
        </div>

        {/* Input Config */}
        <div className="glass-card p-6 grid grid-cols-1 md:grid-cols-3 gap-6 items-end relative z-10">
            <Field className="md:col-span-2">
                <Label className="text-xs text-gray-400 ml-1 mb-1 block">Target WebSocket URL</Label>
                <Input value={url} onChange={e => setUrl(e.target.value)} className="glass-input w-full h-12 font-mono" placeholder="ws://echo.websocket.org" />
            </Field>
            
            <Field>
                <Label className="text-xs text-gray-400 ml-1 mb-1 block">Message Payload</Label>
                <Input value={message} onChange={e => setMessage(e.target.value)} className="glass-input w-full h-12" placeholder="Ping" />
            </Field>

            <button 
                onClick={runTest} 
                disabled={loading}
                className={`md:col-span-3 h-14 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all ${loading ? 'bg-gray-700 cursor-not-allowed' : 'bg-purple-600/80 hover:bg-purple-600 shadow-[0_0_15px_rgba(168,85,247,0.5)]'}`}
            >
                {loading ? <span className="animate-pulse">Connecting & Testing...</span> : <><PaperAirplaneIcon className="w-5 h-5"/> Send Traffic</>}
            </button>
        </div>

        {/* Results Area */}
        {result && (
            <div className="animate-in fade-in slide-in-from-bottom-4 space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="glass-card p-4 text-center border-l-4 border-blue-500">
                        <div className="text-xs text-gray-400">Messages Sent</div>
                        <div className="text-2xl font-bold text-blue-400">{result.sent}</div>
                    </div>
                    <div className="glass-card p-4 text-center border-l-4 border-green-500">
                        <div className="text-xs text-gray-400">Messages Recv</div>
                        <div className="text-2xl font-bold text-green-400">{result.received}</div>
                    </div>
                    <div className="glass-card p-4 text-center border-l-4 border-orange-500">
                        <div className="text-xs text-gray-400">Avg Latency</div>
                        <div className="text-2xl font-bold text-orange-400">{result.avg_latency.toFixed(1)} ms</div>
                    </div>
                    <div className="glass-card p-4 text-center border-l-4 border-red-500">
                        <div className="text-xs text-gray-400">Errors</div>
                        <div className="text-2xl font-bold text-red-400">{result.errors}</div>
                    </div>
                </div>

                {/* Log Terminal */}
                <div className="glass-panel p-0 overflow-hidden rounded-xl border border-white/10">
                    <div className="bg-black/40 px-4 py-2 text-xs font-mono text-gray-500 border-b border-white/5 flex items-center gap-2">
                        <ServerIcon className="w-3 h-3" /> CONNECTION LOG
                    </div>
                    <div className="p-4 bg-black/20 font-mono text-xs space-y-1 h-64 overflow-y-auto custom-scrollbar">
                        {result.logs.map((log, i) => (
                            <div key={i} className={`${log.includes('❌') || log.includes('🔥') ? 'text-red-400' : 'text-green-300'}`}>
                                <span className="opacity-50 mr-2">[{i+1}]</span>{log}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )}
    </div>
  );
};

export default WebSocketTest;