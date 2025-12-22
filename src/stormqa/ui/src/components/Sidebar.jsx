import React from 'react';
import { BoltIcon, GlobeAltIcon, CircleStackIcon, DocumentChartBarIcon, HomeIcon, HeartIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'; // <--- آیکون جدید اضافه شد

const Sidebar = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: HomeIcon },
    { id: 'load', label: 'Load Scenario', icon: BoltIcon },
    { id: 'network', label: 'Network Sim', icon: GlobeAltIcon },
    { id: 'websocket', label: 'WebSocket Test', icon: ChatBubbleLeftRightIcon }, // <--- آیتم جدید
    { id: 'db', label: 'Database', icon: CircleStackIcon },
    { id: 'report', label: 'AI Report', icon: DocumentChartBarIcon },
  ];
  const openLink = (url) => {
      if (window.pywebview) {
          window.pywebview.api.open_link(url);
      } else {
          window.open(url, '_blank');
      }
  };

  return (
    <aside className="w-64 glass-panel m-4 rounded-3xl flex flex-col p-6 z-[100] relative h-[calc(100vh-2rem)]">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-[0_0_15px_rgba(59,130,246,0.5)] flex items-center justify-center">
            <BoltIcon className="w-6 h-6 text-white" />
        </div>
        <div>
            <h1 className="text-xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400">StormQA</h1>
            <div className="text-[10px] text-blue-400 tracking-[0.2em] font-bold">ENTERPRISE</div>
        </div>
      </div>
      
      <nav className="space-y-2 flex-1">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group ${
              activeTab === item.id 
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-[0_0_10px_rgba(59,130,246,0.1)]' 
                : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
            }`}
          >
            <item.icon className={`w-5 h-5 ${activeTab === item.id ? 'animate-pulse' : ''}`} />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
      
      {/* Footer Section */}
      <div className="mt-4 space-y-4">
          <div className="flex justify-center">
            <button 
                onClick={() => openLink('https://pay.oxapay.com/14009511')}
                className="w-10/12 bg-gradient-to-r from-yellow-600/10 to-orange-600/10 hover:from-yellow-600/20 hover:to-orange-600/20 border border-yellow-500/20 text-yellow-500/80 text-xs font-bold py-2 rounded-lg flex items-center justify-center gap-2 transition-all hover:text-yellow-400 relative z-20 cursor-pointer"
            >
                <HeartIcon className="w-3 h-3" /> Support & Donate
            </button>
          </div>

          <div className="glass-card p-4 text-center border-t border-white/5 relative z-20">
              <div className="text-[10px] text-gray-500 mb-1 tracking-widest">VERSION 3</div>
              <div className="text-xs text-gray-400">Powered by <span className="text-white font-bold">Testeto</span></div>
              
              <div 
                onClick={() => openLink('https://pouyarezapour.ir')}
                className="text-xs text-blue-400 mt-1 cursor-pointer hover:text-blue-300 hover:underline transition-colors font-medium relative z-20 inline-block"
              >
                  Pouya Rezapour
              </div>
          </div>
      </div>
    </aside>
  );
};

export default Sidebar;