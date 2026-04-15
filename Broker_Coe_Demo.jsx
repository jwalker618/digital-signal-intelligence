import { useState, useMemo, useCallback, useEffect } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ScatterChart, Scatter, Cell, AreaChart, Area, Legend, ComposedChart, PieChart, Pie } from "recharts";
// ─── Utility functions ───
function orderBy(arr, iteratee, order = "asc") {
  const fn = typeof iteratee === "function" ? iteratee : (o) => o[iteratee];
  return [...arr].sort((a, b) => {
    const va = fn(a), vb = fn(b);
    if (va < vb) return order === "asc" ? -1 : 1;
    if (va > vb) return order === "asc" ? 1 : -1;
    return 0;
  });
}
function groupBy(arr, key) {
  return arr.reduce((acc, item) => {
    const k = typeof key === "function" ? key(item) : item[key];
    (acc[k] = acc[k] || []).push(item);
    return acc;
  }, {});
}
function sampleSize(arr, n, randFn) {
  const shuffled = [...arr];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor((randFn ? randFn() : Math.random()) * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled.slice(0, n);
}

// ─── Seed-based random for reproducibility ───
const seededRandom = (seed) => {
  let s = seed;
  return () => { s = (s * 16807 + 0) % 2147483647; return (s - 1) / 2147483646; };
};

// ─── Synthetic Data Generation ───
const generateData = () => {
  const rand = seededRandom(42);
  const r = (min, max) => min + rand() * (max - min);
  const ri = (min, max) => Math.floor(r(min, max + 1));
  const pick = (arr) => arr[ri(0, arr.length - 1)];

  const regions = ["London Market", "UK Regional", "Europe", "Asia Pacific", "North America", "Middle East"];
  const lobs = ["Property", "Casualty", "Marine", "Energy", "Cyber", "D&O", "PI", "Financial Institutions"];
  const tiers = ["Platinum", "Gold", "Silver", "Bronze"];
  const firstNames = ["Aon", "Marsh", "Willis", "Gallagher", "Howden", "Lockton", "BMS", "Miller", "McGill", "Tysers", "Paragon", "Ed Broking", "Price Forbes", "UIB", "Ardonagh", "Acrisure", "PIB", "Alliant", "AssuredPartners", "Brown & Brown"];
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  // Brokers
  const brokers = Array.from({ length: 80 }, (_, i) => {
    const tier = i < 8 ? "Platinum" : i < 24 ? "Gold" : i < 48 ? "Silver" : "Bronze";
    const baseHitRate = tier === "Platinum" ? r(0.28, 0.38) : tier === "Gold" ? r(0.22, 0.32) : tier === "Silver" ? r(0.15, 0.25) : r(0.10, 0.20);
    const region = pick(regions);
    return {
      id: `BRK-${String(i + 1).padStart(3, "0")}`,
      name: i < 20 ? firstNames[i] : `${pick(["Global","National","Regional","Metro","Pacific","Atlantic","Summit","Crown","Shield","Apex"])} ${pick(["Partners","Group","Broking","Insurance","Risk","Advisory"])}`,
      region,
      tier,
      lobs: sampleSize(lobs, ri(1, 4), rand),
      contact: `broker${i + 1}@example.com`,
      hitRate: baseHitRate,
      lossRatio: r(0.45, 0.85),
      avgPremium: r(50000, 2000000),
      nps: ri(tier === "Platinum" ? 40 : 10, tier === "Platinum" ? 90 : 70),
      isNew: rand() < 0.2,
      monthlyData: months.map((m, mi) => ({
        month: m,
        hitRate: Math.max(0.05, Math.min(0.50, baseHitRate + r(-0.06, 0.06))),
        premium: r(200000, 5000000) * (tier === "Platinum" ? 3 : tier === "Gold" ? 2 : 1),
        quotes: ri(5, 40),
        binds: ri(1, 15),
        lossRatio: r(0.40, 0.90),
      }))
    };
  });

  // Policies
  const policies = Array.from({ length: 2000 }, (_, i) => {
    const broker = pick(brokers);
    const lob = pick(broker.lobs);
    const riskScore = r(20, 100);
    const basePremium = r(10000, 500000) * (riskScore / 50);
    const guardrailBand = lob === "Cyber" ? [0.8, 1.3] : lob === "Energy" ? [0.85, 1.25] : [0.9, 1.2];
    const guardrailMid = (guardrailBand[0] + guardrailBand[1]) / 2;
    const deviation = rand() < 0.08 ? r(1.1, 1.6) : rand() < 0.05 ? r(0.5, 0.85) : r(guardrailBand[0], guardrailBand[1]);
    const premium = basePremium * deviation;
    const limit = premium * r(5, 20);
    const region = broker.region;
    const month = ri(0, 11);

    return {
      id: `POL-${String(i + 1).padStart(5, "0")}`,
      brokerId: broker.id,
      brokerName: broker.name,
      region,
      lob,
      riskScore: Math.round(riskScore),
      premium: Math.round(premium),
      limit: Math.round(limit),
      guardrailLow: guardrailBand[0],
      guardrailHigh: guardrailBand[1],
      deviation: Math.round(deviation * 100) / 100,
      breachesGuardrail: deviation < guardrailBand[0] || deviation > guardrailBand[1],
      severity: deviation > guardrailBand[1] * 1.1 || deviation < guardrailBand[0] * 0.9 ? "red" : (deviation > guardrailBand[1] || deviation < guardrailBand[0]) ? "amber" : "green",
      month,
      monthLabel: months[month],
      client: `Client-${ri(1, 500)}`,
      industry: pick(["Financial Services", "Manufacturing", "Technology", "Healthcare", "Energy", "Retail", "Real Estate", "Transportation", "Telecoms", "Government"]),
    };
  });

  // Survey responses
  const surveys = brokers.map(b => ({
    brokerId: b.id,
    brokerName: b.name,
    nps: b.nps,
    easeOfBusiness: ri(3, 10),
    responseSpeed: ri(2, 10),
    pricingTransparency: ri(3, 10),
    comments: pick([
      "Quick turnaround on quotes, very responsive team",
      "Pricing feels opaque, need more transparency on rate basis",
      "Excellent relationship management, would increase placement",
      "Slow to respond on complex risks, losing deals to competitors",
      "Great appetite for emerging risks, especially cyber",
      "Claims handling needs improvement, too many delays",
      "Competitive on property but not on casualty lines",
      "Would like more capacity on D&O and PI",
      "Strong technical underwriting capability",
      "Need faster indication on large energy accounts",
      "Market-leading on marine hull, keep it up",
      "Struggling with aggregation limits on cat-exposed business",
      "Would welcome more broker events and market updates",
      "Documentation turnaround is too slow",
      "Underwriters are knowledgeable and easy to work with",
    ]),
    quarter: pick(["Q1", "Q2", "Q3", "Q4"]),
  }));

  // Tasks
  const tasks = Array.from({ length: 30 }, (_, i) => ({
    id: `TSK-${String(i + 1).padStart(3, "0")}`,
    title: pick([
      "Review guardrail breach on energy account",
      "Follow up on broker NPS feedback",
      "Remediate pricing deviation - D&O portfolio",
      "Broker tier review - quarterly assessment",
      "Respond to capacity request - cyber programme",
      "Update broker contact information",
      "Schedule broker performance review meeting",
      "Investigate claim escalation from broker",
      "Prepare broker scorecard for QBR",
      "Resolve SLA breach on quote turnaround",
    ]),
    broker: pick(brokers).name,
    status: pick(["open", "open", "in_progress", "in_progress", "resolved"]),
    priority: pick(["high", "high", "medium", "medium", "medium", "low"]),
    created: `2025-${String(ri(1, 12)).padStart(2, "0")}-${String(ri(1, 28)).padStart(2, "0")}`,
    slaHours: pick([24, 48, 72]),
    hoursElapsed: ri(2, 96),
  }));

  return { brokers, policies, surveys, tasks, months, regions, lobs, tiers };
};

// ─── Theme ───
const theme = {
  bg: "#0B0F1A",
  surface: "#111827",
  surfaceAlt: "#1A2236",
  border: "#1E2A3F",
  borderLight: "#2A3A52",
  text: "#E2E8F0",
  textMuted: "#8896AB",
  textDim: "#5A6A80",
  accent: "#3B82F6",
  accentAlt: "#6366F1",
  success: "#10B981",
  warning: "#F59E0B",
  danger: "#EF4444",
  info: "#06B6D4",
  gradientStart: "#3B82F6",
  gradientEnd: "#6366F1",
};

const darkMode = true; // default

// ─── Utility Components ───
const Card = ({ children, style, className = "", onClick }) => (
  <div onClick={onClick} style={{
    background: theme.surface,
    border: `1px solid ${theme.border}`,
    borderRadius: 12,
    padding: 20,
    ...style,
  }} className={className}>
    {children}
  </div>
);

const Badge = ({ label, color }) => (
  <span style={{
    display: "inline-block",
    padding: "2px 10px",
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: 0.5,
    background: `${color}20`,
    color: color,
    border: `1px solid ${color}40`,
  }}>{label}</span>
);

const KPICard = ({ label, value, subtext, trend, color = theme.accent, onClick }) => {
  const trendColor = trend > 0 ? theme.success : trend < 0 ? theme.danger : theme.textMuted;
  const trendArrow = trend > 0 ? "▲" : trend < 0 ? "▼" : "—";
  return (
    <Card onClick={onClick} style={{ cursor: onClick ? "pointer" : "default", flex: 1, minWidth: 180, position: "relative", overflow: "hidden" }}>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, background: `linear-gradient(90deg, ${color}, ${color}80)` }} />
      <div style={{ fontSize: 12, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 1, fontWeight: 600, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: theme.text, fontFamily: "'DM Sans', sans-serif" }}>{value}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 6 }}>
        <span style={{ color: trendColor, fontSize: 12, fontWeight: 600 }}>{trendArrow} {Math.abs(trend)}%</span>
        <span style={{ color: theme.textDim, fontSize: 11 }}>{subtext}</span>
      </div>
    </Card>
  );
};

const Select = ({ options, value, onChange, label, style = {} }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 4, ...style }}>
    {label && <label style={{ fontSize: 11, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 0.8, fontWeight: 600 }}>{label}</label>}
    <select value={value} onChange={e => onChange(e.target.value)} style={{
      background: theme.surfaceAlt,
      color: theme.text,
      border: `1px solid ${theme.border}`,
      borderRadius: 8,
      padding: "8px 12px",
      fontSize: 13,
      outline: "none",
      cursor: "pointer",
      appearance: "none",
      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238896AB' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`,
      backgroundRepeat: "no-repeat",
      backgroundPosition: "right 10px center",
      paddingRight: 30,
    }}>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  </div>
);

const Tab = ({ label, active, onClick }) => (
  <button onClick={onClick} style={{
    background: active ? `linear-gradient(135deg, ${theme.gradientStart}, ${theme.gradientEnd})` : "transparent",
    color: active ? "#fff" : theme.textMuted,
    border: active ? "none" : `1px solid ${theme.border}`,
    borderRadius: 8,
    padding: "8px 16px",
    fontSize: 13,
    fontWeight: active ? 600 : 400,
    cursor: "pointer",
    transition: "all 0.2s ease",
    whiteSpace: "nowrap",
  }}>{label}</button>
);

const Modal = ({ open, onClose, title, children }) => {
  if (!open) return null;
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.7)", backdropFilter: "blur(4px)" }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: theme.surface, border: `1px solid ${theme.border}`, borderRadius: 16, padding: 28, maxWidth: 700, width: "90%", maxHeight: "80vh", overflowY: "auto", position: "relative" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h3 style={{ margin: 0, color: theme.text, fontSize: 18 }}>{title}</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", color: theme.textMuted, fontSize: 20, cursor: "pointer" }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
};

const Toggle = ({ label, value, onChange }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }} onClick={() => onChange(!value)}>
    <div style={{
      width: 36, height: 20, borderRadius: 10, background: value ? theme.accent : theme.borderLight, position: "relative", transition: "0.2s",
    }}>
      <div style={{
        width: 16, height: 16, borderRadius: 8, background: "#fff", position: "absolute", top: 2, left: value ? 18 : 2, transition: "0.2s",
      }} />
    </div>
    <span style={{ fontSize: 12, color: theme.textMuted }}>{label}</span>
  </div>
);

// ─── Charts tooltip style ───
const tooltipStyle = { contentStyle: { background: theme.surfaceAlt, border: `1px solid ${theme.border}`, borderRadius: 8, color: theme.text, fontSize: 12 } };

// ─── Main App ───
export default function App() {
  const data = useMemo(() => generateData(), []);
  const [activeTab, setActiveTab] = useState(0);
  const [regionFilter, setRegionFilter] = useState("All");
  const [lobFilter, setLobFilter] = useState("All");
  const [tierFilter, setTierFilter] = useState("All");
  const [compareMode, setCompareMode] = useState(false);
  const [selectedBrokers, setSelectedBrokers] = useState([]);
  const [brokerModal, setBrokerModal] = useState(null);
  const [guardrailThreshold, setGuardrailThreshold] = useState(1.2);
  const [darkTheme, setDarkTheme] = useState(true);

  const tabs = ["Executive Dashboard", "Broker Performance", "Exposure & Concentration", "Pricing & Guardrails", "Market Perception", "Operational Workflow"];

  // Filtered data
  const filteredPolicies = useMemo(() => data.policies.filter(p =>
    (regionFilter === "All" || p.region === regionFilter) &&
    (lobFilter === "All" || p.lob === lobFilter)
  ), [data, regionFilter, lobFilter]);

  const filteredBrokers = useMemo(() => data.brokers.filter(b =>
    (regionFilter === "All" || b.region === regionFilter) &&
    (tierFilter === "All" || b.tier === tierFilter) &&
    (lobFilter === "All" || b.lobs.includes(lobFilter))
  ), [data, regionFilter, lobFilter, tierFilter]);

  // KPIs
  const totalPremium = useMemo(() => filteredPolicies.reduce((s, p) => s + p.premium, 0), [filteredPolicies]);
  const avgHitRate = useMemo(() => filteredBrokers.length ? (filteredBrokers.reduce((s, b) => s + b.hitRate, 0) / filteredBrokers.length) : 0, [filteredBrokers]);
  const breachPct = useMemo(() => filteredPolicies.length ? (filteredPolicies.filter(p => p.breachesGuardrail).length / filteredPolicies.length * 100) : 0, [filteredPolicies]);
  const avgNPS = useMemo(() => filteredBrokers.length ? Math.round(filteredBrokers.reduce((s, b) => s + b.nps, 0) / filteredBrokers.length) : 0, [filteredBrokers]);
  const totalExposure = useMemo(() => filteredPolicies.reduce((s, p) => s + p.limit, 0), [filteredPolicies]);

  const toggleBrokerCompare = (id) => {
    setSelectedBrokers(prev => prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 3 ? [...prev, id] : prev);
  };

  const regionOpts = [{ value: "All", label: "All Regions" }, ...data.regions.map(r => ({ value: r, label: r }))];
  const lobOpts = [{ value: "All", label: "All Lines" }, ...data.lobs.map(l => ({ value: l, label: l }))];
  const tierOpts = [{ value: "All", label: "All Tiers" }, ...data.tiers.map(t => ({ value: t, label: t }))];

  const tabColors = [theme.accent, theme.info, theme.warning, theme.danger, theme.success, theme.accentAlt];

  return (
    <div style={{
      fontFamily: "'DM Sans', 'Segoe UI', system-ui, sans-serif",
      background: theme.bg,
      color: theme.text,
      minHeight: "100vh",
      padding: 0,
    }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />

      {/* Header */}
      <div style={{
        background: `linear-gradient(135deg, ${theme.surface} 0%, ${theme.surfaceAlt} 100%)`,
        borderBottom: `1px solid ${theme.border}`,
        padding: "16px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 12,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: `linear-gradient(135deg, ${theme.gradientStart}, ${theme.gradientEnd})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontWeight: 700, fontSize: 16, color: "#fff",
          }}>MS</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: theme.text }}>Broker Relations Centre of Excellence</div>
            <div style={{ fontSize: 11, color: theme.textMuted, letterSpacing: 0.5 }}>MITSUI SUMITOMO — DEMO ENVIRONMENT</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <Select options={regionOpts} value={regionFilter} onChange={setRegionFilter} label="Region" />
          <Select options={lobOpts} value={lobFilter} onChange={setLobFilter} label="Line of Business" />
          <Select options={tierOpts} value={tierFilter} onChange={setTierFilter} label="Tier" />
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display: "flex", gap: 6, padding: "12px 24px", overflowX: "auto", borderBottom: `1px solid ${theme.border}`, background: theme.bg }}>
        {tabs.map((t, i) => <Tab key={t} label={t} active={activeTab === i} onClick={() => setActiveTab(i)} />)}
      </div>

      {/* Content */}
      <div style={{ padding: "20px 24px", maxWidth: 1400, margin: "0 auto" }}>

        {/* ═══ EXECUTIVE DASHBOARD ═══ */}
        {activeTab === 0 && (
          <div>
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
              <KPICard label="Hit Ratio" value={`${(avgHitRate * 100).toFixed(1)}%`} trend={2.3} subtext="vs prior month" color={theme.accent} onClick={() => setActiveTab(1)} />
              <KPICard label="Total Exposure" value={`£${(totalExposure / 1e9).toFixed(1)}bn`} trend={-1.2} subtext="vs prior month" color={theme.warning} onClick={() => setActiveTab(2)} />
              <KPICard label="Guardrail Breaches" value={`${breachPct.toFixed(1)}%`} trend={-0.8} subtext="of premiums" color={theme.danger} onClick={() => setActiveTab(3)} />
              <KPICard label="Broker NPS" value={avgNPS} trend={4.1} subtext="vs last quarter" color={theme.success} onClick={() => setActiveTab(4)} />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20 }}>
              <Card>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: theme.text }}>12-Month Trend — Hit Ratio & Premium Volume</div>
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={data.months.map((m, i) => {
                    const monthPols = filteredPolicies.filter(p => p.month === i);
                    const monthBrokers = filteredBrokers;
                    return {
                      month: m,
                      hitRate: (monthBrokers.reduce((s, b) => s + (b.monthlyData[i]?.hitRate || 0), 0) / Math.max(monthBrokers.length, 1) * 100),
                      premium: monthPols.reduce((s, p) => s + p.premium, 0) / 1e6,
                    };
                  })}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                    <XAxis dataKey="month" tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <YAxis yAxisId="left" tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <Tooltip {...tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 11, color: theme.textMuted }} />
                    <Area yAxisId="right" type="monotone" dataKey="premium" fill={`${theme.accent}20`} stroke={theme.accent} name="Premium (£m)" />
                    <Line yAxisId="left" type="monotone" dataKey="hitRate" stroke={theme.success} strokeWidth={2} dot={false} name="Hit Rate (%)" />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>

              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <Card>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: theme.text }}>Top 5 Brokers by Premium</div>
                  {orderBy(filteredBrokers, b => b.monthlyData.reduce((s, m) => s + m.premium, 0), "desc").slice(0, 5).map((b, i) => (
                    <div key={b.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: i < 4 ? `1px solid ${theme.border}` : "none", cursor: "pointer" }} onClick={() => setBrokerModal(b)}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{ width: 22, height: 22, borderRadius: 6, background: `${theme.accent}20`, color: theme.accent, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700 }}>{i + 1}</span>
                        <span style={{ fontSize: 13, color: theme.text }}>{b.name}</span>
                      </div>
                      <span style={{ fontSize: 13, fontFamily: "'JetBrains Mono', monospace", color: theme.textMuted }}>£{(b.monthlyData.reduce((s, m) => s + m.premium, 0) / 1e6).toFixed(1)}m</span>
                    </div>
                  ))}
                </Card>

                <Card style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: theme.text }}>Recent Alerts</div>
                  {[
                    { msg: "Guardrail breach: Energy portfolio +14%", severity: "red" },
                    { msg: "NPS drop: 3 brokers below threshold", severity: "amber" },
                    { msg: "SLA breach: 4 open tasks overdue", severity: "amber" },
                    { msg: "New broker onboarded: Crown Advisory", severity: "green" },
                  ].map((a, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 0", fontSize: 12, color: theme.textMuted }}>
                      <div style={{ width: 8, height: 8, borderRadius: 4, background: a.severity === "red" ? theme.danger : a.severity === "amber" ? theme.warning : theme.success, flexShrink: 0 }} />
                      {a.msg}
                    </div>
                  ))}
                </Card>
              </div>
            </div>
          </div>
        )}

        {/* ═══ BROKER PERFORMANCE ═══ */}
        {activeTab === 1 && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div style={{ fontSize: 16, fontWeight: 600 }}>Broker Performance Leaderboard</div>
              <Toggle label="Compare Mode (select up to 3)" value={compareMode} onChange={setCompareMode} />
            </div>

            {compareMode && selectedBrokers.length >= 2 && (
              <Card style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Broker Comparison</div>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                    <XAxis dataKey="month" type="category" allowDuplicatedCategory={false} tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <YAxis tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <Tooltip {...tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    {selectedBrokers.map((id, i) => {
                      const b = data.brokers.find(x => x.id === id);
                      const colors = [theme.accent, theme.success, theme.warning];
                      return <Line key={id} data={b.monthlyData} dataKey="hitRate" name={b.name} stroke={colors[i]} strokeWidth={2} dot={false} type="monotone" />;
                    })}
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            )}

            <Card style={{ overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: `2px solid ${theme.border}` }}>
                    {compareMode && <th style={{ padding: "10px 8px", textAlign: "left", color: theme.textMuted, fontSize: 11, textTransform: "uppercase" }}></th>}
                    <th style={{ padding: "10px 8px", textAlign: "left", color: theme.textMuted, fontSize: 11, textTransform: "uppercase" }}>Broker</th>
                    <th style={{ padding: "10px 8px", textAlign: "left", color: theme.textMuted, fontSize: 11, textTransform: "uppercase" }}>Tier</th>
                    <th style={{ padding: "10px 8px", textAlign: "left", color: theme.textMuted, fontSize: 11, textTransform: "uppercase" }}>Region</th>
                    <th style={{ padding: "10px 8px", textAlign: "right", color: theme.textMuted, fontSize: 11, textTransform: "uppercase" }}>Hit Rate</th>
                    <th style={{ padding: "10px 8px", textAlign: "right", color: theme.textMuted, fontSize: 11, textTransform: "uppercase" }}>Loss Ratio</th>
                    <th style={{ padding: "10px 8px", textAlign: "right", color: theme.textMuted, fontSize: 11, textTransform: "uppercase" }}>Avg Premium</th>
                    <th style={{ padding: "10px 8px", textAlign: "right", color: theme.textMuted, fontSize: 11, textTransform: "uppercase" }}>NPS</th>
                    <th style={{ padding: "10px 8px", textAlign: "center", color: theme.textMuted, fontSize: 11, textTransform: "uppercase" }}>Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {orderBy(filteredBrokers, "hitRate", "desc").slice(0, 25).map((b) => {
                    const tierColors = { Platinum: theme.accent, Gold: theme.warning, Silver: theme.textMuted, Bronze: "#CD7F32" };
                    return (
                      <tr key={b.id} style={{ borderBottom: `1px solid ${theme.border}`, cursor: "pointer" }} onClick={() => !compareMode && setBrokerModal(b)}>
                        {compareMode && <td style={{ padding: "10px 8px" }}>
                          <input type="checkbox" checked={selectedBrokers.includes(b.id)} onChange={() => toggleBrokerCompare(b.id)} style={{ accentColor: theme.accent }} />
                        </td>}
                        <td style={{ padding: "10px 8px", fontWeight: 500 }}>
                          {b.name} {b.isNew && <Badge label="NEW" color={theme.info} />}
                        </td>
                        <td style={{ padding: "10px 8px" }}><Badge label={b.tier} color={tierColors[b.tier]} /></td>
                        <td style={{ padding: "10px 8px", color: theme.textMuted }}>{b.region}</td>
                        <td style={{ padding: "10px 8px", textAlign: "right", fontFamily: "'JetBrains Mono', monospace" }}>{(b.hitRate * 100).toFixed(1)}%</td>
                        <td style={{ padding: "10px 8px", textAlign: "right", fontFamily: "'JetBrains Mono', monospace", color: b.lossRatio > 0.7 ? theme.danger : theme.text }}>{(b.lossRatio * 100).toFixed(1)}%</td>
                        <td style={{ padding: "10px 8px", textAlign: "right", fontFamily: "'JetBrains Mono', monospace" }}>£{(b.avgPremium / 1000).toFixed(0)}k</td>
                        <td style={{ padding: "10px 8px", textAlign: "right", fontFamily: "'JetBrains Mono', monospace", color: b.nps >= 50 ? theme.success : b.nps >= 30 ? theme.warning : theme.danger }}>{b.nps}</td>
                        <td style={{ padding: "10px 8px", textAlign: "center" }}>
                          <svg width="60" height="20" viewBox="0 0 60 20">
                            <polyline fill="none" stroke={theme.accent} strokeWidth="1.5"
                              points={b.monthlyData.map((m, i) => `${i * 5},${20 - m.hitRate * 50}`).join(" ")} />
                          </svg>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Card>
          </div>
        )}

        {/* ═══ EXPOSURE & CONCENTRATION ═══ */}
        {activeTab === 2 && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
              <Card>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Exposure by Region</div>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={data.regions.map(reg => ({
                    region: reg.split(" ")[0],
                    exposure: filteredPolicies.filter(p => p.region === reg).reduce((s, p) => s + p.limit, 0) / 1e9,
                    premium: filteredPolicies.filter(p => p.region === reg).reduce((s, p) => s + p.premium, 0) / 1e6,
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                    <XAxis dataKey="region" tick={{ fill: theme.textMuted, fontSize: 10 }} />
                    <YAxis tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <Tooltip {...tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="exposure" name="Exposure (£bn)" fill={theme.accent} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="premium" name="Premium (£m)" fill={theme.info} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              <Card>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Exposure by Line of Business</div>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart layout="vertical" data={orderBy(data.lobs.map(lob => ({
                    lob,
                    exposure: filteredPolicies.filter(p => p.lob === lob).reduce((s, p) => s + p.limit, 0) / 1e9,
                  })), "exposure", "desc")}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                    <XAxis type="number" tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <YAxis type="category" dataKey="lob" tick={{ fill: theme.textMuted, fontSize: 11 }} width={100} />
                    <Tooltip {...tooltipStyle} />
                    <Bar dataKey="exposure" name="Exposure (£bn)" fill={theme.warning} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>

            <Card>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Industry Concentration — Top 15 Clients by Exposure</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {(() => {
                  const clientExposure = orderBy(
                    Object.entries(groupBy(filteredPolicies, "client")).map(([client, pols]) => ({
                      client,
                      exposure: pols.reduce((s, p) => s + p.limit, 0),
                      industry: pols[0].industry,
                    })),
                    "exposure", "desc"
                  ).slice(0, 15);
                  const maxExp = clientExposure[0]?.exposure || 1;
                  const industryColors = {
                    "Financial Services": theme.accent, Manufacturing: theme.info, Technology: theme.accentAlt,
                    Healthcare: theme.success, Energy: theme.warning, Retail: "#EC4899",
                    "Real Estate": "#8B5CF6", Transportation: "#F97316", Telecoms: "#06B6D4", Government: "#6B7280"
                  };
                  return clientExposure.map((c) => (
                    <div key={c.client} style={{
                      width: `${Math.max(6, (c.exposure / maxExp) * 100)}%`,
                      minWidth: 60,
                      background: `${industryColors[c.industry] || theme.accent}30`,
                      border: `1px solid ${industryColors[c.industry] || theme.accent}50`,
                      borderRadius: 8,
                      padding: "8px 12px",
                      fontSize: 11,
                    }}>
                      <div style={{ fontWeight: 600, color: theme.text }}>{c.client}</div>
                      <div style={{ color: theme.textMuted }}>£{(c.exposure / 1e6).toFixed(0)}m — {c.industry}</div>
                    </div>
                  ));
                })()}
              </div>
              <div style={{ marginTop: 12, fontSize: 11, color: theme.textDim }}>
                Block size proportional to exposure. Colour indicates industry sector.
              </div>
            </Card>

            {/* Concentration Curve */}
            <Card style={{ marginTop: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Concentration Curve (Lorenz)</div>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={(() => {
                  const sorted = orderBy(filteredPolicies, "limit", "asc");
                  const total = sorted.reduce((s, p) => s + p.limit, 0);
                  let cum = 0;
                  const points = sorted.filter((_, i) => i % 20 === 0).map((p, i, arr) => {
                    cum += sorted.slice(i * 20, (i + 1) * 20).reduce((s, x) => s + x.limit, 0);
                    return { pct: ((i + 1) / arr.length * 100).toFixed(0), cumExposure: (cum / total * 100) };
                  });
                  return points;
                })()}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                  <XAxis dataKey="pct" tick={{ fill: theme.textMuted, fontSize: 11 }} label={{ value: "% of policies", position: "bottom", fill: theme.textMuted, fontSize: 11 }} />
                  <YAxis tick={{ fill: theme.textMuted, fontSize: 11 }} label={{ value: "% of exposure", angle: -90, position: "insideLeft", fill: theme.textMuted, fontSize: 11 }} />
                  <Tooltip {...tooltipStyle} />
                  <Area type="monotone" dataKey="cumExposure" fill={`${theme.warning}30`} stroke={theme.warning} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </div>
        )}

        {/* ═══ PRICING & GUARDRAILS ═══ */}
        {activeTab === 3 && (
          <div>
            <Card style={{ marginBottom: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div style={{ fontSize: 14, fontWeight: 600 }}>Premium Distribution vs Guardrail Bands</div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ fontSize: 12, color: theme.textMuted }}>Guardrail threshold:</span>
                  <input type="range" min="1.0" max="1.5" step="0.05" value={guardrailThreshold}
                    onChange={e => setGuardrailThreshold(parseFloat(e.target.value))}
                    style={{ accentColor: theme.accent, width: 120 }} />
                  <span style={{ fontSize: 13, fontFamily: "'JetBrains Mono', monospace", color: theme.accent, minWidth: 40 }}>{guardrailThreshold.toFixed(2)}</span>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={(() => {
                  const buckets = Array.from({ length: 20 }, (_, i) => ({ range: (0.5 + i * 0.05).toFixed(2), count: 0, breach: 0 }));
                  filteredPolicies.forEach(p => {
                    const idx = Math.min(19, Math.max(0, Math.floor((p.deviation - 0.5) / 0.05)));
                    buckets[idx].count++;
                    if (p.deviation > guardrailThreshold || p.deviation < (2 - guardrailThreshold)) buckets[idx].breach++;
                  });
                  return buckets;
                })()}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                  <XAxis dataKey="range" tick={{ fill: theme.textMuted, fontSize: 10 }} />
                  <YAxis tick={{ fill: theme.textMuted, fontSize: 11 }} />
                  <Tooltip {...tooltipStyle} />
                  <Bar dataKey="count" name="All policies" fill={theme.accent} radius={[3, 3, 0, 0]} />
                  <Bar dataKey="breach" name="Breaching" fill={theme.danger} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <div style={{ textAlign: "center", fontSize: 11, color: theme.textMuted, marginTop: 8 }}>
                Drag the slider to adjust the guardrail threshold and see how breach counts change — {filteredPolicies.filter(p => p.deviation > guardrailThreshold).length} policies currently exceed the {guardrailThreshold.toFixed(2)} threshold
              </div>
            </Card>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
              <Card>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Premium vs Risk Score</div>
                <ResponsiveContainer width="100%" height={280}>
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                    <XAxis dataKey="riskScore" name="Risk Score" tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <YAxis dataKey="premium" name="Premium" tick={{ fill: theme.textMuted, fontSize: 11 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                    <Tooltip {...tooltipStyle} />
                    <Scatter data={filteredPolicies.slice(0, 400)} fill={theme.accent}>
                      {filteredPolicies.slice(0, 400).map((p, i) => (
                        <Cell key={i} fill={p.severity === "red" ? theme.danger : p.severity === "amber" ? theme.warning : `${theme.accent}80`} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
                <div style={{ display: "flex", gap: 16, justifyContent: "center", marginTop: 8 }}>
                  <span style={{ fontSize: 11, color: theme.textMuted }}>● <span style={{ color: theme.success }}>Within band</span></span>
                  <span style={{ fontSize: 11, color: theme.textMuted }}>● <span style={{ color: theme.warning }}>Amber (5-10% over)</span></span>
                  <span style={{ fontSize: 11, color: theme.textMuted }}>● <span style={{ color: theme.danger }}>Red (&gt;10% over)</span></span>
                </div>
              </Card>

              <Card>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Guardrail Breaches by Line of Business</div>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart layout="vertical" data={orderBy(data.lobs.map(lob => {
                    const lobPols = filteredPolicies.filter(p => p.lob === lob);
                    return {
                      lob,
                      amberPct: lobPols.length ? (lobPols.filter(p => p.severity === "amber").length / lobPols.length * 100) : 0,
                      redPct: lobPols.length ? (lobPols.filter(p => p.severity === "red").length / lobPols.length * 100) : 0,
                    };
                  }), l => l.amberPct + l.redPct, "desc")}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                    <XAxis type="number" tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <YAxis type="category" dataKey="lob" tick={{ fill: theme.textMuted, fontSize: 11 }} width={100} />
                    <Tooltip {...tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="amberPct" name="Amber %" stackId="a" fill={theme.warning} radius={[0, 0, 0, 0]} />
                    <Bar dataKey="redPct" name="Red %" stackId="a" fill={theme.danger} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </div>
        )}

        {/* ═══ MARKET PERCEPTION ═══ */}
        {activeTab === 4 && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20, marginBottom: 20 }}>
              <Card style={{ textAlign: "center" }}>
                <div style={{ fontSize: 12, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>Net Promoter Score</div>
                <div style={{ position: "relative", width: 160, height: 80, margin: "0 auto" }}>
                  <svg viewBox="0 0 160 80" width="160" height="80">
                    <path d="M 10 75 A 70 70 0 0 1 150 75" fill="none" stroke={theme.border} strokeWidth="12" strokeLinecap="round" />
                    <path d="M 10 75 A 70 70 0 0 1 150 75" fill="none" stroke={`url(#npsGrad)`} strokeWidth="12" strokeLinecap="round"
                      strokeDasharray={`${(avgNPS + 100) / 200 * 220} 220`} />
                    <defs>
                      <linearGradient id="npsGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor={theme.danger} />
                        <stop offset="50%" stopColor={theme.warning} />
                        <stop offset="100%" stopColor={theme.success} />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div style={{ position: "absolute", bottom: 0, left: "50%", transform: "translateX(-50%)", fontSize: 28, fontWeight: 700, color: theme.text }}>{avgNPS}</div>
                </div>
              </Card>

              <Card style={{ textAlign: "center" }}>
                <div style={{ fontSize: 12, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>Preferred Partner %</div>
                <div style={{ fontSize: 36, fontWeight: 700, color: theme.success }}>{(filteredBrokers.filter(b => b.nps >= 50).length / Math.max(filteredBrokers.length, 1) * 100).toFixed(0)}%</div>
                <div style={{ fontSize: 12, color: theme.textMuted, marginTop: 4 }}>{filteredBrokers.filter(b => b.nps >= 50).length} of {filteredBrokers.length} brokers</div>
              </Card>

              <Card style={{ textAlign: "center" }}>
                <div style={{ fontSize: 12, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>Avg Friction Score</div>
                <div style={{ fontSize: 36, fontWeight: 700, color: theme.warning }}>
                  {(10 - (data.surveys.reduce((s, sv) => s + sv.easeOfBusiness, 0) / Math.max(data.surveys.length, 1))).toFixed(1)}
                </div>
                <div style={{ fontSize: 12, color: theme.textMuted, marginTop: 4 }}>Lower is better (0-10 scale)</div>
              </Card>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
              <Card>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>NPS Distribution</div>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={(() => {
                    const buckets = [
                      { range: "Detractors (0-6)", count: 0, fill: theme.danger },
                      { range: "Passives (7-8)", count: 0, fill: theme.warning },
                      { range: "Promoters (9-10)", count: 0, fill: theme.success },
                    ];
                    data.surveys.forEach(s => {
                      const scaled = Math.round(s.nps / 10);
                      if (scaled <= 6) buckets[0].count++;
                      else if (scaled <= 8) buckets[1].count++;
                      else buckets[2].count++;
                    });
                    return buckets;
                  })()}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                    <XAxis dataKey="range" tick={{ fill: theme.textMuted, fontSize: 10 }} />
                    <YAxis tick={{ fill: theme.textMuted, fontSize: 11 }} />
                    <Tooltip {...tooltipStyle} />
                    <Bar dataKey="count" name="Brokers" radius={[6, 6, 0, 0]}>
                      {[theme.danger, theme.warning, theme.success].map((c, i) => <Cell key={i} fill={c} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              <Card>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Broker Verbatim Comments</div>
                <div style={{ maxHeight: 250, overflowY: "auto" }}>
                  {data.surveys.slice(0, 12).map((s, i) => (
                    <div key={i} style={{ padding: "10px 0", borderBottom: `1px solid ${theme.border}`, fontSize: 12 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, color: theme.text }}>{s.brokerName}</span>
                        <Badge label={`NPS ${s.nps}`} color={s.nps >= 50 ? theme.success : s.nps >= 30 ? theme.warning : theme.danger} />
                      </div>
                      <div style={{ color: theme.textMuted, fontStyle: "italic" }}>"{s.comments}"</div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Word cloud simulation */}
            <Card style={{ marginTop: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Keyword Themes from Broker Feedback</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", padding: "10px 0" }}>
                {[
                  { word: "responsive", size: 28, color: theme.success },
                  { word: "pricing", size: 24, color: theme.warning },
                  { word: "capacity", size: 22, color: theme.accent },
                  { word: "claims", size: 20, color: theme.danger },
                  { word: "turnaround", size: 26, color: theme.info },
                  { word: "competitive", size: 18, color: theme.success },
                  { word: "transparency", size: 22, color: theme.warning },
                  { word: "technical", size: 16, color: theme.accent },
                  { word: "relationship", size: 24, color: theme.success },
                  { word: "delays", size: 18, color: theme.danger },
                  { word: "cyber", size: 20, color: theme.accentAlt },
                  { word: "documentation", size: 16, color: theme.warning },
                  { word: "events", size: 14, color: theme.info },
                  { word: "appetite", size: 20, color: theme.success },
                  { word: "slow", size: 16, color: theme.danger },
                ].map((w, i) => (
                  <span key={i} style={{ fontSize: w.size, fontWeight: 600, color: w.color, opacity: 0.85, padding: "2px 6px" }}>{w.word}</span>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* ═══ OPERATIONAL WORKFLOW ═══ */}
        {activeTab === 5 && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 20 }}>
              <KPICard label="Open Issues" value={data.tasks.filter(t => t.status === "open").length} trend={-2} subtext="vs last week" color={theme.danger} />
              <KPICard label="Avg Response Time" value="34h" trend={-8} subtext="improving" color={theme.success} />
              <KPICard label="SLA Compliance" value="78%" trend={5} subtext="vs target 90%" color={theme.warning} />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
              {["open", "in_progress", "resolved"].map(status => {
                const statusLabel = { open: "Open", in_progress: "In Progress", resolved: "Resolved" }[status];
                const statusColor = { open: theme.danger, in_progress: theme.warning, resolved: theme.success }[status];
                const tasks = data.tasks.filter(t => t.status === status);
                return (
                  <div key={status}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12, padding: "8px 12px", background: `${statusColor}15`, borderRadius: 8, border: `1px solid ${statusColor}30` }}>
                      <div style={{ width: 10, height: 10, borderRadius: 5, background: statusColor }} />
                      <span style={{ fontSize: 13, fontWeight: 600, color: statusColor }}>{statusLabel}</span>
                      <span style={{ fontSize: 12, color: theme.textMuted, marginLeft: "auto" }}>{tasks.length}</span>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {tasks.map(t => {
                        const overdue = t.hoursElapsed > t.slaHours && t.status !== "resolved";
                        return (
                          <Card key={t.id} style={{ padding: 14, borderLeft: `3px solid ${overdue ? theme.danger : statusColor}` }}>
                            <div style={{ fontSize: 12, fontWeight: 600, color: theme.text, marginBottom: 6 }}>{t.title}</div>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <span style={{ fontSize: 11, color: theme.textMuted }}>{t.broker}</span>
                              <Badge label={t.priority.toUpperCase()} color={t.priority === "high" ? theme.danger : t.priority === "medium" ? theme.warning : theme.textMuted} />
                            </div>
                            {overdue && <div style={{ fontSize: 10, color: theme.danger, marginTop: 4, fontWeight: 600 }}>⚠ SLA breached — {t.hoursElapsed - t.slaHours}h overdue</div>}
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Minimal message composer */}
            <Card style={{ marginTop: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Quick Message Composer</div>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <select style={{ flex: 1, minWidth: 200, background: theme.surfaceAlt, color: theme.text, border: `1px solid ${theme.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 13 }}>
                  <option>Select broker...</option>
                  {data.brokers.slice(0, 20).map(b => <option key={b.id}>{b.name}</option>)}
                </select>
                <select style={{ flex: 1, minWidth: 200, background: theme.surfaceAlt, color: theme.text, border: `1px solid ${theme.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 13 }}>
                  <option>Select template...</option>
                  <option>Guardrail breach notification</option>
                  <option>Performance review invitation</option>
                  <option>Capacity update</option>
                  <option>NPS follow-up</option>
                </select>
                <button style={{
                  background: `linear-gradient(135deg, ${theme.gradientStart}, ${theme.gradientEnd})`,
                  color: "#fff", border: "none", borderRadius: 8, padding: "8px 20px", fontSize: 13, fontWeight: 600, cursor: "pointer",
                }}>Send</button>
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* ═══ BROKER MODAL ═══ */}
      <Modal open={!!brokerModal} onClose={() => setBrokerModal(null)} title={brokerModal?.name}>
        {brokerModal && (
          <div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 20 }}>
              <Badge label={brokerModal.tier} color={theme.accent} />
              <Badge label={brokerModal.region} color={theme.info} />
              {brokerModal.isNew && <Badge label="NEW" color={theme.success} />}
              {brokerModal.lobs.map(l => <Badge key={l} label={l} color={theme.textMuted} />)}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 12, marginBottom: 20 }}>
              {[
                { label: "Hit Rate", value: `${(brokerModal.hitRate * 100).toFixed(1)}%` },
                { label: "Loss Ratio", value: `${(brokerModal.lossRatio * 100).toFixed(1)}%` },
                { label: "Avg Premium", value: `£${(brokerModal.avgPremium / 1000).toFixed(0)}k` },
                { label: "NPS", value: brokerModal.nps },
              ].map(k => (
                <div key={k.label} style={{ background: theme.surfaceAlt, borderRadius: 8, padding: 12, textAlign: "center" }}>
                  <div style={{ fontSize: 11, color: theme.textMuted, marginBottom: 4 }}>{k.label}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: theme.text }}>{k.value}</div>
                </div>
              ))}
            </div>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: theme.text }}>Monthly Performance</div>
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={brokerModal.monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.border} />
                <XAxis dataKey="month" tick={{ fill: theme.textMuted, fontSize: 10 }} />
                <YAxis tick={{ fill: theme.textMuted, fontSize: 10 }} />
                <Tooltip {...tooltipStyle} />
                <Line type="monotone" dataKey="hitRate" stroke={theme.accent} strokeWidth={2} dot={false} name="Hit Rate" />
                <Line type="monotone" dataKey="lossRatio" stroke={theme.danger} strokeWidth={2} dot={false} name="Loss Ratio" />
              </LineChart>
            </ResponsiveContainer>
            <div style={{ marginTop: 16, fontSize: 12, color: theme.textMuted }}>
              Contact: {brokerModal.contact}
            </div>
          </div>
        )}
      </Modal>

      {/* Footer */}
      <div style={{ textAlign: "center", padding: "24px 0", fontSize: 11, color: theme.textDim, borderTop: `1px solid ${theme.border}`, marginTop: 40 }}>
        Mitsui Sumitomo — Broker Relations Centre of Excellence — Demo Environment — Synthetic Data Only
      </div>
    </div>
  );
}
