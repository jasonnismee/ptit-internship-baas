"use client";
import React, { useState, useEffect, createContext, useContext, useRef } from "react";
import axios from "axios";
import { Activity, Server, Box, RefreshCw, Zap, Plus, Monitor, Terminal, AlertTriangle, Layers, Cpu, Database, Truck, Factory, ShieldAlert, CheckCircle2, Package, ArrowRight, Shield } from "lucide-react";
import dynamic from 'next/dynamic';

const ForceGraph = dynamic(() => import('react-force-graph-2d'), { ssr: false });
const API_BASE = "http://localhost:8000/api/v1";

// ==========================================
// 1. GLOBAL STATE (CONTEXT API)
// ==========================================
const AppContext = createContext<any>(null);

function AppProvider({ children }: { children: React.ReactNode }) {
  // App Layer State (Real K8s Data)
  const [inventory, setInventory] = useState({ farm: 50000, factory: 0, transport: 0, warehouse: 0 });
  const [transactions, setTransactions] = useState<any[]>([]);
  const [activeNodesCount, setActiveNodesCount] = useState(0);
  const [totalNodesCount, setTotalNodesCount] = useState(0);
  const [minConsensus, setMinConsensus] = useState(4);
  const [isProcessingTx, setIsProcessingTx] = useState(false);
  const [hackAlert, setHackAlert] = useState(false);
  const [txLight, setTxLight] = useState<string | null>(null); // Để trigger animation flow
  const [isInfraLoading, setIsInfraLoading] = useState(false);

  // Infra Layer State (Real K8s Data + Mock Extensions)
  const [activeTab, setActiveTab] = useState<'app' | 'infra'>('app');
  const [nodes, setNodes] = useState<any[]>([]);
  const [topology, setTopology] = useState({ nodes: [], links: [] });
  const [metrics, setMetrics] = useState({ blockHeight: 12050, peers: 0, tps: 0 });
  const [logs, setLogs] = useState<string[]>([]);
  const [infraAlerts, setInfraAlerts] = useState<any[]>([]);

  // Fetch Real Data from Backend
  const fetchData = async () => {
    try {
      const [nds, topo, mets, lg, vinamilk] = await Promise.all([
        axios.get(`${API_BASE}/nodes?namespace=default`),
        axios.get(`${API_BASE}/network/topology?namespace=default`),
        axios.get(`${API_BASE}/network/metrics?namespace=default`),
        axios.get(`${API_BASE}/network/logs?namespace=default`),
        axios.get(`${API_BASE}/vinamilk/state?namespace=default`)
      ]);
      setNodes(nds.data);
      setTopology(topo.data);
      setInventory(vinamilk.data.inventory);
      setTransactions(vinamilk.data.transactions);
      setActiveNodesCount(vinamilk.data.active_nodes);
      setTotalNodesCount(vinamilk.data.total_nodes);
      setMinConsensus(vinamilk.data.min_consensus);
      
      setMetrics(prev => {
        const newBlockHeight = mets.data.blockHeight > prev.blockHeight 
          ? mets.data.blockHeight 
          : prev.blockHeight + Math.floor(Math.random() * 2); 
          
        return {
          blockHeight: newBlockHeight,
          peers: mets.data.peers,
          tps: isProcessingTx ? Math.floor(Math.random() * 50) + 100 : mets.data.tps
        };
      });
      
      setLogs(prev => {
        const injectedMocks = prev.filter(l => l.startsWith("INFO [") || l.startsWith("WARN ["));
        return [...lg.data.logs, ...injectedMocks].slice(-50);
      });
    } catch (e) {
      console.error("Backend offline, using fallback data.");
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [isProcessingTx]);

  // Actions
  const addTransaction = async (station: string, amount: number) => {
    setIsProcessingTx(true);
    setTxLight(station);
    try {
      const res = await axios.post(`${API_BASE}/vinamilk/transaction`, { station, amount });
      const newTx = res.data.tx;
      await fetchData();
      
      // Inject realtime logs
      setTimeout(() => {
        setLogs(prev => [...prev, `INFO [${new Date().toLocaleTimeString()}] Received new transaction hash=${newTx.txHash} from App`].slice(-50));
      }, 1000);
      
      setTimeout(() => {
        if (newTx.status === 'CONFIRMED') {
          setLogs(prev => [...prev, `INFO [${new Date().toLocaleTimeString()}] Mined new block #${metrics.blockHeight + 1}.`].slice(-50));
        } else {
          setLogs(prev => [...prev, `WARN [${new Date().toLocaleTimeString()}] Transaction pending consensus. Waiting for nodes to recover...`].slice(-50));
        }
      }, 3000);

    } catch (e) {
      console.error(e);
    }
    setTimeout(() => {
      setIsProcessingTx(false);
      setTxLight(null);
    }, 1000);
  };

  const simulateHack = () => {
    setHackAlert(true);
    const newAlert = {
      id: Math.random().toString(),
      time: new Date().toLocaleTimeString(),
      level: 'CRITICAL',
      message: '[CRITICAL] Data mismatch detected. Tamper attempt rejected by consensus network.'
    };
    setInfraAlerts(prev => [newAlert, ...prev]);
    setLogs(prev => [...prev, `[SECURITY] Rejecting invalid state transition from external source.`]);
    
    setTimeout(() => {
      setHackAlert(false);
    }, 3000);
  };

  const createNetwork = async () => {
    setIsInfraLoading(true);
    try {
      await axios.post(`${API_BASE}/network/create`, { name: "default", replicas: 3, chain_id: 12345 });
      fetchData();
    } catch (e) {}
    setIsInfraLoading(false);
  };

  const scaleNetwork = async (newReplicas: number) => {
    if (nodes.length === 0) return;
    if (newReplicas < 1) newReplicas = 1;
    
    try {
      await axios.post(`${API_BASE}/network/scale`, { name: "default", replicas: newReplicas });
      setInfraAlerts(prev => [{
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        message: `Đang gửi lệnh thiết lập mạng lưới thành ${newReplicas} nodes cho K8s...`
      }, ...prev].slice(0, 5));
    } catch (e) {
      console.error(e);
    }
  };

  const cleanupNetwork = async () => {
    setIsInfraLoading(true);
    try {
      await axios.post(`${API_BASE}/network/cleanup?namespace=default`);
      setNodes([]);
      setTopology({ nodes: [], links: [] });
      setMetrics({ blockHeight: 0, peers: 0, tps: 0 });
      setLogs([]);
    } catch (e) {}
    setIsInfraLoading(false);
  };

  const crashRandomNode = async () => {
    try {
      const res = await axios.post(`${API_BASE}/demo/crash?namespace=default`);
      const msg = res.data.message; 
      
      let backupMsg = "";
      if (activeNodesCount > minConsensus) {
        backupMsg = ` [DỰ PHÒNG] Mạng vẫn còn ${activeNodesCount - 1} Nodes (>= ${minConsensus}). Hệ thống tiếp tục duy trì đồng thuận bình thường.`;
      } else {
        backupMsg = ` [CẢNH BÁO] Mạng chỉ còn ${activeNodesCount - 1} Nodes (< ${minConsensus}). Hệ thống sẽ tạm dừng đồng thuận cho đến khi Node được K8s tự động hồi phục!`;
      }

      setInfraAlerts(prev => [{
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        message: msg + backupMsg
      }, ...prev].slice(0, 5));
      
      await fetchData(); 
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <AppContext.Provider value={{
      activeTab, setActiveTab,
      inventory, transactions, isProcessingTx, hackAlert, txLight, addTransaction, simulateHack,
      nodes, topology, metrics, logs, infraAlerts, isInfraLoading, createNetwork, scaleNetwork, cleanupNetwork, crashRandomNode,
      activeNodesCount, totalNodesCount, minConsensus
    }}>
      {children}
    </AppContext.Provider>
  );
}

// ==========================================
// 2. APP LAYER (VINAMILK - LIGHT THEME)
// ==========================================
function VinamilkAppLayer() {
  const { inventory, transactions, addTransaction, isProcessingTx, hackAlert, simulateHack, txLight, nodes, activeNodesCount, totalNodesCount, minConsensus } = useContext(AppContext);
  const [amount, setAmount] = useState(500);
  const [station, setStation] = useState('farm');
  const [hackQuery, setHackQuery] = useState("UPDATE db_kho SET so_luong = 48000 WHERE id = 3");

  const stations = [
    { id: 'farm', name: 'Trang trại', icon: <Database />, inv: inventory.farm },
    { id: 'factory', name: 'Nhà máy', icon: <Factory />, inv: inventory.factory },
    { id: 'transport', name: 'Vận chuyển', icon: <Truck />, inv: inventory.transport },
    { id: 'warehouse', name: 'Kho tổng', icon: <Package />, inv: inventory.warehouse },
  ];

  if (totalNodesCount === 0) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6 transition-colors duration-500">
        <div className="bg-slate-800 border border-slate-700 p-8 rounded-xl max-w-lg text-center shadow-2xl">
          <ShieldAlert className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Hệ thống bị khóa (Zero-State Lock)</h2>
          <p className="text-slate-400">Hệ thống chưa được cấp phát hạ tầng Blockchain K8s. Vui lòng chuyển sang Tab BaaS và Khởi tạo mạng lưới trước khi sử dụng ứng dụng.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 p-6 font-sans transition-colors duration-500">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-slate-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-xl">V</div>
            <div>
              <h1 className="text-xl font-bold text-blue-900">Vinamilk SCM</h1>
              <p className="text-xs text-slate-500 uppercase tracking-wider">Supply Chain Management</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {/* Node Health Mini-Widget */}
            <div className="flex items-center space-x-1 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200" title="Consensus Nodes Status">
              <Shield className="w-4 h-4 text-slate-500 mr-2" />
              {[...Array(totalNodesCount)].map((_, i) => (
                <div key={i} className={`w-2.5 h-2.5 rounded-full ${i < activeNodesCount ? 'bg-green-500' : 'bg-red-500'} ${isProcessingTx && i < activeNodesCount ? 'animate-pulse' : ''}`}></div>
              ))}
            </div>
          </div>
        </div>

        {/* Supply Chain Flowchart */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-bold text-slate-700 mb-6 flex items-center"><Activity className="w-5 h-5 mr-2 text-blue-500"/> Luồng vận chuyển thực tế</h2>
          <div className="flex justify-between items-center relative px-8">
            {/* Connection Lines */}
            <div className="absolute left-16 right-16 top-8 h-1 bg-slate-100 z-0"></div>
            {stations.map((s, i) => (
              <div key={s.id} className="relative z-10 flex flex-col items-center">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center border-4 ${txLight === s.id ? 'border-green-400 bg-green-50 shadow-[0_0_15px_rgba(74,222,128,0.5)]' : 'border-white bg-blue-50 text-blue-600'} transition-all duration-300`}>
                  {s.icon}
                </div>
                <div className="mt-3 font-bold text-slate-700">{s.name}</div>
                <div className="text-sm text-slate-500 font-mono bg-slate-100 px-2 py-1 rounded mt-1">{s.inv.toLocaleString()} Lít</div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Action Form */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 className="text-lg font-bold text-slate-700 mb-4">Ghi nhận Giao dịch</h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-600">Trạm xuất phát</label>
                <select value={station} onChange={e=>setStation(e.target.value)} className="w-full mt-1 border border-slate-300 rounded-lg px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500">
                  <option value="farm">Trang trại ➔ Nhà máy</option>
                  <option value="factory">Nhà máy ➔ Vận chuyển</option>
                  <option value="transport">Vận chuyển ➔ Kho tổng</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-600">Số lượng (Lít)</label>
                <input type="number" value={amount} onChange={e=>setAmount(Number(e.target.value))} className="w-full mt-1 border border-slate-300 rounded-lg px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500" />
              </div>
              <button 
                onClick={() => addTransaction(station, amount)} 
                disabled={isProcessingTx}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2.5 rounded-lg transition-colors disabled:opacity-50 flex justify-center items-center"
              >
                {isProcessingTx ? (
                  <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Đang đồng thuận (4 Nodes)...</>
                ) : "Ghi nhận lên Blockchain"}
              </button>
            </div>
          </div>

          {/* Ledger */}
          <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h2 className="text-lg font-bold text-slate-700 mb-4 flex items-center"><Database className="w-5 h-5 mr-2 text-green-500"/> Sổ cái Bất biến (Ledger)</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-slate-500 uppercase text-xs">
                  <tr>
                    <th className="px-4 py-2 rounded-l-lg">Thời gian</th>
                    <th className="px-4 py-2">Hành động</th>
                    <th className="px-4 py-2">Số lượng</th>
                    <th className="px-4 py-2">TxHash</th>
                    <th className="px-4 py-2 rounded-r-lg">Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.length === 0 && <tr><td colSpan={5} className="text-center py-4 text-slate-400">Chưa có giao dịch nào</td></tr>}
                  {transactions.map(tx => (
                    <tr key={tx.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono text-xs">{tx.time}</td>
                      <td className="px-4 py-3 font-medium text-slate-700">{tx.station.toUpperCase()}</td>
                      <td className="px-4 py-3 font-mono text-blue-600">+{tx.amount.toLocaleString()}</td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500 bg-slate-100 rounded px-2">{tx.txHash}</td>
                      <td className={`px-4 py-3 flex items-center text-xs font-bold ${tx.status === 'CONFIRMED' ? 'text-green-600' : 'text-orange-500'}`}>
                        {tx.status === 'CONFIRMED' ? <CheckCircle2 className="w-4 h-4 mr-1" /> : <RefreshCw className="w-4 h-4 mr-1 animate-spin" />}
                        {tx.status === 'CONFIRMED' ? 'Confirmed' : `Chờ đồng thuận (${tx.confirmations}/${minConsensus} Nodes)`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Hacker Console */}
        <div className={`mt-6 border-2 rounded-xl overflow-hidden transition-all duration-300 ${hackAlert ? 'border-red-500 shadow-[0_0_30px_rgba(239,68,68,0.4)]' : 'border-slate-800'}`}>
          <div className="bg-slate-900 px-4 py-2 flex items-center justify-between">
            <h3 className="text-red-400 font-mono text-sm font-bold flex items-center">
              <Terminal className="w-4 h-4 mr-2" /> Kẻ gian tấn công Database (Mô phỏng Hack)
            </h3>
          </div>
          <div className="bg-black p-4 space-y-4">
            <div className="text-slate-400 font-mono text-xs mb-2">
              -- Cố tình sửa đổi dữ liệu tồn kho ngoài Blockchain
            </div>
            <div className="flex space-x-2">
              <span className="text-green-500 font-mono mt-2">root@db:~#</span>
              <input 
                type="text" 
                value={hackQuery}
                onChange={e=>setHackQuery(e.target.value)}
                className="flex-1 bg-transparent border-none text-slate-300 font-mono outline-none"
              />
            </div>
            <button 
              onClick={simulateHack}
              className="bg-red-900/50 hover:bg-red-800 text-red-200 border border-red-700 px-4 py-1.5 rounded font-mono text-sm transition-colors"
            >
              Thực thi Lệnh
            </button>

            {hackAlert && (
              <div className="mt-4 p-3 bg-red-500/20 border border-red-500 rounded text-red-400 font-mono text-sm animate-pulse flex items-start">
                <ShieldAlert className="w-5 h-5 mr-3 shrink-0" />
                <div>
                  <div className="font-bold">CẢNH BÁO XÂM PHẠM TOÀN VẸN DỮ LIỆU!</div>
                  <div className="text-xs mt-1 text-red-300">Dòng dữ liệu bị từ chối bởi cơ chế đồng thuận của 4 Nodes Blockchain. Đã khôi phục trạng thái gốc. Kích hoạt báo động hạ tầng!</div>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

// ==========================================
// 3. INFRA LAYER (BAAS - DARK THEME)
// ==========================================
function BaaSInfraLayer() {
  const { topology, metrics, logs, infraAlerts, hackAlert, nodes, isInfraLoading, createNetwork, scaleNetwork, cleanupNetwork, crashRandomNode, activeNodesCount, totalNodesCount } = useContext(AppContext);
  const [targetNodes, setTargetNodes] = useState(3);

  // Sync state if it's the first time and nodes exist
  useEffect(() => {
    if (nodes.length > 0 && targetNodes === 3) {
      setTargetNodes(nodes.length);
    }
  }, [nodes.length]);

  return (
    <div className={`min-h-screen bg-[#0a0f18] text-slate-300 p-6 font-sans transition-colors duration-500 ${hackAlert ? 'animate-[pulse_1s_ease-in-out_3]' : ''}`}>
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 pb-4">
          <div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400 uppercase tracking-widest flex items-center">
              <Server className="w-6 h-6 mr-3 text-emerald-400" /> BaaS Orchestrator
            </h1>
            <p className="text-slate-500 text-xs font-mono mt-1">:: INFRASTRUCTURE COMMAND CENTER ::</p>
          </div>
          <div className="flex items-center space-x-4">
            <button onClick={cleanupNetwork} disabled={isInfraLoading} className="text-xs font-mono text-red-400 border border-red-500/30 bg-red-500/10 px-3 py-1.5 rounded hover:bg-red-500/20 transition-colors disabled:opacity-50 flex items-center">
              {isInfraLoading ? <RefreshCw className="w-3 h-3 mr-1 animate-spin" /> : <RefreshCw className="w-3 h-3 mr-1" />} RESET / CLEANUP
            </button>
            <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400 border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 rounded">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
              <span>SYS_ONLINE_SECURE</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          
          {/* Topology & Monitoring */}
          <div className="xl:col-span-8 flex flex-col space-y-6">
            
            {/* Metrics Board */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-black/30 border border-white/5 p-4 rounded-xl flex flex-col items-center justify-center">
                <Activity className="text-cyan-400 w-6 h-6 mb-2" />
                <div className="text-3xl font-mono text-white">{metrics.tps}</div>
                <div className="text-xs text-slate-500 uppercase mt-1">Live TPS</div>
              </div>
              <div className="bg-black/30 border border-white/5 p-4 rounded-xl flex flex-col items-center justify-center">
                <Server className="text-purple-400 w-6 h-6 mb-2" />
                <div className="text-3xl font-mono text-white">{Math.max(activeNodesCount - 1, 0)}/{Math.max(totalNodesCount - 1, 0)}</div>
                <div className="text-xs text-slate-500 uppercase mt-1">Peers Connected</div>
              </div>
            </div>

            {/* Topology Graph */}
            <div className={`bg-black/30 border rounded-xl backdrop-blur-md flex-1 min-h-[350px] overflow-hidden relative transition-colors duration-300 ${hackAlert ? 'border-red-500/50' : 'border-white/5'}`}>
              <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between">
                <div className="flex items-center text-sm uppercase tracking-wider font-bold text-emerald-400 bg-black/50 px-3 py-1 rounded border border-white/10">
                  <Activity className="w-4 h-4 mr-2" /> Network Topology
                </div>
                {nodes.length > 0 && (
                  <div className="flex items-center space-x-2 bg-black/50 p-1 rounded-lg border border-white/10">
                    <button
                      onClick={crashRandomNode}
                      disabled={nodes.length <= 1}
                      className="px-3 py-1.5 bg-yellow-500/10 text-yellow-500 border border-yellow-500/30 rounded hover:bg-yellow-500/20 text-sm font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Mô phỏng sập ngẫu nhiên 1 Node"
                    >
                      💥 Kill Node
                    </button>
                    <div className="w-px h-6 bg-white/20 mx-2"></div>
                    <span className="text-sm text-slate-400">Nodes:</span>
                    <input 
                      type="number" 
                      value={targetNodes} 
                      onChange={(e) => setTargetNodes(Number(e.target.value))}
                      className="w-16 bg-black/50 border border-white/20 rounded px-2 py-1 text-white text-sm outline-none text-center"
                      min="1"
                    />
                    <button
                      onClick={() => scaleNetwork(targetNodes)}
                      className="px-3 py-1.5 bg-indigo-500/20 text-indigo-400 rounded hover:bg-indigo-500/40 text-sm font-medium transition-all border border-indigo-500/30"
                    >
                      Lưu / Scale
                    </button>
                  </div>
                )}
              </div>
              
              {nodes.length === 0 ? (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-600 font-mono absolute inset-0">
                  <div className="mb-4">No active nodes in K8s Cluster.</div>
                  <button 
                    onClick={createNetwork} 
                    disabled={isInfraLoading}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-6 rounded-lg transition-colors flex items-center shadow-[0_0_15px_rgba(16,185,129,0.5)] disabled:opacity-50"
                  >
                    {isInfraLoading ? <RefreshCw className="w-5 h-5 mr-2 animate-spin" /> : <Server className="w-5 h-5 mr-2" />}
                    Khởi tạo Cụm Blockchain (3 Nodes)
                  </button>
                </div>
              ) : topology.nodes.length > 0 ? (
                <ForceGraph
                  graphData={topology}
                  nodeAutoColorBy="status"
                  nodeRelSize={8}
                  linkDirectionalParticles={4}
                  linkDirectionalParticleSpeed={0.015}
                  linkColor={() => hackAlert ? 'rgba(239, 68, 68, 0.4)' : 'rgba(52, 211, 153, 0.4)'}
                  nodeCanvasObject={(node: any, ctx: any, globalScale: any) => {
                    const label = node.id;
                    const fontSize = 12/globalScale;
                    ctx.font = `${fontSize}px Sans-Serif`;
                    ctx.beginPath();
                    ctx.arc(node.x, node.y, 6, 0, 2 * Math.PI, false);
                    
                    // Highlight node 3 if hack alert
                    if (hackAlert && node.id === 'node-3') {
                      ctx.fillStyle = '#ef4444';
                    } else {
                      ctx.fillStyle = node.status === 'Running' ? '#10b981' : '#f59e0b';
                    }
                    ctx.fill();
                    
                    // Draw glow
                    ctx.shadowColor = ctx.fillStyle;
                    ctx.shadowBlur = hackAlert ? 20 : 10;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#cbd5e1';
                    ctx.fillText(label, node.x, node.y + 12);
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-600 font-mono absolute inset-0">
                  <RefreshCw className="w-6 h-6 animate-spin mr-2" /> Đang đồng bộ Topology...
                </div>
              )}
            </div>
            
            {/* Node Resource Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {nodes.map((node, i) => (
                <div key={i} className={`bg-black/30 border rounded-xl p-5 text-sm font-mono transition-colors duration-300 ${hackAlert && i === 3 ? 'border-red-500/50 bg-red-500/5' : 'border-white/5'}`}>
                  <div className="text-slate-400 mb-4 flex justify-between text-base font-bold">
                    <span>Node-{i}</span>
                    <span className={hackAlert && i === 3 ? 'text-red-400' : (node.status === 'Running' ? 'text-emerald-400' : 'text-yellow-400')}>
                      {node.status === 'Running' ? 'OK' : 'WAIT'}
                    </span>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-xs text-slate-500 mb-1"><span>CPU</span><span>{hackAlert && i === 3 ? '98%' : Math.floor(Math.random() * 20 + 10) + '%'}</span></div>
                      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <div className={`h-full ${hackAlert && i === 3 ? 'bg-red-500 w-[98%]' : 'bg-cyan-500 w-[20%]'}`}></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-xs text-slate-500 mb-1"><span>RAM</span><span>{hackAlert && i === 3 ? '85%' : Math.floor(Math.random() * 10 + 40) + '%'}</span></div>
                      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <div className={`h-full ${hackAlert && i === 3 ? 'bg-orange-500 w-[85%]' : 'bg-purple-500 w-[45%]'}`}></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

          </div>

          {/* Terminal & Alerts */}
          <div className="xl:col-span-4 flex flex-col space-y-6">
            
            {/* Alert System */}
            <div className={`border p-4 rounded-xl backdrop-blur-md flex-1 max-h-[300px] overflow-y-auto transition-colors duration-300 ${hackAlert ? 'bg-red-900/10 border-red-500/50' : 'bg-black/30 border-white/5'}`}>
              <h2 className={`flex items-center text-sm uppercase tracking-wider font-bold mb-4 sticky top-0 py-1 ${hackAlert ? 'text-red-400 bg-red-900/10' : 'text-orange-400 bg-[#0a0f18]/90'}`}>
                <ShieldAlert className="w-4 h-4 mr-2" /> SOC Alerts
              </h2>
              <div className="space-y-3">
                {infraAlerts.length === 0 && <div className="text-xs font-mono text-emerald-500/50">No threats detected.</div>}
                {infraAlerts.map(alert => (
                  <div key={alert.id} className="bg-red-500/10 border-l-2 border-red-500 p-2 text-xs font-mono text-red-200">
                    <span className="text-slate-500">[{alert.time}]</span> {alert.message}
                  </div>
                ))}
              </div>
            </div>

            {/* Virtual Terminal */}
            <div className="bg-[#050505] border border-white/10 p-4 rounded-xl flex-1 flex flex-col h-[200px]">
              <h2 className="flex items-center text-xs uppercase tracking-wider font-bold text-slate-500 mb-3">
                <Terminal className="w-4 h-4 mr-2" /> K8s Pod Logs (Real-time)
              </h2>
              <div className="font-mono text-[10px] sm:text-xs text-emerald-500/80 overflow-y-auto space-y-1 h-full flex flex-col-reverse scrollbar-thin scrollbar-thumb-white/10">
                {[...logs].reverse().map((log, i) => (
                  <div key={i} className="break-all hover:bg-white/5 px-1 rounded">{log}</div>
                ))}
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// 4. MAIN LAYOUT & TAB SWITCHER
// ==========================================
export default function Page() {
  return (
    <AppProvider>
      <MainLayout />
    </AppProvider>
  );
}

function MainLayout() {
  const { activeTab, setActiveTab } = useContext(AppContext);

  return (
    <div className="relative min-h-screen">
      {/* Floating Tab Switcher */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 bg-slate-900/80 backdrop-blur-xl p-1.5 rounded-full border border-white/10 shadow-2xl flex space-x-1">
        <button 
          onClick={() => setActiveTab('app')}
          className={`px-6 py-2.5 rounded-full text-sm font-bold flex items-center transition-all ${activeTab === 'app' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
        >
          <Database className="w-4 h-4 mr-2" /> Vinamilk App
        </button>
        <button 
          onClick={() => setActiveTab('infra')}
          className={`px-6 py-2.5 rounded-full text-sm font-bold flex items-center transition-all ${activeTab === 'infra' ? 'bg-emerald-600 text-white shadow-lg' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
        >
          <Server className="w-4 h-4 mr-2" /> BaaS Infra
        </button>
      </div>

      {/* Render Active Tab */}
      <div className="pb-24">
        {activeTab === 'app' ? <VinamilkAppLayer /> : <BaaSInfraLayer />}
      </div>
    </div>
  );
}
