import React, { useState, useEffect } from 'react';
import { Field, Label, Input, Textarea } from '@headlessui/react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { PlusIcon, XMarkIcon, ArrowDownTrayIcon, ArrowUpTrayIcon, CommandLineIcon, DocumentIcon, FunnelIcon, FireIcon } from '@heroicons/react/24/outline';
import { CheckBadgeIcon, XCircleIcon } from '@heroicons/react/24/solid';
import CustomSelect from './CustomSelect'; 

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler);

const LoadTest = () => {
  const [url, setUrl] = useState('');
  const [method, setMethod] = useState('GET');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [headers, setHeaders] = useState('{"Content-Type": "application/json"}');
  const [body, setBody] = useState('');
  const [assertion, setAssertion] = useState('');
  const [extract, setExtract] = useState(''); 
  
  const [thresholdRules, setThresholdRules] = useState([]); 
  const [thresholdsStr, setThresholdsStr] = useState('');

  const [chaos, setChaos] = useState({ enabled: false, rate: 10, type: 'latency' });

  const [dataFile, setDataFile] = useState('');
  const [steps, setSteps] = useState([{ users: 10, duration: 30, ramp: 5, think: 0.5, jitter: 10 }]);
  
  const [isRunning, setIsRunning] = useState(false);
  const [stats, setStats] = useState({ users: 0, rps: 0, avg_latency: 0, failed: 0 });
  const [finalResult, setFinalResult] = useState(null);

  const [chartData, setChartData] = useState({
    labels: Array(20).fill(''),
    datasets: [{ fill: true, label: 'Active Users', data: Array(20).fill(0), borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', tension: 0.4 }],
  });

  useEffect(() => {
      const str = thresholdRules
        .filter(r => r.val !== '')
        .map(r => {
            let metricName = r.type;
            if (r.type === 'p') {
                metricName = `p${r.p_val || '95'}`; 
            }
            return `${metricName}<${r.val}`;
        })
        .join(', ');
      setThresholdsStr(str);
  }, [thresholdRules]);

  useEffect(() => {
    window.updateLiveStats = (newStats) => {
      setStats(newStats);
      setChartData(prev => {
        const newData = [...prev.datasets[0].data.slice(1), newStats.users];
        return { ...prev, datasets: [{ ...prev.datasets[0], data: newData }] };
      });
    };

    window.testFinished = (summary) => { 
        setIsRunning(false); 
        setFinalResult(summary); 
    };
    
    window.testError = (msg) => { setIsRunning(false); alert("Error: " + msg); };
    
    window.loadImportedData = (data) => {
        try {
            if(typeof data === 'string') data = JSON.parse(data);
            setUrl(data.url || "");
            setMethod(data.method || "GET");
            setSteps(data.steps || []);
            if (data.data_file) setDataFile(data.data_file);
            if (data.extract) setExtract(data.extract);
            if (data.chaos) setChaos(data.chaos);
            
            if (data.thresholds) {
                const loadedRules = data.thresholds.split(',').map(rule => {
                    const [metric, val] = rule.split('<');
                    let type = metric.trim();
                    let p_val = '';
                    if (type.startsWith('p')) {
                        p_val = type.substring(1); 
                        type = 'p';
                    }
                    return { type, p_val, val: val.trim() };
                });
                setThresholdRules(loadedRules);
            }

            if (data.headers || data.body || data.extract || data.thresholds || data.chaos?.enabled) setShowAdvanced(true);
            alert("Scenario Loaded Successfully!");
        } catch(e) {
            alert("Error parsing file.");
        }
    }
  }, []);

  const handleImportSqa = () => { if(window.pywebview) window.pywebview.api.load_scenario_file(); };
  
  const handleSaveSqa = () => { 
      if(window.pywebview) {
          window.pywebview.api.save_scenario_file(JSON.stringify({
              url, method, steps, data_file: dataFile, extract, thresholds: thresholdsStr, chaos,
              headers: JSON.parse(headers || '{}'), body: body ? JSON.parse(body) : null
          })).then(res => {
              if(res.status === 'success') alert("Saved to: " + res.path);
          });
      }
  };

  const handleSelectDataFile = () => {
      if(window.pywebview) {
          window.pywebview.api.select_data_file().then(path => {
              if(path) setDataFile(path);
          });
      }
  };

  const handleCurlImport = () => {
      const cmd = prompt("Paste cURL command here:");
      if(cmd && window.pywebview) {
          window.pywebview.api.parse_curl_command(cmd).then(res => {
              if(res.status === 'success') {
                  const d = res.data;
                  setUrl(d.url);
                  setMethod(d.method);
                  if(d.headers && Object.keys(d.headers).length > 0) {
                      setHeaders(JSON.stringify(d.headers, null, 2));
                      setShowAdvanced(true);
                  }
                  if(d.body) {
                      setBody(d.body);
                      setShowAdvanced(true);
                  }
              } else {
                  alert(res.message);
              }
          })
      }
  }

  const addRule = () => setThresholdRules([...thresholdRules, { type: 'p', p_val: '95', val: '' }]);
  const removeRule = (idx) => setThresholdRules(thresholdRules.filter((_, i) => i !== idx));
  const updateRule = (idx, key, val) => {
      const newRules = [...thresholdRules];
      newRules[idx][key] = val;
      setThresholdRules(newRules);
  };

  const addStep = () => setSteps([...steps, { users: 50, duration: 30, ramp: 5, think: 0.5, jitter: 10 }]);
  const removeStep = (idx) => { if(steps.length > 1) setSteps(steps.filter((_, i) => i !== idx)); };
  
  const updateStep = (idx, field, val) => {
      const s = [...steps];
      s[idx][field] = val;
      setSteps(s);
  };

  const startTest = () => {
    if (!url) return alert("Target URL is required");
    let parsedHeaders = {}, parsedBody = null;
    try {
        if(headers) parsedHeaders = JSON.parse(headers);
        if(body) parsedBody = JSON.parse(body);
    } catch(e) { return alert("Invalid JSON in Headers or Body"); }

    setFinalResult(null); 

    const config = { 
        url, method, headers: parsedHeaders, body: parsedBody, assertion, 
        data_file: dataFile, extract, 
        thresholds: thresholdsStr,
        chaos, 
        steps: steps.map(s => ({
            ...s, 
            users: parseInt(s.users), 
            duration: parseInt(s.duration),
            ramp: parseInt(s.ramp),
            think: parseFloat(s.think),
            jitter: parseInt(s.jitter)
        })) 
    };
    if(window.pywebview) { setIsRunning(true); window.pywebview.api.start_load_test(config); }
  };

  return (
    <div className="space-y-6 pb-10">
      <div className="flex justify-between items-end">
        <div><h2 className="text-2xl font-bold text-white mb-1">Load Scenario</h2><p className="text-gray-400 text-sm">Configure swarm attack.</p></div>
        <div className="flex gap-2">
            <button onClick={handleSelectDataFile} className={`glass-btn text-sm flex items-center gap-2 ${dataFile ? 'border-green-500/50 text-green-400' : ''}`} title={dataFile}>
                <DocumentIcon className="w-4 h-4"/> {dataFile ? 'CSV Attached' : 'Attach Data (CSV)'}
            </button>
            <div className="w-px h-8 bg-white/10 mx-1"></div>
            <button onClick={handleCurlImport} className="glass-btn text-sm flex items-center gap-2 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border-blue-500/30"><CommandLineIcon className="w-4 h-4"/>Import cURL</button>
            <button onClick={handleImportSqa} className="glass-btn text-sm flex items-center gap-2"><ArrowDownTrayIcon className="w-4 h-4"/> Import .sqa </button>
            <button onClick={handleSaveSqa} className="glass-btn text-sm flex items-center gap-2"><ArrowUpTrayIcon className="w-4 h-4"/> Save .sqa</button>
        </div>
      </div>

      <div className="glass-card p-6 space-y-4 relative z-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            <div className="w-full relative">
                <CustomSelect label="Method" value={method} onChange={setMethod} options={["GET", "POST", "PUT", "DELETE"]} />
            </div>
            <Field className="md:col-span-2">
                <Label className="text-xs text-gray-400 ml-1 mb-1 block">Target URL {dataFile && <span className="text-green-400 text-[10px] ml-2">(Use {'{{col_name}}'})</span>}</Label>
                <Input value={url} onChange={e => setUrl(e.target.value)} className="glass-input w-full h-12" placeholder="https://api.example.com/users/{{id}}" />
            </Field>
        </div>
        
        {dataFile && (
            <div className="text-xs text-gray-500 flex items-center gap-2 bg-black/20 p-2 rounded border border-white/5">
                <span className="text-green-400 font-bold">Data Source:</span> {dataFile}
                <button onClick={() => setDataFile('')} className="ml-auto text-red-400 hover:text-red-300">Remove</button>
            </div>
        )}
        
        <div>
            <button onClick={() => setShowAdvanced(!showAdvanced)} className="text-xs text-blue-400 hover:text-blue-300 underline">
                {showAdvanced ? '- Hide Advanced' : '+ Show Advanced (Headers, Chaos, Rules, Extraction)'}
            </button>
            {showAdvanced && (
                <div className="grid grid-cols-2 gap-4 mt-3 animate-in fade-in slide-in-from-top-2">
                    <Field>
                        <Label className="text-xs text-gray-500 ml-1">Headers (JSON)</Label>
                        <Textarea value={headers} onChange={e => setHeaders(e.target.value)} className="glass-input w-full h-24 font-mono text-xs mt-1 pt-2" placeholder='{"Authorization": "Bearer {{TOKEN}}"}' />
                    </Field>
                    <Field>
                        <Label className="text-xs text-gray-500 ml-1">Body (JSON)</Label>
                        <Textarea value={body} onChange={e => setBody(e.target.value)} className="glass-input w-full h-24 font-mono text-xs mt-1 pt-2" placeholder='{"username": "{{user}}"}'/>
                    </Field>
                    
                    <Field>
                          <Label className="text-xs text-gray-500 ml-1">Assertion (Response Check)</Label>
                          <Input value={assertion} onChange={e => setAssertion(e.target.value)} className="glass-input w-full mt-1" placeholder='e.g. "success": true OR status:201' />
                    </Field>
                    <Field>
                          <Label className="text-xs text-purple-400 font-bold ml-1">Extract Variable</Label>
                          <Input value={extract} onChange={e => setExtract(e.target.value)} className="glass-input w-full mt-1 border-purple-500/30" placeholder='e.g. TOKEN=json.auth.token' />
                    </Field>

                    <div className="col-span-2 bg-red-900/10 p-4 rounded-xl border border-red-500/20 mt-2 relative overflow-visible">
                        <div className="absolute -right-10 -top-10 w-32 h-32 bg-red-500/10 rounded-full blur-3xl pointer-events-none"></div>
                        
                        <div className="flex justify-between items-center mb-4 relative z-10">
                            <div className="text-sm text-red-400 font-bold flex gap-2 items-center">
                                <FireIcon className="w-5 h-5 animate-pulse"/> Chaos Injection (Failure Simulation)
                            </div>
                            
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] text-gray-400 uppercase tracking-widest">{chaos.enabled ? 'Active' : 'Disabled'}</span>
                                <button 
                                    onClick={() => setChaos({...chaos, enabled: !chaos.enabled})}
                                    className={`w-10 h-5 rounded-full p-1 transition-all ${chaos.enabled ? 'bg-red-500' : 'bg-gray-700'}`}
                                >
                                    <div className={`w-3 h-3 bg-white rounded-full shadow-md transition-all transform ${chaos.enabled ? 'translate-x-5' : 'translate-x-0'}`}></div>
                                </button>
                            </div>
                        </div>

                        {chaos.enabled && (
                            <div className="grid grid-cols-2 gap-6 animate-in fade-in slide-in-from-top-2 relative z-20">
                                <div className="w-full relative">
                                    <CustomSelect 
                                        label="Chaos Type"
                                        value={chaos.type === 'latency' ? "🐢 Network Lag (0.5s - 2s)" : "💣 Connection Drops (Exceptions)"}
                                        onChange={(val) => setChaos({
                                            ...chaos, 
                                            type: val === "🐢 Network Lag (0.5s - 2s)" ? 'latency' : 'exception'
                                        })}
                                        options={["🐢 Network Lag (0.5s - 2s)", "💣 Connection Drops (Exceptions)"]} 
                                    />
                                </div>

                                <div>
                                    <label className="text-[10px] text-gray-400 mb-1 block">Injection Rate ({chaos.rate}%)</label>
                                    <div className="flex gap-2 items-center h-12">
                                        <input 
                                            type="range" min="1" max="100" 
                                            value={chaos.rate} 
                                            onChange={e => setChaos({...chaos, rate: parseInt(e.target.value)})}
                                            className="w-full accent-red-500 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                                        />
                                        <span className="text-xs font-mono w-8 text-right text-red-200">{chaos.rate}%</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* --- Dynamic Threshold Builder --- */}
                    <div className="col-span-2 bg-black/20 p-4 rounded-xl border border-white/5 mt-2">
                        <div className="flex justify-between items-center mb-2">
                            <div className="text-xs text-orange-400 font-bold flex gap-2 items-center">
                                <FunnelIcon className="w-4 h-4"/> Success Criteria (Pass/Fail Rules)
                            </div>
                            <button onClick={addRule} className="text-[10px] bg-orange-500/10 text-orange-400 px-3 py-1 rounded hover:bg-orange-500/20 border border-orange-500/30">+ Add Rule</button>
                        </div>
                        
                        {thresholdRules.length === 0 && <div className="text-xs text-gray-600 text-center py-2">No rules defined. Test will always PASS.</div>}

                        <div className="space-y-2">
                            {thresholdRules.map((rule, idx) => (
                                <div key={idx} className="flex gap-2 items-center bg-white/5 p-2 rounded-lg">
                                    <span className="text-xs text-red-400 font-bold whitespace-nowrap">Fail if:</span>
                                    
                                    <select 
                                        value={rule.type} 
                                        onChange={e => updateRule(idx, 'type', e.target.value)}
                                        className="appearance-none bg-slate-900/80 border border-white/10 text-white py-2 px-3 rounded leading-tight focus:outline-none focus:border-orange-500/50 text-xs w-40"
                                    >
                                        <option value="p">Latency (Percentile)</option>
                                        <option value="avg">Average Latency</option>
                                        <option value="error">Error Rate</option>
                                    </select>

                                    {rule.type === 'p' && (
                                        <div className="flex items-center">
                                            <span className="text-xs text-gray-400 mr-1">P</span>
                                            <input 
                                                type="number" 
                                                value={rule.p_val} 
                                                onChange={e => updateRule(idx, 'p_val', e.target.value)}
                                                placeholder="95"
                                                className="bg-slate-900/80 border border-white/10 text-white py-2 px-1 rounded w-12 text-center text-xs focus:outline-none focus:border-orange-500/50"
                                            />
                                        </div>
                                    )}

                                    <span className="text-xs text-gray-400 mx-1">is greater than</span>

                                    <input 
                                        type="number" 
                                        value={rule.val} 
                                        onChange={e => updateRule(idx, 'val', e.target.value)}
                                        placeholder="Value"
                                        className="bg-slate-900/80 border border-white/10 text-white py-2 px-3 rounded w-20 text-center text-xs focus:outline-none focus:border-orange-500/50"
                                    />
                                    
                                    <span className="text-xs text-gray-500 w-8">{rule.type === 'error' ? '%' : 'ms'}</span>

                                    <button onClick={() => removeRule(idx)} className="text-gray-500 hover:text-red-400 p-1 ml-auto"><XMarkIcon className="w-4 h-4"/></button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
      </div>

      <div className="glass-card p-6 relative z-10">
          <div className="flex justify-between mb-4 items-center">
              <h3 className="text-sm font-bold text-white">Scenario Steps</h3>
              <button onClick={addStep} className="glass-btn text-xs flex items-center gap-1 bg-green-500/10 text-green-400 hover:bg-green-500/20"><PlusIcon className="w-3 h-3"/> Add Step</button>
          </div>
          <div className="space-y-3">
            {steps.map((step, idx) => (
                <div key={idx} className="flex gap-3 items-end bg-black/20 p-3 rounded-lg border border-white/5 animate-in slide-in-from-left-2">
                    <div className="text-xs text-gray-500 py-3 w-6 font-mono font-bold">#{idx + 1}</div>
                    
                    <Field className="flex-1"><Label className="text-[10px] text-gray-500 ml-1">Users</Label>
                        <Input type="number" value={step.users} onChange={e => updateStep(idx, 'users', e.target.value)} className="glass-input w-full h-10 text-center" />
                    </Field>
                    <Field className="flex-1"><Label className="text-[10px] text-gray-500 ml-1">Duration (s)</Label>
                        <Input type="number" value={step.duration} onChange={e => updateStep(idx, 'duration', e.target.value)} className="glass-input w-full h-10 text-center" />
                    </Field>
                    <Field className="flex-1"><Label className="text-[10px] text-gray-500 ml-1">Ramp (s)</Label>
                        <Input type="number" value={step.ramp} onChange={e => updateStep(idx, 'ramp', e.target.value)} className="glass-input w-full h-10 text-center" />
                    </Field>
                    <Field className="flex-1"><Label className="text-[10px] text-gray-500 ml-1">Think (s)</Label>
                        <Input type="number" step="0.1" value={step.think} onChange={e => updateStep(idx, 'think', e.target.value)} className="glass-input w-full h-10 text-center" />
                    </Field>
                      <Field className="flex-1"><Label className="text-[10px] text-blue-400 ml-1 font-bold">Jitter %</Label>
                        <Input type="number" value={step.jitter} onChange={e => updateStep(idx, 'jitter', e.target.value)} className="glass-input w-full h-10 text-center border-blue-500/30 text-blue-100" />
                    </Field>
                    
                    <button onClick={() => removeStep(idx)} className="glass-btn p-0 hover:bg-red-500/20 text-red-400 border-red-500/30 h-10 w-10 flex justify-center items-center rounded-lg"><XMarkIcon className="w-5 h-5"/></button>
                </div>
            ))}
          </div>
      </div>

      <div className="grid grid-cols-3 gap-6 relative z-0">
          <div className="glass-card p-4 col-span-2 h-64"><Line options={{ responsive: true, maintainAspectRatio: false, scales: { x: { display: false }, y: { grid: { color: 'rgba(255,255,255,0.05)' } } }, plugins: { legend: { display: false } } }} data={chartData} /></div>
          <div className="space-y-4">
              <div className="glass-card p-4 text-center"><div className="text-3xl font-bold text-blue-400">{stats.users}</div><div className="text-[10px] text-gray-500">USERS</div></div>
              <div className="glass-card p-4 text-center"><div className="text-3xl font-bold text-green-400">{parseFloat(stats.rps).toFixed(1)}</div><div className="text-[10px] text-gray-500">RPS</div></div>
              <div className="glass-card p-4 text-center"><div className="text-3xl font-bold text-red-400">{stats.failed}</div><div className="text-[10px] text-gray-500">FAIL</div></div>
          </div>
      </div>

      {finalResult && !isRunning && (
          <div className={`glass-card p-6 border animate-in zoom-in duration-300 ${
              finalResult.test_result.status === 'passed' ? 'border-green-500/30 bg-green-900/10' : 'border-red-500/50 bg-red-900/10'
          }`}>
              <div className="flex items-center gap-3 mb-4 border-b border-white/5 pb-4">
                  {finalResult.test_result.status === 'passed' ? (
                      <CheckBadgeIcon className="w-10 h-10 text-green-400" />
                  ) : (
                      <XCircleIcon className="w-10 h-10 text-red-500" />
                  )}
                  <div>
                      <h3 className={`text-xl font-bold ${
                          finalResult.test_result.status === 'passed' ? 'text-green-400' : 'text-red-400'
                      }`}>
                          {finalResult.test_result.status === 'passed' ? 'TEST PASSED' : 'TEST FAILED'}
                      </h3>
                      <p className="text-xs text-gray-400">
                          {finalResult.test_result.failures.length > 0 
                            ? `Reasons: ${finalResult.test_result.failures.join(', ')}` 
                            : 'All thresholds met successfully.'}
                      </p>
                  </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-black/20 p-3 rounded-lg"><div className="text-[10px] text-gray-500 uppercase">Avg Latency</div><div className="text-lg font-mono text-white">{finalResult.avg_response_time_ms.toFixed(1)} ms</div></div>
                  <div className="bg-black/20 p-3 rounded-lg"><div className="text-[10px] text-blue-400 font-bold uppercase">P95 Latency</div><div className="text-lg font-mono text-blue-100">{finalResult.p95_latency.toFixed(1)} ms</div></div>
                  <div className="bg-black/20 p-3 rounded-lg"><div className="text-[10px] text-purple-400 font-bold uppercase">P99 Latency</div><div className="text-lg font-mono text-purple-100">{finalResult.p99_latency.toFixed(1)} ms</div></div>
                  <div className="bg-black/20 p-3 rounded-lg"><div className="text-[10px] text-green-400 uppercase">Throughput</div><div className="text-lg font-mono text-green-100">{finalResult.throughput_rps.toFixed(1)} req/s</div></div>
              </div>
          </div>
      )}

      {!isRunning ? (
          <button onClick={startTest} className="glass-btn-primary w-full h-14 text-lg tracking-widest uppercase">⚡ Initiate Storm</button>
      ) : (
          <button onClick={() => window.pywebview.api.stop_load_test()} className="w-full h-14 bg-red-600/80 text-white rounded-lg">⛔ Abort</button>
      )}
    </div>
  );
};
export default LoadTest;