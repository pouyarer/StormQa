import { useState } from 'react';
import Sidebar from './components/Sidebar';
import LoadTest from './components/LoadTest';
import NetworkTest from './components/NetworkTest';
import DbTest from './components/DbTest';
import Dashboard from './components/Dashboard';
import WebSocketTest from './components/WebSocketTest'; 

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [reportLog, setReportLog] = useState("");

  const getReport = () => {
      if(window.pywebview) {
          window.pywebview.api.get_ai_analysis().then(res => setReportLog(res));
      } else {
          setReportLog("Demo: Analysis requires Python backend.\nRun 'stormqa open' to see real AI results.");
      }
  };

  const exportPdf = () => {
      if(window.pywebview) {
          window.pywebview.api.export_report_pdf().then(res => {
              if(res.status === 'success') alert("Saved: " + res.path);
              else alert("Error: " + res.message);
          });
      }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0f172a]">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 p-4 pl-0 relative">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none -z-10">
           <div className="absolute top-[-20%] left-[20%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px]"></div>
           <div className="absolute bottom-[-10%] right-[10%] w-[400px] h-[400px] bg-purple-600/10 rounded-full blur-[100px]"></div>
        </div>

        <div className="h-full glass-panel rounded-3xl p-8 relative overflow-y-auto custom-scrollbar">
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              {activeTab === 'dashboard' && <Dashboard />}
              {activeTab === 'load' && <LoadTest />}
              {activeTab === 'network' && <NetworkTest />}
              {activeTab === 'websocket' && <WebSocketTest />} 
              {activeTab === 'db' && <DbTest />}
              
              {activeTab === 'report' && (
                  <div className="space-y-6 max-w-4xl mx-auto">
                      <div className="flex justify-between items-center">
                          <h2 className="text-2xl font-bold text-white">AI Analysis Report</h2>
                          <div className="flex gap-4">
                              <button onClick={getReport} className="glass-btn hover:bg-white/10">🤖 Generate Insight</button>
                              <button onClick={exportPdf} className="glass-btn text-green-400 border-green-500/30 hover:bg-green-500/10">📄 Export PDF</button>
                          </div>
                      </div>
                      <div className="glass-card p-6 min-h-[400px] whitespace-pre-wrap font-mono text-sm text-gray-300 shadow-inner bg-black/20">
                          {reportLog || "No analysis generated yet. Run a Load or Network test first, then click 'Generate Insight'."}
                      </div>
                  </div>
              )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;