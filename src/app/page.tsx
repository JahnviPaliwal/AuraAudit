"use client";

import React, { useState, useEffect } from "react";
import { 
  Scale, AlertTriangle, CheckCircle, RefreshCw, Download, 
  ArrowRightLeft, FileSpreadsheet, Send, Settings, BookOpen, Clock, AlertCircle,
  TrendingUp, Percent, ShieldCheck, DollarSign, Users, Briefcase, Info,
  Upload, FileText, ArrowLeft, Home as HomeIcon, MessageSquare, ChevronDown, Eye, EyeOff,
  Activity, ShieldAlert, LineChart, FileCode
} from "lucide-react";

interface ExceptionItem {
  type: string;
  tx_id: string;
  date: string;
  amount: number;
  details: string;
  proposed_adjustment: string;
  confidence?: number;
  why_unresolved?: string;
}

interface AuditedRow {
  tx_id: string;
  date: string;
  description: string;
  amount: number;
  messy_category: string;
  audited_category: string;
  flags: string[];
  receipt_uploaded: boolean;
  confidence?: number;
  reasoning?: string;
}

interface ForecastData {
  months: string[];
  baseline: number[];
  p10: number[];
  p50: number[];
  p90: number[];
  runway_months: number;
  starting_cash: number;
  monthly_burn: number;
}

interface ChatMessage {
  sender: "user" | "bot";
  text: string;
}

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [currentView, setCurrentView] = useState<"home" | "generator" | "analyzer">("home");
  
  // Generator view states
  const [downloading, setDownloading] = useState(false);
  const [hasDownloaded, setHasDownloaded] = useState(false);

  // Analyzer view states
  const [hasUploaded, setHasUploaded] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Floating widgets toggle states
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isGstOpen, setIsGstOpen] = useState(false);
  const [showTable, setShowTable] = useState(true);

  // Chart interactivity states
  const [activeMonthIdx, setActiveMonthIdx] = useState(2); // Default to Nov 2026 (index 2)

  // Sub-tabs in strategy playground
  const [playgroundTab, setPlaygroundTab] = useState<"hiring" | "marketing" | "capital">("hiring");

  // Core dashboard states
  const [activeTab, setActiveTab] = useState<"metrics" | "resolved" | "exceptions" | "extended">("metrics");
  const [extendedTab, setExtendedTab] = useState<"forecast" | "msme_priority">("forecast");
  
  const [runId, setRunId] = useState<string | null>(null);
  const [evalReport, setEvalReport] = useState<any | null>(null);
  const [pastRuns, setPastRuns] = useState<any[]>([]);
  const [rbiRate, setRbiRate] = useState<number>(6.75);

  const [auditData, setAuditData] = useState<{ exceptions: ExceptionItem[]; audited_transactions: AuditedRow[] }>({
    exceptions: [],
    audited_transactions: []
  });
  
  const [forecast, setForecast] = useState<ForecastData>({
    months: [], baseline: [], p10: [], p50: [], p90: [], runway_months: 6, starting_cash: 1845000.00, monthly_burn: 810000.00
  });

  // Scenario control states
  // 1. Hiring
  const [newHiresCount, setNewHiresCount] = useState(5);
  const [newHiresSalary, setNewHiresSalary] = useState(150000);
  const [newHiresStartMonth, setNewHiresStartMonth] = useState(1); 
  
  // 2. Client Payment Delay
  const [paymentDelayDays, setPaymentDelayDays] = useState(45);

  // 3. Marketing Campaign
  const [adSpend, setAdSpend] = useState(0);
  const [cac, setCac] = useState(1000);

  // 4. Office Upgrade
  const [officeUpgrade, setOfficeUpgrade] = useState(false);

  // 5. Product Pricing Hike
  const [priceHike, setPriceHike] = useState(0);

  // 6. Funding Round
  const [fundingRound, setFundingRound] = useState(0);
  const [fundingMonth, setFundingMonth] = useState(2); 

  const [approvedAdjustments, setApprovedAdjustments] = useState<Record<number, boolean>>({});
  const [exportFormat, setExportFormat] = useState<"csv" | "quickbooks" | "xero">("csv");
  
  // MSME Allocator States
  const [apInvoices, setApInvoices] = useState([
    { id: 1, vendor: "Beta Packaging Systems", type: "MSME Micro", amount: 250000, daysLeft: 5, category: "Raw Materials COGS" },
    { id: 2, vendor: "Sharma Realty (Rent)", type: "Large Corp", amount: 75000, daysLeft: 20, category: "Rent OpEx" },
    { id: 3, vendor: "TechConsulting Experts", type: "MSME Small", amount: 120000, daysLeft: 12, category: "Professional Fees OpEx" },
    { id: 4, vendor: "AWS Server Hosting", type: "Foreign Corp", amount: 180000, daysLeft: 35, category: "Server Hosting COGS" },
    { id: 5, vendor: "Alpha Marketing Agency", type: "MSME Small", amount: 100000, daysLeft: 42, category: "Marketing OpEx" }
  ]);
  const [selectedInvoices, setSelectedInvoices] = useState<Record<number, boolean>>({
    1: true,
    3: true
  });
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { sender: "bot", text: "Namaste! I am your AuraAudit Co-pilot. Ask me anything about the current reconciliation run's exceptions or details (e.g. 'Why was TX-TDS-SPLIT-A flagged?')." }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [sendingChat, setSendingChat] = useState(false);
  
  // Settings / API Key state
  const [showSettings, setShowSettings] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [apiProvider, setApiProvider] = useState<"openai" | "gemini" | "groq">("openai");

  // Search filter
  const [searchQuery, setSearchQuery] = useState("");

  const fetchForecast = async () => {
    try {
      const res = await fetch("/api/forecast");
      const json = await res.json();
      setForecast(json);
    } catch (e) {
      console.error("Failed fetching forecast data", e);
    }
  };

  const fetchPastRuns = async () => {
    try {
      const res = await fetch("/api/runs");
      const json = await res.json();
      setPastRuns(json.runs || []);
    } catch (e) {
      console.error("Failed fetching past runs list", e);
    }
  };

  const loadRun = async (selectedRunId: string) => {
    try {
      setLoading(true);
      const res = await fetch(`/api/run-details?run_id=${selectedRunId}`);
      if (res.ok) {
        const json = await res.json();
        setRunId(json.id);
        setAuditData(json.audit_results);
        setEvalReport(json.eval_report);
        setHasUploaded(true);
      } else {
        alert("Failed loading past run details.");
      }
    } catch (e) {
      console.error("Failed loading run details", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPastRuns();
  }, []);

  const triggerScenarioAPI = async () => {
    try {
      const res = await fetch("/api/scenario", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          new_hires_count: newHiresCount,
          new_hires_salary: newHiresSalary,
          new_hires_start_month: newHiresStartMonth,
          payment_delay_days: paymentDelayDays,
          ad_spend: adSpend,
          cac: cac,
          office_upgrade: officeUpgrade,
          price_hike: priceHike,
          funding_round: fundingRound,
          funding_month: fundingMonth
        })
      });
      const json = await res.json();
      setForecast(json);
    } catch (e) {
      console.error("Failed fetching scenario", e);
    }
  };

  // Update scenario automatically as sliders change
  useEffect(() => {
    if (hasUploaded && !loading) {
      triggerScenarioAPI();
    }
  }, [
    newHiresCount, newHiresSalary, newHiresStartMonth, paymentDelayDays, 
    adSpend, cac, officeUpgrade, priceHike, fundingRound, fundingMonth, hasUploaded
  ]);

  const handleDownloadMock = async () => {
    setDownloading(true);
    try {
      await fetch('/api/generate', { method: 'POST' });
      const res = await fetch('/api/ledgers');
      const json = await res.json();
      const rows = json.ledger;
      
      const csvHeaders = ["TransactionID", "Date", "Description", "Amount", "MessyCategory", "GSTIN", "TDSSection", "VendorType", "ReceiptUploaded"];
      const csvRows = [csvHeaders.join(",")];
      
      rows.forEach((r: any) => {
        const values = csvHeaders.map(header => {
          const val = r[header];
          if (typeof val === 'string') {
            return `"${val.replace(/"/g, '""')}"`;
          }
          return val !== null && val !== undefined ? val : "";
        });
        csvRows.push(values.join(","));
      });
      
      const csvContent = csvRows.join("\n");
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", "razorpay_ledger_mock.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setHasDownloaded(true);
    } catch (e) {
      console.error("Download failed", e);
      alert("Failed generating sandbox dataset.");
    } finally {
      setDownloading(false);
    }
  };

  const handleLoadSample = async () => {
    if (!apiKey || !apiKey.trim()) {
      alert("Stage 2 compliance auditing requires a configured API key. Please click the 'AI Configuration' button in the top right to configure your API key first.");
      return;
    }
    setUploading(true);
    setCurrentView("analyzer");
    const formData = new FormData();
    formData.append("apiKey", apiKey);
    formData.append("provider", apiProvider);

    try {
      const res = await fetch("/api/load-sample", {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const json = await res.json();
        setRunId(json.run_id);
        setAuditData(json.audit_results);
        setEvalReport(json.eval_report);
        setHasUploaded(true);
        await Promise.all([fetchForecast(), fetchPastRuns()]);
        setActiveTab("metrics");
      } else {
        const err = await res.json();
        alert(`Error importing file: ${err.detail || "Invalid ledger format."}`);
      }
    } catch (e) {
      console.error("Ledger import failed", e);
      alert("Failed connecting to the backend API.");
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleImportCSV = async () => {
    if (!selectedFile) {
      alert("Please select a CSV statement file first!");
      return;
    }

    if (!apiKey || !apiKey.trim()) {
      alert("Stage 2 compliance auditing requires a configured API key. Please click the 'AI Configuration' button in the top right to configure your API key before importing.");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("apiKey", apiKey);
    formData.append("provider", apiProvider);

    try {
      const res = await fetch("/api/upload-ledger", {
        method: "POST",
        body: formData
      });
      
      if (res.ok) {
        const json = await res.json();
        setRunId(json.run_id);
        setAuditData(json.audit_results);
        setEvalReport(json.eval_report);
        setHasUploaded(true);
        await Promise.all([fetchForecast(), fetchPastRuns()]);
        setActiveTab("metrics");
      } else {
        const err = await res.json();
        alert(`Error importing file: ${err.detail || "Invalid ledger format."}`);
      }
    } catch (e) {
      console.error("Ledger import failed", e);
      alert("Failed connecting to the backend API.");
    } finally {
      setUploading(false);
    }
  };

  const handleSendChat = async () => {
    if (!chatInput.trim()) return;
    
    const userMsg = chatInput;
    setChatMessages(prev => [...prev, { sender: "user", text: userMsg }]);
    setChatInput("");
    setSendingChat(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg,
          apiKey: apiKey || null,
          provider: apiProvider,
          runId: runId
        })
      });
      const json = await res.json();
      setChatMessages(prev => [...prev, { sender: "bot", text: json.reply }]);
    } catch (e) {
      setChatMessages(prev => [...prev, { sender: "bot", text: "Error communicating with the assistant API." }]);
    } finally {
      setSendingChat(false);
    }
  };

  const formatLakhs = (num: number) => {
    return `Rs. ${(num / 100000).toFixed(2)} Lakhs`;
  };

  const formatRupees = (num: number) => {
    const formatted = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(Math.abs(num));
    return num < 0 ? `-₹${formatted}` : `₹${formatted}`;
  };

  const getShadedPolygonPoints = () => {
    if (!forecast.p90 || !forecast.p10 || forecast.p90.length === 0) return "";
    const maxVal = 2500000.00;
    const topPoints = forecast.p90.map((v, i) => {
      const x = 30 + (i * 90);
      const y = 140 - Math.max(0, Math.min(120, (v / maxVal) * 120));
      return `${x},${y}`;
    });
    const bottomPoints = forecast.p10.map((v, i) => {
      const x = 30 + (i * 90);
      const y = 140 - Math.max(0, Math.min(120, (v / maxVal) * 120));
      return `${x},${y}`;
    }).reverse();
    return [...topPoints, ...bottomPoints].join(" ");
  };

  return (
    <div className="min-h-screen bg-black text-neutral-100 flex flex-col font-sans selection:bg-[#EAB308]/30">
      
      {/* Top Main Navbar */}
      <nav className="border-b border-neutral-800 bg-[#171717] px-6 py-4 flex justify-between items-center shadow-md">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentView("home")}>
          <div className="relative flex items-center justify-center h-9 w-9">
            <div className="absolute inset-0 bg-[#EAB308] opacity-20 rounded-full animate-ping"></div>
            <div className="absolute h-6 w-6 rounded-full border-2 border-[#EAB308] flex items-center justify-center">
              <div className="h-2.5 w-2.5 rounded-full bg-[#F59E0B]"></div>
            </div>
          </div>
          <span className="font-extrabold text-lg tracking-wider text-white uppercase">AuraAudit</span>
          <span className="text-[10px] bg-neutral-900 px-2 py-0.5 rounded text-[#EAB308] border border-neutral-800 font-mono">Reconciler v2.1</span>
        </div>

        <div className="flex items-center space-x-4">
          <button 
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center space-x-1 border border-neutral-700 bg-neutral-800 hover:bg-neutral-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition"
          >
            <Settings className="h-4 w-4 text-neutral-400" />
            <span>AI Configuration</span>
          </button>
        </div>
      </nav>

      {/* Settings Modal Bar */}
      {showSettings && (
        <div className="bg-[#171717] border-b border-neutral-800 p-4 transition-all">
          <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
            <div>
              <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider block mb-1">Model Provider</label>
              <select 
                value={apiProvider}
                onChange={(e: any) => setApiProvider(e.target.value)}
                className="w-full bg-black text-white border border-neutral-700 text-xs rounded px-3 py-2 focus:outline-none"
              >
                <option value="openai">OpenRouter AI (Gemini 2.5 Flash)</option>
                <option value="gemini">Google Gemini Developer API</option>
                <option value="groq">Groq Cloud API (Llama 3.1 70B)</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider block mb-1">API Key</label>
              <input 
                type="password" 
                placeholder="Paste key to activate live LLM Stage 2 auditing..." 
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                autoComplete="new-password"
                spellCheck={false}
                data-lpignore="true"
                data-1p-ignore="true"
                className="w-full bg-black text-white border border-neutral-700 text-xs rounded px-3 py-2 focus:outline-none font-mono"
              />
            </div>
            <div className="pt-4 md:pt-0">
              <span className="text-[10px] text-[#EAB308] block leading-normal font-medium">
                🔒 In-memory only: Your API key is never written to disk, database, or storage. It vanishes completely upon browser refresh or server restart.
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Main Workspace Frame */}
      <div className="flex-1 flex flex-col justify-start">
        
        {/* PHASE 1: Landing Marketing / Flow Entry */}
        {currentView === "home" && (
          <div className="flex-1 max-w-5xl mx-auto w-full p-6 flex flex-col justify-center items-center text-center space-y-12 my-auto">
            
            <div className="space-y-4">
              <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
                Automate. Simulate. <br/>
                <span className="bg-gradient-to-r from-[#EAB308] to-[#EA580C] bg-clip-text text-transparent">
                  Secure Your Startup Treasury
                </span>
              </h1>
              <p className="text-neutral-400 max-w-xl mx-auto text-xs md:text-sm leading-relaxed">
                Reconcile transaction ledgers against complex Indian compliances (TDS, GSTR-2B, MSME 43B(h)) in a two-stage rule + generative LLM pipeline. Run Monte Carlo runway models instantly.
              </p>
            </div>

            {/* Grid Portals */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
              
              {/* Card 1: Generator Portal */}
              <div 
                onClick={() => setCurrentView("generator")}
                className="group cursor-pointer bg-[#171717] border border-neutral-800 p-8 rounded-2xl hover:border-[#EAB308]/60 transition-all text-left flex flex-col justify-between space-y-6 shadow-lg"
              >
                <div className="space-y-3">
                  <div className="h-10 w-10 rounded-lg bg-[#EAB308]/10 border border-[#EAB308]/30 flex items-center justify-center text-[#EAB308] group-hover:scale-105 transition">
                    <FileCode className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-bold text-white group-hover:text-[#EAB308] transition">1. Setup Sandbox Dataset</h3>
                  <p className="text-xs text-neutral-400 leading-relaxed">
                    Synthesize a 50+ record bank ledger batch injected with TDS split-payments, typo-induced MSME delays, duplicate rents, and missing receipts. Includes ground-truth labels.
                  </p>
                </div>
                <span className="text-xs font-bold text-[#EAB308] flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
                  <span>Enter Generator Portal</span>
                  <span>→</span>
                </span>
              </div>

              {/* Card 2: Upload Audit Analyzer */}
              <div 
                onClick={() => setCurrentView("analyzer")}
                className="group cursor-pointer bg-[#171717] border border-neutral-800 p-8 rounded-2xl hover:border-[#F59E0B]/60 transition-all text-left flex flex-col justify-between space-y-6 shadow-lg"
              >
                <div className="space-y-3">
                  <div className="h-10 w-10 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/30 flex items-center justify-center text-[#F59E0B] group-hover:scale-105 transition">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-bold text-white group-hover:text-[#F59E0B] transition">2. Run Reconciler Core</h3>
                  <p className="text-xs text-neutral-400 leading-relaxed">
                    Upload your bank ledger CSV statement. Run the deterministic and LLM classifier loops, verify the pipeline's accuracy, and export QuickBooks corrections.
                  </p>
                </div>
                <span className="text-xs font-bold text-[#F59E0B] flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
                  <span>Open Audit Workspace</span>
                  <span>→</span>
                </span>
              </div>

            </div>

            {/* Clean Graphics Line Grid */}
            <div className="w-full border border-neutral-800 p-6 rounded-2xl bg-[#171717]/40 text-left max-w-4xl text-xs space-y-4">
              <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider block">Compliance Checklist Verified</span>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-neutral-400 font-semibold font-mono">
                <span className="flex items-center space-x-2"><CheckCircle className="h-4 w-4 text-[#EAB308]" /> <span>TDS Sec 194J/194R</span></span>
                <span className="flex items-center space-x-2"><CheckCircle className="h-4 w-4 text-[#EAB308]" /> <span>MSME Sec 43B(h)</span></span>
                <span className="flex items-center space-x-2"><CheckCircle className="h-4 w-4 text-[#EAB308]" /> <span>GSTR-2B Mismatches</span></span>
                <span className="flex items-center space-x-2"><CheckCircle className="h-4 w-4 text-[#EAB308]" /> <span>Duplicate Auditing</span></span>
              </div>
            </div>

          </div>
        )}

        {/* PHASE 2: Sandbox Generator View */}
        {currentView === "generator" && (
          <div className="flex-1 max-w-2xl mx-auto w-full p-6 flex flex-col justify-center my-auto space-y-6">
            <div className="bg-[#171717] border border-neutral-800 rounded-2xl p-8 shadow-xl space-y-6">
              
              <div className="space-y-2">
                <button 
                  onClick={() => setCurrentView("home")}
                  className="text-xs font-semibold text-[#EAB308] flex items-center space-x-1 hover:underline"
                >
                  <ArrowLeft className="h-3 w-3" />
                  <span>Back to Home</span>
                </button>
                <h2 className="text-xl font-bold text-white">Generate Sandbox Ledger Batch</h2>
                <p className="text-xs text-neutral-400">Creates a compliant 55-record bank ledger CSV statement along with a validation key label list.</p>
              </div>

              <div className="bg-neutral-900/60 p-4 rounded-xl border border-neutral-800 space-y-3 text-xs leading-normal">
                <span className="font-bold text-[#F59E0B] block">Injected Sandbox Cases Included:</span>
                <ul className="list-disc pl-4 space-y-1.5 text-neutral-400">
                  <li>**TDS Split Payments:** Two professional fee clearances of Rs. 20,000 to bypass Section 194J threshold.</li>
                  <li>**MSME Name Typo:** Outstanding packing materials invoice to "Rajj Packrs" (typo matching Raj Packers).</li>
                  <li>**Contractor Perks (Section 194R):** Rs. 25,000 contractor benefit labeled as gift.</li>
                  <li>**Duplicated Rent:** Double billing of office lease rent to Sharma Realty.</li>
                </ul>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={handleDownloadMock}
                  disabled={downloading}
                  className="flex-1 bg-[#EAB308] hover:bg-[#CA8A04] text-[#000000] font-bold text-xs py-3 rounded-lg transition flex justify-center items-center space-x-1.5 shadow-md"
                >
                  {downloading ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Synthesizing Batch...</span>
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4" />
                      <span>Download Statement CSV</span>
                    </>
                  )}
                </button>

                {hasDownloaded && (
                  <button 
                    onClick={handleLoadSample}
                    className="flex-1 bg-transparent hover:bg-neutral-800 text-[#EAB308] border border-[#EAB308]/30 font-bold text-xs py-3 rounded-lg transition"
                  >
                    Load in Analyzer →
                  </button>
                )}
              </div>

            </div>
          </div>
        )}

        {/* PHASE 3: Analyzer Workspace Dashboard */}
        {currentView === "analyzer" && (
          <div className="flex-1 flex flex-col">
            {!hasUploaded ? (
              
              /* File Upload Page */
              <div className="flex-1 max-w-md mx-auto w-full p-6 flex flex-col justify-center my-auto space-y-6">
                <div className="bg-[#171717] border border-neutral-800 rounded-2xl p-6 shadow-xl space-y-5 text-center">
                  
                  <div className="text-left space-y-1 mb-2">
                    <button 
                      onClick={() => setCurrentView("home")}
                      className="text-xs font-semibold text-[#F59E0B] flex items-center space-x-1 hover:underline"
                    >
                      <ArrowLeft className="h-3 w-3" />
                      <span>Back to Home</span>
                    </button>
                    <h3 className="text-base font-bold text-white">Upload Bank Statement</h3>
                    <p className="text-[11px] text-neutral-400">Select statement to run evaluation metrics.</p>
                  </div>

                  <div className="border-2 border-dashed border-neutral-800 hover:border-[#F59E0B]/50 rounded-xl p-8 relative cursor-pointer group bg-neutral-900/30 transition">
                    <input 
                      type="file" 
                      accept=".csv" 
                      onChange={handleFileChange}
                      className="absolute inset-0 opacity-0 w-full h-full cursor-pointer"
                    />
                    <FileText className="h-8 w-8 text-[#F59E0B] mx-auto mb-2" />
                    <span className="text-xs text-white font-semibold block">
                      {selectedFile ? selectedFile.name : "Click to select CSV File"}
                    </span>
                    <span className="text-[10px] text-neutral-500 mt-1 block">Supports .csv statements</span>
                  </div>

                  <div className="flex space-x-4 pt-2">
                    <button 
                      onClick={() => setCurrentView("home")}
                      className="flex-1 border border-neutral-700 hover:bg-neutral-800 text-neutral-300 font-semibold text-xs py-2.5 rounded-lg transition"
                    >
                      Cancel
                    </button>
                    <button 
                      onClick={handleImportCSV}
                      disabled={uploading || !selectedFile}
                      className="flex-1 bg-[#F59E0B] hover:bg-[#D97706] disabled:opacity-50 text-white font-bold text-xs py-2.5 rounded-lg transition flex justify-center items-center space-x-1.5 shadow-sm"
                    >
                      {uploading ? (
                        <>
                          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          <span>Uploading...</span>
                        </>
                      ) : (
                        <span>Import & Analyze</span>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              
              /* Phase 3B: Analysis Dashboard */
              <div className="flex-1 w-full max-w-7xl mx-auto p-6 space-y-6">
                
                {/* Tab Header bar */}
                <div className="flex justify-between items-center border-b border-neutral-800 bg-[#171717] px-6 py-2 rounded-t-xl shadow-sm">
                  <div className="flex space-x-4">
                    <button 
                      onClick={() => setActiveTab("metrics")}
                      className={`py-3.5 px-4 font-bold text-sm border-b-2 transition ${activeTab === "metrics" ? "border-[#EAB308] text-[#EAB308]" : "border-transparent text-neutral-400 hover:text-white"}`}
                    >
                      Reconciliation Metrics
                    </button>
                    <button 
                      onClick={() => setActiveTab("resolved")}
                      className={`py-3.5 px-4 font-bold text-sm border-b-2 transition ${activeTab === "resolved" ? "border-[#EAB308] text-[#EAB308]" : "border-transparent text-neutral-400 hover:text-white"}`}
                    >
                      Resolved Matches
                    </button>
                    <button 
                      onClick={() => setActiveTab("exceptions")}
                      className={`py-3.5 px-4 font-bold text-sm border-b-2 transition ${activeTab === "exceptions" ? "border-[#EAB308] text-[#EAB308]" : "border-transparent text-neutral-400 hover:text-white"}`}
                    >
                      Audit Exceptions
                    </button>
                    <button 
                      onClick={() => setActiveTab("extended")}
                      className={`py-3.5 px-4 font-bold text-sm border-b-2 transition ${activeTab === "extended" ? "border-[#EAB308] text-[#EAB308]" : "border-transparent text-neutral-400 hover:text-white"}`}
                    >
                      Extended Strategy Tools
                    </button>
                  </div>

                  <span className="text-xs bg-black border border-neutral-700 font-semibold px-2.5 py-1 rounded text-neutral-300">
                    Active Session: {runId || "none"}
                  </span>
                </div>

                {/* Dashboard Core Tab Workspace */}
                <div className="bg-[#171717] p-6 rounded-b-xl border-x-2 border-b-2 border-neutral-800 shadow-sm min-h-[500px]">
                  
                  {/* TAB 1: RECONCILIATION ACCURACY METRICS */}
                  {activeTab === "metrics" && (
                    <div className="space-y-6">
                      <div className="flex justify-between items-center border-b border-neutral-800 pb-3">
                        <div>
                          <h3 className="text-base font-bold text-white">Reconciliation Accuracy & Evaluation Report</h3>
                          <p className="text-xs text-neutral-400">Measured accuracy of the two-stage (Heuristic + LLM) auditing pipeline against ground-truth labels.</p>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-neutral-400 font-semibold">Load Run History:</span>
                          <select
                            onChange={(e) => {
                              if (e.target.value) loadRun(e.target.value);
                            }}
                            value={runId || ""}
                            className="bg-black text-white border border-neutral-800 text-xs rounded px-2 py-1.5 focus:outline-none font-semibold font-mono"
                          >
                            <option value="" disabled>Select past session...</option>
                            {pastRuns.map((r) => (
                              <option key={r.id} value={r.id}>
                                {r.filename} ({(r.match_rate * 100).toFixed(0)}% match - {new Date(r.timestamp).toLocaleTimeString()})
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Big Metrics Dial / Cards Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-black p-6 rounded-xl border border-neutral-800 flex flex-col justify-center items-center text-center shadow-sm">
                          <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider mb-2">Match Rate (Accuracy)</span>
                          <div className="relative flex items-center justify-center">
                            <svg className="w-24 h-24">
                              <circle className="text-neutral-900" strokeWidth="6" stroke="#262626" fill="transparent" r="40" cx="48" cy="48"/>
                              <circle className="text-[#EAB308]" strokeWidth="6" strokeDasharray={251.2} strokeDashoffset={251.2 - (251.2 * (evalReport?.match_rate ?? 0.0))} strokeLinecap="round" stroke="currentColor" fill="transparent" r="40" cx="48" cy="48" style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}/>
                            </svg>
                            <span className="absolute text-xl font-mono font-bold text-white">{(evalReport?.match_rate ? evalReport.match_rate * 100 : 0.0).toFixed(1)}%</span>
                          </div>
                          <span className="text-[10px] text-neutral-500 mt-3 font-semibold">Reconciliation match success</span>
                        </div>

                        <div className="bg-black p-6 rounded-xl border border-neutral-800 flex flex-col justify-center items-center text-center shadow-sm">
                          <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider mb-2">Precision</span>
                          <div className="relative flex items-center justify-center">
                            <svg className="w-24 h-24">
                              <circle className="text-neutral-900" strokeWidth="6" stroke="#262626" fill="transparent" r="40" cx="48" cy="48"/>
                              <circle className="text-[#F59E0B]" strokeWidth="6" strokeDasharray={251.2} strokeDashoffset={251.2 - (251.2 * (evalReport?.precision ?? 0.0))} strokeLinecap="round" stroke="currentColor" fill="transparent" r="40" cx="48" cy="48" style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}/>
                            </svg>
                            <span className="absolute text-xl font-mono font-bold text-white">{(evalReport?.precision ? evalReport.precision * 100 : 0.0).toFixed(1)}%</span>
                          </div>
                          <span className="text-[10px] text-neutral-500 mt-3 font-semibold">Flagging precision index</span>
                        </div>

                        <div className="bg-black p-6 rounded-xl border border-neutral-800 flex flex-col justify-center items-center text-center shadow-sm">
                          <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider mb-2">Recall</span>
                          <div className="relative flex items-center justify-center">
                            <svg className="w-24 h-24">
                              <circle className="text-neutral-900" strokeWidth="6" stroke="#262626" fill="transparent" r="40" cx="48" cy="48"/>
                              <circle className="text-[#F59E0B]" strokeWidth="6" strokeDasharray={251.2} strokeDashoffset={251.2 - (251.2 * (evalReport?.recall ?? 0.0))} strokeLinecap="round" stroke="currentColor" fill="transparent" r="40" cx="48" cy="48" style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}/>
                            </svg>
                            <span className="absolute text-xl font-mono font-bold text-white">{(evalReport?.recall ? evalReport.recall * 100 : 0.0).toFixed(1)}%</span>
                          </div>
                          <span className="text-[10px] text-neutral-500 mt-3 font-semibold">Exhaustive recall rate</span>
                        </div>

                        <div className="bg-black p-4 rounded-xl border border-neutral-800 flex flex-col justify-center shadow-sm">
                          <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider mb-3">Confusion Matrix</span>
                          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                            <div className="bg-neutral-900/50 p-2 rounded border border-neutral-900">
                              <div className="text-neutral-500 text-[9px] uppercase font-bold">True Positives</div>
                              <div className="text-white font-bold text-sm mt-0.5">{evalReport?.tp ?? 0}</div>
                            </div>
                            <div className="bg-neutral-900/50 p-2 rounded border border-neutral-900">
                              <div className="text-neutral-500 text-[9px] uppercase font-bold">True Negatives</div>
                              <div className="text-white font-bold text-sm mt-0.5">{evalReport?.tn ?? 0}</div>
                            </div>
                            <div className="bg-neutral-900/50 p-2 rounded border border-neutral-900">
                              <div className="text-neutral-500 text-[9px] uppercase font-bold">False Positives</div>
                              <div className="text-rose-400 font-bold text-sm mt-0.5">{evalReport?.fp ?? 0}</div>
                            </div>
                            <div className="bg-neutral-900/50 p-2 rounded border border-neutral-900">
                              <div className="text-neutral-500 text-[9px] uppercase font-bold">False Negatives</div>
                              <div className="text-rose-400 font-bold text-sm mt-0.5">{evalReport?.fn ?? 0}</div>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Breakdown category Table */}
                      <div className="space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-300">Category Accuracy Breakdown</h4>
                        <div className="overflow-x-auto border border-neutral-800 rounded-lg">
                          <table className="min-w-full divide-y divide-neutral-800 text-xs text-left">
                            <thead className="bg-black text-neutral-400 font-bold">
                              <tr>
                                <th className="px-4 py-3">Compliance Category / Penalty Code</th>
                                <th className="px-4 py-3 text-right">Expected Exceptions</th>
                                <th className="px-4 py-3 text-right">Correctly Detected</th>
                                <th className="px-4 py-3 text-right">Total Flags Added</th>
                                <th className="px-4 py-3 text-right">Category Accuracy</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-neutral-800 bg-[#171717] text-neutral-300 font-medium font-sans">
                              {Object.entries(evalReport?.category_metrics || {
                                "TDS_UNDER_DEDUCTION": { expected_count: 0, detected_count: 0, correct_count: 0, accuracy: 0.0 },
                                "MSME_PAYMENT_DELAY": { expected_count: 0, detected_count: 0, correct_count: 0, accuracy: 0.0 },
                                "GSTR2B_MISMATCH": { expected_count: 0, detected_count: 0, correct_count: 0, accuracy: 0.0 },
                                "MISSING_RECEIPT": { expected_count: 0, detected_count: 0, correct_count: 0, accuracy: 0.0 },
                                "DUPLICATE_PAYMENT": { expected_count: 0, detected_count: 0, correct_count: 0, accuracy: 0.0 },
                                "SAAS_PRICE_SPIKE": { expected_count: 0, detected_count: 0, correct_count: 0, accuracy: 0.0 }
                              }).map(([key, item]: [string, any]) => (
                                <tr key={key} className="hover:bg-neutral-800/40">
                                  <td className="px-4 py-3 font-semibold text-white font-mono">{key.replace("_", " ")}</td>
                                  <td className="px-4 py-3 text-right font-mono">{item.expected_count}</td>
                                  <td className="px-4 py-3 text-right font-mono text-emerald-400">{item.correct_count}</td>
                                  <td className="px-4 py-3 text-right font-mono">{item.detected_count}</td>
                                  <td className="px-4 py-3 text-right font-mono font-bold text-[#EAB308]">{(item.accuracy * 100).toFixed(0)}%</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Evaluating Pipeline Alert */}
                      <div className="bg-neutral-950/80 border border-neutral-800 rounded-lg p-4 text-xs flex items-start">
                        <Info className="h-4 w-4 mr-2 text-[#EAB308] shrink-0 mt-0.5" />
                        <div className="space-y-1">
                          <span className="text-[#EAB308] font-bold">Judged Pipeline Configuration:</span>
                          <p className="text-neutral-400 leading-relaxed">
                            Every upload initiates a two-stage classification engine: Stage 1 parses deterministic business rules while Stage 2 invokes a generative LLM reasoning call (via OpenAI, Groq, or Gemini API) to check semantic ambiguities (such as split payments, contractor benefits under Section 194R, and typo-induced invoice delays). Accuracy rates are computed dynamically against ground-truth labels.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* TAB 2: RESOLVED MATCHES LIST */}
                  {activeTab === "resolved" && (() => {
                    const resolvedList = (auditData?.audited_transactions || []).filter((tx: any) => !tx.flags || tx.flags.length === 0);
                    return (
                      <div className="space-y-6">
                        <div className="flex justify-between items-center border-b border-neutral-800 pb-3">
                          <div>
                            <h3 className="text-base font-bold text-white">Resolved Matches & Reconciled Entries</h3>
                            <p className="text-xs text-neutral-400">Transactions cleared as compliant without requiring manual exception resolution.</p>
                          </div>
                          <span className="text-xs bg-black text-[#EAB308] border border-[#EAB308]/30 font-bold px-3 py-1 rounded-lg">
                            {resolvedList.length} Compliant Items
                          </span>
                        </div>

                        <div className="overflow-x-auto border border-neutral-800 rounded-lg">
                          <table className="min-w-full divide-y divide-neutral-800 text-xs text-left">
                            <thead className="bg-black text-neutral-400 font-bold">
                              <tr>
                                <th className="px-4 py-3">TX ID</th>
                                <th className="px-4 py-3">Date</th>
                                <th className="px-4 py-3">Description</th>
                                <th className="px-4 py-3">Messy Category</th>
                                <th className="px-4 py-3">Audited Category</th>
                                <th className="px-4 py-3 text-right">Amount</th>
                                <th className="px-4 py-3 text-center">Status</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-neutral-800 bg-[#171717] text-neutral-300 font-medium">
                              {resolvedList.length === 0 ? (
                                <tr>
                                  <td colSpan={7} className="px-4 py-8 text-center text-neutral-500 italic">No reconciled entries found. Run or upload a statement.</td>
                                </tr>
                              ) : (
                                resolvedList.map((tx: any) => (
                                  <tr key={tx.tx_id} className="hover:bg-neutral-800/40">
                                    <td className="px-4 py-3 font-mono font-bold text-white">{tx.tx_id}</td>
                                    <td className="px-4 py-3 font-mono">{tx.date}</td>
                                    <td className="px-4 py-3">{tx.description}</td>
                                    <td className="px-4 py-3 text-neutral-500">{tx.messy_category || "-"}</td>
                                    <td className="px-4 py-3 text-[#EAB308]">{tx.audited_category}</td>
                                    <td className="px-4 py-3 text-right font-mono font-bold text-white">{formatRupees(tx.amount)}</td>
                                    <td className="px-4 py-3 text-center">
                                      <span className="bg-emerald-950 text-emerald-400 border border-emerald-900 text-[9px] font-bold px-2.5 py-0.5 rounded-full">
                                        MATCHED (100%)
                                      </span>
                                    </td>
                                  </tr>
                                ))
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    );
                  })()}

                  {/* TAB 3: AUDIT EXCEPTIONS */}
                  {activeTab === "exceptions" && (() => {
                    const exceptionsList = auditData?.exceptions || [];
                    
                    const handleDownloadExport = async () => {
                      if (exceptionsList.length === 0) return;
                      try {
                        const res = await fetch("/api/export-adjustments", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({
                            exceptions: exceptionsList,
                            format: exportFormat
                          })
                        });
                        const blob = await res.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = exportFormat === "quickbooks" ? "quickbooks_adjustments.iif" : "reconciliation_exceptions.csv";
                        a.click();
                      } catch (e) {
                        console.error("Export failed", e);
                      }
                    };

                    return (
                      <div className="space-y-6">
                        <div className="flex justify-between items-center border-b border-neutral-800 pb-3">
                          <div>
                            <h3 className="text-base font-bold text-white">Honest Exceptions & Adjustments List</h3>
                            <p className="text-xs text-neutral-400">Identified compliance failures and semantic issues that require review or journal postings.</p>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            <select 
                              value={exportFormat}
                              onChange={(e: any) => setExportFormat(e.target.value)}
                              className="bg-black text-white border border-neutral-800 text-xs rounded px-2 py-1.5 focus:outline-none font-semibold"
                            >
                              <option value="csv">Export CSV</option>
                              <option value="quickbooks">Export QuickBooks IIF</option>
                            </select>
                            <button 
                              onClick={handleDownloadExport}
                              disabled={exceptionsList.length === 0}
                              className="bg-[#EAB308] hover:bg-[#CA8A04] text-[#000000] font-bold text-xs px-4 py-1.5 rounded-lg transition disabled:opacity-50"
                            >
                              Export Ledger
                            </button>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 gap-4">
                          {exceptionsList.length === 0 ? (
                            <div className="bg-black p-8 rounded-xl border border-neutral-800 text-center text-neutral-500 italic">
                              No exceptions found in this reconciliation run.
                            </div>
                          ) : (
                            exceptionsList.map((exc: any, idx: number) => {
                              let badgeStyle = "bg-rose-950 text-rose-400 border border-rose-900";
                              if (exc.type === "MSME_PAYMENT_DELAY") badgeStyle = "bg-amber-950 text-amber-500 border border-amber-900";
                              
                              return (
                                <div key={idx} className="bg-black p-5 rounded-xl border border-neutral-800 space-y-4">
                                  <div className="flex justify-between items-start">
                                    <div className="space-y-1">
                                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${badgeStyle}`}>
                                        {exc.type.replace('_', ' ')}
                                      </span>
                                      <h4 className="text-sm font-bold text-white mt-1">Transaction {exc.tx_id}</h4>
                                      <p className="text-[11px] text-neutral-500">Date: {exc.date} | Amount: {formatRupees(exc.amount)}</p>
                                    </div>
                                    
                                    <div className="text-right">
                                      <span className="text-[10px] text-neutral-400 font-semibold block uppercase">Confidence</span>
                                      <span className="text-sm font-mono font-bold text-[#EAB308]">{(exc.confidence ? exc.confidence * 100 : 95.0).toFixed(0)}%</span>
                                    </div>
                                  </div>

                                  <div className="border-t border-neutral-800/60 pt-3 text-xs space-y-2">
                                    <div>
                                      <span className="text-neutral-400 font-bold block mb-0.5">Audit Discovery & Reason:</span>
                                      <p className="text-neutral-300 leading-relaxed">{exc.details}</p>
                                    </div>
                                    
                                    {exc.proposed_adjustment && (
                                      <div className="bg-neutral-950/40 border border-neutral-800 p-2.5 rounded">
                                        <span className="text-amber-500 font-bold block text-[10px] uppercase mb-1">Proposed Balancing Journal Entry:</span>
                                        <span className="text-[#EAB308] font-mono block select-all">{exc.proposed_adjustment}</span>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })
                          )}
                        </div>
                      </div>
                    );
                  })()}

                  {/* TAB 4: EXTENDED STRATEGY TOOLS */}
                  {activeTab === "extended" && (
                    <div className="space-y-6">
                      
                      {/* Sub-tab selection */}
                      <div className="flex space-x-2 border-b border-neutral-800 pb-2">
                        <button 
                          onClick={() => setExtendedTab("forecast")}
                          className={`px-4 py-2 font-bold text-xs rounded-lg transition ${extendedTab === "forecast" ? "bg-neutral-800 text-[#EAB308] border border-neutral-700" : "text-neutral-400 hover:text-white"}`}
                        >
                          Cash Runway Forecast Simulator
                        </button>
                        <button 
                          onClick={() => setExtendedTab("msme_priority")}
                          className={`px-4 py-2 font-bold text-xs rounded-lg transition ${extendedTab === "msme_priority" ? "bg-neutral-800 text-[#EAB308] border border-neutral-700" : "text-neutral-400 hover:text-white"}`}
                        >
                          MSME Payment Priority Allocator
                        </button>
                      </div>

                      {/* SUB-VIEW 1: Cash Runway forecast */}
                      {extendedTab === "forecast" && (
                        <div className="space-y-6">
                          
                          {/* Grid metrics */}
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-stretch">
                            <div className="flex flex-col gap-4">
                              <div className="bg-black p-5 rounded-xl border border-neutral-800 shadow-sm flex flex-col justify-center flex-1">
                                <p className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">CASH BALANCE (INR)</p>
                                <h3 className="text-xl font-bold mt-1 text-[#EAB308]">{formatLakhs(forecast.starting_cash)}</h3>
                                <span className="text-[9px] text-neutral-500 mt-0.5">Closing cash level</span>
                              </div>
                              
                              <div className="bg-black p-5 rounded-xl border border-neutral-800 shadow-sm flex flex-col justify-center flex-1">
                                <p className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">NET MONTHLY BURN (INR)</p>
                                <h3 className="text-xl font-bold mt-1 text-[#F59E0B]">{formatLakhs(forecast.monthly_burn)}</h3>
                                <span className="text-[9px] text-neutral-500 mt-0.5">Taxes & scenarios included</span>
                              </div>
                              
                              <div className="bg-[#2B2319] p-5 rounded-xl border border-amber-600/40 shadow-sm flex flex-col justify-center flex-1">
                                <p className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">CASH RUNWAY</p>
                                <h3 className={`text-xl font-bold mt-1 ${forecast.runway_months <= 2 ? "text-amber-500" : "text-emerald-400"}`}>
                                  {`${forecast.runway_months} Months`}
                                </h3>
                                <span className="inline-flex items-center text-[9px] text-[#F59E0B] mt-1 border border-amber-600/35 px-1.5 py-0.5 rounded-full w-fit bg-amber-500/5 font-semibold">
                                  Configurable Constant Run
                                </span>
                              </div>
                            </div>

                            {/* Chart */}
                            <div className="md:col-span-3 border border-neutral-800 p-6 rounded-xl bg-black flex flex-col justify-between shadow-sm min-h-[300px] relative">
                              <div className="absolute top-4 right-4 bg-[#2B2319]/90 border border-amber-600/30 rounded-lg p-3 w-52 shadow-xl z-10 text-left">
                                <span className="text-[9px] text-amber-400/85 font-bold uppercase tracking-wider block">Depletion Risk</span>
                                <h5 className="text-xs font-bold text-[#F59E0B] mt-0.5">Projected Cash Out Date</h5>
                                <div className="flex justify-between items-baseline mt-1">
                                  <span className="text-sm font-extrabold text-[#F59E0B]">
                                    {forecast.runway_months < 6 ? forecast.months[forecast.runway_months] : "Stable"}
                                  </span>
                                  <span className="text-[9px] text-amber-500/80 font-medium">Time to out date: 10th</span>
                                </div>
                              </div>

                              <div>
                                <span className="text-xs text-neutral-400 font-bold uppercase tracking-wider block">Monte Carlo Confidence Band</span>
                                <h4 className="text-base font-extrabold text-white mt-1">Cash Depletion Volatility Forecast</h4>
                              </div>

                              <div className="h-44 w-full mt-4 flex items-end">
                                <svg className="w-full h-full overflow-visible" viewBox="0 0 500 150">
                                  <polygon points={getShadedPolygonPoints()} fill="#EAB308" fillOpacity="0.08" />
                                  <line x1="30" y1="20" x2="480" y2="20" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3"/>
                                  <line x1="30" y1="50" x2="480" y2="50" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3"/>
                                  <line x1="30" y1="80" x2="480" y2="80" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3"/>
                                  <line x1="30" y1="110" x2="480" y2="110" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3"/>
                                  <line x1="30" y1="140" x2="480" y2="140" stroke="#334155" strokeWidth="1.5" />

                                  <polyline fill="none" stroke="#10B981" strokeWidth="2" strokeDasharray="2 2"
                                    points={forecast.p90.map((v, i) => `${30 + (i * 90)},${140 - Math.max(0, Math.min(120, (v / 2500000) * 120))}`).join(" ")}
                                  />
                                  <polyline fill="none" stroke="#EAB308" strokeWidth="3.5" 
                                    points={forecast.p50.map((v, i) => `${30 + (i * 90)},${140 - Math.max(0, Math.min(120, (v / 2500000) * 120))}`).join(" ")}
                                  />
                                  <polyline fill="none" stroke="#F59E0B" strokeWidth="2" strokeDasharray="2 2"
                                    points={forecast.p10.map((v, i) => `${30 + (i * 90)},${140 - Math.max(0, Math.min(120, (v / 2500000) * 120))}`).join(" ")}
                                  />

                                  {forecast.months.map((m, i) => (
                                    <text key={i} x={30 + (i * 90)} y="150" fill="#64748B" textAnchor="middle" className="text-[9px] font-bold font-mono">
                                      {m}
                                    </text>
                                  ))}

                                  {activeMonthIdx !== null && (
                                    <>
                                      <line x1={30 + (activeMonthIdx * 90)} y1="20" x2={30 + (activeMonthIdx * 90)} y2="140" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="4 2" />
                                      <circle cx={30 + (activeMonthIdx * 90)} cy={140 - Math.max(0, Math.min(120, (forecast.p50[activeMonthIdx] / 2500000) * 120))} r="5" fill="#F59E0B" stroke="#FFFFFF" strokeWidth="1.5" />
                                    </>
                                  )}
                                </svg>
                              </div>
                            </div>
                          </div>

                          {/* Strategy Controls */}
                          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            <div className="bg-black p-5 rounded-xl border border-neutral-800 shadow-sm">
                              <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider block">Projection Details</span>
                              <div className="mt-3 space-y-2 text-xs">
                                <div className="flex justify-between">
                                  <span className="text-neutral-500">Month:</span>
                                  <span className="text-white font-bold">{forecast.months[activeMonthIdx]}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-emerald-400">p90 (Optimistic):</span>
                                  <span className="text-white font-bold font-mono">{formatRupees(forecast.p90[activeMonthIdx])}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-[#EAB308]">p50 (Likely):</span>
                                  <span className="text-white font-bold font-mono">{formatRupees(forecast.p50[activeMonthIdx])}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-amber-500">p10 (Conservative):</span>
                                  <span className="text-white font-bold font-mono">{formatRupees(forecast.p10[activeMonthIdx])}</span>
                                </div>
                              </div>
                              <div className="flex gap-1 mt-4">
                                {forecast.months.map((_, idx) => (
                                  <button key={idx} onClick={() => setActiveMonthIdx(idx)} className={`flex-1 py-1 rounded text-[10px] font-bold font-mono ${activeMonthIdx === idx ? "bg-[#EAB308] text-[#000000]" : "bg-neutral-900 text-neutral-400 hover:text-white"}`}>
                                    M{idx+1}
                                  </button>
                                ))}
                              </div>
                            </div>

                            <div className="md:col-span-3 border border-neutral-800 rounded-xl bg-black p-5 space-y-4">
                              <div className="flex space-x-2 border-b border-neutral-900 pb-2">
                                <button onClick={() => setPlaygroundTab("hiring")} className={`px-3 py-1 text-xs font-bold rounded-lg transition ${playgroundTab === "hiring" ? "bg-neutral-800 text-[#F59E0B] border border-neutral-700" : "text-neutral-400 hover:text-white"}`}>Hiring & Payroll</button>
                                <button onClick={() => setPlaygroundTab("marketing")} className={`px-3 py-1 text-xs font-bold rounded-lg transition ${playgroundTab === "marketing" ? "bg-neutral-800 text-[#F59E0B] border border-neutral-700" : "text-neutral-400 hover:text-white"}`}>Growth Marketing</button>
                                <button onClick={() => setPlaygroundTab("capital")} className={`px-3 py-1 text-xs font-bold rounded-lg transition ${playgroundTab === "capital" ? "bg-neutral-800 text-[#F59E0B] border border-neutral-700" : "text-neutral-400 hover:text-white"}`}>Capital & Pricing</button>
                              </div>

                              <div className="space-y-4 pt-2">
                                {playgroundTab === "hiring" && (
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                      <label className="text-xs text-neutral-400 flex justify-between">
                                        <span>Engineering Headcount Addition</span>
                                        <span className="font-mono font-bold text-white">{newHiresCount} Hires</span>
                                      </label>
                                      <input type="range" min="0" max="15" step="1" value={newHiresCount} onChange={(e) => setNewHiresCount(parseInt(e.target.value))} className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-[#EAB308]" />
                                    </div>
                                    <div className="space-y-2">
                                      <label className="text-xs text-neutral-400 flex justify-between">
                                        <span>Average Monthly Cost Per Hire</span>
                                        <span className="font-mono font-bold text-white">{formatLakhs(newHiresSalary)}</span>
                                      </label>
                                      <input type="range" min="50000" max="300000" step="10000" value={newHiresSalary} onChange={(e) => setNewHiresSalary(parseInt(e.target.value))} className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-[#EAB308]" />
                                    </div>
                                  </div>
                                )}

                                {playgroundTab === "marketing" && (
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                      <label className="text-xs text-neutral-400 flex justify-between">
                                        <span>Ad Spend Spend</span>
                                        <span className="font-mono font-bold text-white">{formatLakhs(adSpend)}</span>
                                      </label>
                                      <input type="range" min="0" max="500000" step="25000" value={adSpend} onChange={(e) => setAdSpend(parseInt(e.target.value))} className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-[#EAB308]" />
                                    </div>
                                    <div className="space-y-2">
                                      <label className="text-xs text-neutral-400 flex justify-between">
                                        <span>Customer Acquisition Cost</span>
                                        <span className="font-mono font-bold text-white">{formatRupees(cac)}</span>
                                      </label>
                                      <input type="range" min="500" max="5000" step="100" value={cac} onChange={(e) => setCac(parseInt(e.target.value))} className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-[#EAB308]" />
                                    </div>
                                  </div>
                                )}

                                {playgroundTab === "capital" && (
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                      <label className="text-xs text-neutral-400 flex justify-between">
                                        <span>Product Pricing Hike</span>
                                        <span className="font-mono font-bold text-white">{priceHike}% hike</span>
                                      </label>
                                      <input type="range" min="-10" max="30" step="5" value={priceHike} onChange={(e) => setPriceHike(parseInt(e.target.value))} className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-[#EAB308]" />
                                    </div>
                                    <div className="space-y-2">
                                      <label className="text-xs text-neutral-400 flex justify-between">
                                        <span>Financing Round Funding</span>
                                        <span className="font-mono font-bold text-white">{formatLakhs(fundingRound)}</span>
                                      </label>
                                      <input type="range" min="0" max="5000000" step="500000" value={fundingRound} onChange={(e) => setFundingRound(parseInt(e.target.value))} className="w-full h-1 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-[#EAB308]" />
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="space-y-2">
                            <table className="w-full border-collapse border border-neutral-900 text-xs">
                              <thead className="bg-black text-neutral-400 font-bold font-sans">
                                <tr>
                                  <th className="px-4 py-3 text-left">Month</th>
                                  <th className="px-4 py-3 text-right">Optimistic (p90)</th>
                                  <th className="px-4 py-3 text-right">Most Likely (p50)</th>
                                  <th className="px-4 py-3 text-right">Conservative (p10)</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-neutral-800 bg-[#171717] text-neutral-300 font-mono">
                                {forecast.months.map((m, i) => (
                                  <tr key={i} className="hover:bg-neutral-800/40">
                                    <td className="px-4 py-3 font-sans font-bold text-neutral-200">{m}</td>
                                    <td className="px-4 py-3 text-right font-medium text-emerald-450 text-[#10B981]">{formatRupees(forecast.p90[i])}</td>
                                    <td className="px-4 py-3 text-right font-bold text-[#EAB308]">{formatRupees(forecast.p50[i])}</td>
                                    <td className="px-4 py-3 text-right font-medium text-amber-500">{formatRupees(forecast.p10[i])}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* SUB-VIEW 2: MSME Priority Allocator */}
                      {extendedTab === "msme_priority" && (() => {
                        const totalSelected = apInvoices
                          .filter(inv => selectedInvoices[inv.id])
                          .reduce((sum, inv) => sum + inv.amount, 0);
                        
                        const postPayoutCash = Math.max(0, forecast.starting_cash - totalSelected);
                        
                        const calcMSMEInterestRate = rbiRate * 3;

                        const taxSaved = apInvoices
                          .filter(inv => selectedInvoices[inv.id] && inv.type.startsWith("MSME"))
                          .reduce((sum, inv) => sum + (inv.amount * 0.30), 0);
                        
                        const interestSaved = apInvoices
                          .filter(inv => selectedInvoices[inv.id] && inv.type.startsWith("MSME"))
                          .reduce((sum, inv) => sum + (inv.amount * (calcMSMEInterestRate / 100) / 12), 0);
                        
                        const burn = forecast.monthly_burn || 150000;
                        const postPayoutRunway = Math.round((postPayoutCash / burn) * 10) / 10;

                        const handleAutoOptimize = () => {
                          const sorted = [...apInvoices].sort((a, b) => {
                            const isAMSME = a.type.startsWith("MSME");
                            const isBMSME = b.type.startsWith("MSME");
                            if (isAMSME && !isBMSME) return -1;
                            if (!isAMSME && isBMSME) return 1;
                            return a.daysLeft - b.daysLeft;
                          });

                          const newSelections: Record<number, boolean> = {};
                          let currentCash = forecast.starting_cash;

                          for (const inv of sorted) {
                            const minReserve = Math.max(450000, burn * 3);
                            if (currentCash - inv.amount >= minReserve) {
                              newSelections[inv.id] = true;
                              currentCash -= inv.amount;
                            } else {
                              newSelections[inv.id] = false;
                            }
                          }
                          setSelectedInvoices(newSelections);
                        };

                        const handleExecutePayments = () => {
                          if (totalSelected === 0) {
                            alert("Please select at least one outstanding invoice to pay!");
                            return;
                          }
                          const newStartingCash = forecast.starting_cash - totalSelected;
                          const paidNames = apInvoices
                            .filter(inv => selectedInvoices[inv.id])
                            .map(inv => inv.vendor)
                            .join(", ");
                          
                          setForecast(prev => ({
                            ...prev,
                            starting_cash: newStartingCash
                          }));

                          setApInvoices(prev => prev.filter(inv => !selectedInvoices[inv.id]));
                          setSelectedInvoices({});
                          
                          alert(`Executed payments for: ${paidNames}.\n\nTreasury Deducted: ${formatRupees(totalSelected)}\nCorporate Tax Restored: ${formatRupees(taxSaved)}\nInterest Saved: ${formatRupees(interestSaved)}/month`);
                        };

                        return (
                          <div className="space-y-6">
                            
                            {/* Allocator Header */}
                            <div className="flex justify-between items-center border-b border-neutral-800 pb-3">
                              <div>
                                <h3 className="text-base font-bold text-white">MSME Payout Priority & Runway Allocator</h3>
                                <p className="text-xs text-neutral-400">Optimize working capital allocations to satisfy Income Tax Section 43B(h) and protect operational runway.</p>
                              </div>
                              
                              <div className="flex space-x-3 items-center">
                                {/* Configurable RBI Rate Input */}
                                <div className="flex items-center space-x-1.5 mr-2">
                                  <span className="text-[10px] text-neutral-400 font-bold uppercase">RBI Rate:</span>
                                  <input 
                                    type="number"
                                    step="0.25"
                                    value={rbiRate}
                                    onChange={(e) => setRbiRate(parseFloat(e.target.value) || 6.75)}
                                    className="bg-black text-white border border-neutral-800 text-xs rounded px-2 py-1 w-14 focus:outline-none font-semibold font-mono"
                                  />
                                  <span className="text-[10px] text-neutral-400 font-bold">%</span>
                                </div>

                                <button 
                                  onClick={handleAutoOptimize}
                                  className="bg-transparent hover:bg-neutral-800 text-[#EAB308] border border-[#EAB308]/40 font-bold text-xs px-4 py-2 rounded-lg transition"
                                >
                                  Auto-Optimize Payouts
                                </button>
                                <button 
                                  onClick={handleExecutePayments}
                                  className="bg-[#EAB308] hover:bg-[#CA8A04] text-[#000000] font-bold text-xs px-4 py-2 rounded-lg transition shadow-md"
                                >
                                  Commit & Execute Payments
                                </button>
                              </div>
                            </div>

                            {/* Allocation Metrics Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                              <div className="bg-black p-4 rounded-xl border border-neutral-800 shadow-sm flex flex-col justify-center">
                                <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">Treasury Balance</span>
                                <h4 className="text-lg font-bold text-neutral-100 mt-1">{formatRupees(forecast.starting_cash)}</h4>
                                <span className="text-[9px] text-neutral-500 mt-0.5">Starting operational cash</span>
                              </div>

                              <div className="bg-black p-4 rounded-xl border border-neutral-800 shadow-sm flex flex-col justify-center">
                                <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">Remaining (Post-Payout)</span>
                                <h4 className={`text-lg font-bold mt-1 ${postPayoutCash < 450000 ? "text-rose-400 animate-pulse" : "text-[#EAB308]"}`}>
                                  {formatRupees(postPayoutCash)}
                                </h4>
                                <span className="text-[9px] text-neutral-500 mt-0.5">Projected treasury level</span>
                              </div>

                              <div className="bg-black p-4 rounded-xl border border-neutral-800 shadow-sm flex flex-col justify-center">
                                <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">Corporate Tax Restored</span>
                                <h4 className="text-lg font-bold text-emerald-400 mt-1">+{formatRupees(taxSaved)}</h4>
                                <span className="text-[9px] text-neutral-500 mt-0.5">30% write-offs saved</span>
                              </div>

                              <div className="bg-black p-4 rounded-xl border border-neutral-800 shadow-sm flex flex-col justify-center">
                                <span className="text-[10px] text-neutral-400 font-bold uppercase tracking-wider">Post-Payout Runway</span>
                                <h4 className={`text-lg font-bold mt-1 ${postPayoutRunway < 3 ? "text-amber-500" : "text-emerald-400"}`}>
                                  {postPayoutRunway} Months
                                </h4>
                                <span className="text-[9px] text-neutral-500 mt-0.5">
                                  {postPayoutRunway < 3 ? "Below 3-month buffer" : "Safe working capital runway"}
                                </span>
                              </div>
                            </div>

                            {/* Interactive Invoices table */}
                            <div className="overflow-x-auto border border-neutral-800 rounded-lg">
                              <table className="min-w-full divide-y divide-neutral-800 text-xs text-left">
                                <thead className="bg-black text-neutral-400 font-bold">
                                  <tr>
                                    <th className="px-4 py-3 w-10 text-center">
                                      <input 
                                        type="checkbox" 
                                        className="h-3.5 w-3.5 text-[#EAB308] focus:ring-[#EAB308] border-neutral-700 rounded"
                                        checked={apInvoices.length > 0 && apInvoices.every(inv => selectedInvoices[inv.id])}
                                        onChange={(e) => {
                                          const checked = e.target.checked;
                                          const newSelections: Record<number, boolean> = {};
                                          apInvoices.forEach(inv => {
                                            newSelections[inv.id] = checked;
                                          });
                                          setSelectedInvoices(newSelections);
                                        }}
                                      />
                                    </th>
                                    <th className="px-4 py-3">Vendor / Supplier</th>
                                    <th className="px-4 py-3">Expense Category</th>
                                    <th className="px-4 py-3 text-right">Invoice Amount</th>
                                    <th className="px-4 py-3">MSME Class</th>
                                    <th className="px-4 py-3">Sec 43B(h) Clock</th>
                                    <th className="px-4 py-3 text-right">Interest ({(calcMSMEInterestRate).toFixed(2)}% p.a.)</th>
                                    <th className="px-4 py-3 text-right">Tax Deduction Risk</th>
                                    <th className="px-4 py-3">Allocation Priority</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-neutral-800 bg-[#171717] text-neutral-300 font-medium">
                                  {apInvoices.length === 0 ? (
                                    <tr>
                                      <td colSpan={9} className="px-4 py-8 text-center text-neutral-500 italic">
                                        All outstanding invoices paid! Compliance risk resolved.
                                      </td>
                                    </tr>
                                  ) : (
                                    apInvoices.map((inv) => {
                                      const isChecked = !!selectedInvoices[inv.id];
                                      const isMSME = inv.type.startsWith("MSME");
                                      const interestCost = isMSME ? (inv.amount * (calcMSMEInterestRate / 100) / 12) : 0;
                                      const taxRisk = isMSME ? (inv.amount * 0.30) : 0;
                                      
                                      let priorityLabel = "LOW (Exempt)";
                                      let priorityStyle = "bg-neutral-800 text-neutral-400 border border-neutral-700";
                                      if (isMSME) {
                                        if (inv.daysLeft <= 15) {
                                          priorityLabel = "CRITICAL (High Risk)";
                                          priorityStyle = "bg-red-950 text-red-400 border border-red-900";
                                        } else {
                                          priorityLabel = "MEDIUM (43B(h))";
                                          priorityStyle = "bg-amber-950 text-amber-500 border border-amber-900";
                                        }
                                      }

                                      return (
                                        <tr key={inv.id} className={`hover:bg-neutral-800/40 ${isChecked ? "bg-neutral-800/20" : ""}`}>
                                          <td className="px-4 py-3 text-center">
                                            <input 
                                              type="checkbox" 
                                              checked={isChecked}
                                              onChange={() => {
                                                setSelectedInvoices(prev => ({
                                                  ...prev,
                                                  [inv.id]: !prev[inv.id]
                                                }));
                                              }}
                                              className="h-3.5 w-3.5 text-[#EAB308] focus:ring-[#EAB308] border-neutral-700 rounded"
                                            />
                                          </td>
                                          <td className="px-4 py-3 font-sans font-bold text-white">{inv.vendor}</td>
                                          <td className="px-4 py-3 text-neutral-400">{inv.category}</td>
                                          <td className="px-4 py-3 text-right font-mono font-bold text-white">{formatRupees(inv.amount)}</td>
                                          <td className="px-4 py-3 font-semibold">{inv.type}</td>
                                          <td className={`px-4 py-3 font-semibold font-mono ${inv.daysLeft <= 15 ? "text-rose-400" : "text-neutral-400"}`}>
                                            {isMSME ? `${inv.daysLeft} days remaining` : "Exempt"}
                                          </td>
                                          <td className="px-4 py-3 text-right font-mono text-rose-400">
                                            {isMSME ? `₹${Math.round(interestCost).toLocaleString()}/mo` : "-"}
                                          </td>
                                          <td className="px-4 py-3 text-right font-mono text-[#F59E0B]">
                                            {isMSME ? `₹${Math.round(taxRisk).toLocaleString()}` : "-"}
                                          </td>
                                          <td className="px-4 py-3">
                                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${priorityStyle}`}>
                                              {priorityLabel}
                                            </span>
                                          </td>
                                        </tr>
                                      );
                                    })
                                  )}
                                </tbody>
                              </table>
                            </div>

                            {/* Alert Box */}
                            <div className="bg-neutral-950/80 border border-neutral-800 rounded-lg p-4 text-xs flex items-start">
                              <Info className="h-4 w-4 mr-2 text-[#EAB308] shrink-0 mt-0.5" />
                              <div className="space-y-1">
                                <span className="text-[#EAB308] font-bold">Why MSME Priority Allocation Matters:</span>
                                <p className="text-neutral-400 leading-relaxed">
                                  Under Section 43B(h), micro-vendors must be settled within the 45-day cycle. Delayed bills cannot be written off as corporate business expenses at tax time (add-back liability risk of 30%), and the startup must legally pay compounding monthly interest at 3x the RBI rate. The allocator helps you prioritize treasury allocations to minimize tax penalties while safeguarding runway duration.
                                </p>
                              </div>
                            </div>

                          </div>
                        );
                      })()}

                    </div>
                  )}

                </div>
              </div>
            )}
          </div>
        )}

      </div>


      {/* Copilot Chatbot Removed */}


    </div>
  );
}
