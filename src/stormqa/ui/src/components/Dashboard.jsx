import React, { useState, useEffect } from 'react';
import { ArrowPathIcon, TrashIcon } from '@heroicons/react/24/outline';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler, Legend);

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_tests: 0,
    total_requests_sent: 0,
    total_failures: 0,
    last_test_date: "Never"
  });
  
  const [history, setHistory] = useState([]);

  const fetchData = () => {
    if(window.pywebview) {
        window.pywebview.api.get_global_stats().then(res => setStats(res));
        window.pywebview.api.get_history_chart_data().then(res => setHistory(res || []));
    }
  };

  const resetData = () => {
    if(confirm("Are you sure? This will wipe all session data.")) {
        if(window.pywebview) {
            window.pywebview.api.reset_global_stats().then(res => {
                if(res.status === 'success') {
                    setStats(res.data);
                    setHistory([]); // تاریخچه در دیتابیس میمونه ولی از سشن پاک میشه
                }
            });
        }
    }
  };

  useEffect(() => { fetchData(); }, []);

  // آماده سازی داده های نمودار
  const chartData = {
      labels: history.map(h => h.timestamp.split(' ')[1]), // فقط ساعت
      datasets: [
          {
              label: 'Avg Latency (ms)',
              data: history.map(h => h.avg_latency),
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              fill: true,
              tension: 0.4
          },
          {
              label: 'P95 Latency (ms)',
              data: history.map(h => h.p95_latency),
              borderColor: '#8b5cf6', // بنفش
              backgroundColor: 'rgba(139, 92, 246, 0.0)',
              borderDash: [5, 5], // خط چین
              tension: 0.4
          }
      ]
  };

  const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
          legend: { labels: { color: 'white' } },
          tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: 'rgba(0,0,0,0.8)',
              titleColor: '#fff',
              bodyColor: '#ccc'
          }
      },
      scales: {
          y: {
              grid: { color: 'rgba(255,255,255,0.05)' },
              ticks: { color: '#9ca3af' }
          },
          x: {
              grid: { display: false },
              ticks: { color: '#9ca3af' }
          }
      }
  };

  return (
    <div className="space-y-8 animate-in fade-in zoom-in duration-500 pb-10">
        <div className="flex justify-between items-center">
            <div>
                <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Command Center</h1>
                <p className="text-gray-400 mt-2">System Overview & Performance Trends</p>
            </div>
            <div className="flex gap-3">
                <button onClick={fetchData} className="glass-btn p-3 rounded-full"><ArrowPathIcon className="w-5 h-5" /></button>
                <button onClick={resetData} className="glass-btn hover:bg-red-500/20 text-red-400 border-red-500/30 p-3 rounded-full"><TrashIcon className="w-5 h-5" /></button>
            </div>
        </div>

        {/* Big Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-card p-8 relative overflow-hidden group">
                <div className="absolute -right-6 -top-6 w-24 h-24 bg-blue-500/20 rounded-full blur-2xl group-hover:bg-blue-500/30 transition-all"></div>
                <h3 className="text-gray-400 text-sm font-medium uppercase tracking-widest">Total Runs</h3>
                <div className="text-5xl font-bold text-white mt-4">{stats.total_tests}</div>
            </div>

            <div className="glass-card p-8 relative overflow-hidden group">
                <div className="absolute -right-6 -top-6 w-24 h-24 bg-purple-500/20 rounded-full blur-2xl group-hover:bg-purple-500/30 transition-all"></div>
                <h3 className="text-gray-400 text-sm font-medium uppercase tracking-widest">Requests Sent</h3>
                <div className="text-5xl font-bold text-white mt-4">
                    {stats.total_requests_sent > 1000 ? (stats.total_requests_sent/1000).toFixed(1) + 'k' : stats.total_requests_sent}
                </div>
            </div>

            <div className="glass-card p-8 relative overflow-hidden group">
                 <div className="absolute -right-6 -top-6 w-24 h-24 bg-red-500/10 rounded-full blur-2xl group-hover:bg-red-500/20 transition-all"></div>
                <h3 className="text-gray-400 text-sm font-medium uppercase tracking-widest">Health Score</h3>
                <div className="text-5xl font-bold text-white mt-4">
                    {stats.total_requests_sent > 0 
                        ? (100 - (stats.total_failures / stats.total_requests_sent * 100)).toFixed(1) 
                        : 100}%
                </div>
            </div>
        </div>

        {/* --- Trend Chart Section (New) --- */}
        <div className="glass-panel p-6">
            <h3 className="text-lg font-bold text-white mb-4">Performance Trend (Last 50 Runs)</h3>
            <div className="h-80 w-full">
                {history.length > 0 ? (
                    <Line data={chartData} options={chartOptions} />
                ) : (
                    <div className="h-full flex items-center justify-center text-gray-500 italic">
                        No test history available. Run a load test to see trends.
                    </div>
                )}
            </div>
        </div>

        {/* Recent Activity Table */}
        <div className="glass-panel p-0 overflow-hidden rounded-xl border border-white/5">
             <table className="w-full text-left text-sm text-gray-400">
                 <thead className="bg-black/20 text-xs uppercase font-medium text-gray-500">
                     <tr>
                         <th className="px-6 py-3">Time</th>
                         <th className="px-6 py-3">Target</th>
                         <th className="px-6 py-3">Avg Latency</th>
                         <th className="px-6 py-3">Status</th>
                     </tr>
                 </thead>
                 <tbody className="divide-y divide-white/5">
                     {history.slice(0, 5).map((h, i) => ( // نمایش 5 تای آخر
                         <tr key={i} className="hover:bg-white/5 transition-colors">
                             <td className="px-6 py-3 font-mono">{h.timestamp}</td>
                             <td className="px-6 py-3 text-white">{h.target_url}</td>
                             <td className="px-6 py-3">{h.avg_latency.toFixed(1)} ms</td>
                             <td className="px-6 py-3">
                                 <span className={`px-2 py-1 rounded text-[10px] font-bold ${
                                     h.status === 'PASSED' ? 'bg-green-500/10 text-green-400' : 
                                     h.status === 'FAILED' ? 'bg-red-500/10 text-red-400' : 'bg-gray-500/10 text-gray-400'
                                 }`}>
                                     {h.status}
                                 </span>
                             </td>
                         </tr>
                     ))}
                 </tbody>
             </table>
             {history.length === 0 && <div className="p-4 text-center text-xs">No records found.</div>}
        </div>
    </div>
  )
}
export default Dashboard;