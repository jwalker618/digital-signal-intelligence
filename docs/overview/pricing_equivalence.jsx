import { useState, useEffect } from "react";

// ─── DESIGN TOKENS ──────────────────────────────────────────────────
const C = {
  bg: "#faf8f5",
  surface: "#ffffff",
  surfaceAlt: "#f5f2ee",
  border: "#e8e3db",
  borderStrong: "#d4cec4",
  ink: "#1a1714",
  inkDim: "#5c564d",
  inkMuted: "#8a8279",
  accent: "#c45d3e",
  accentDim: "rgba(196,93,62,0.08)",
  accentLight: "rgba(196,93,62,0.15)",
  trad: "#6b7b3a",
  tradBg: "rgba(107,123,58,0.06)",
  tradBorder: "rgba(107,123,58,0.2)",
  dsi: "#3a6b7b",
  dsiBg: "rgba(58,107,123,0.06)",
  dsiBorder: "rgba(58,107,123,0.2)",
  equal: "#8b6914",
  equalBg: "rgba(139,105,20,0.08)",
};

const serif = `'Libre Baskerville', 'Georgia', serif`;
const sans = `'DM Sans', 'Helvetica Neue', sans-serif`;
const mono = `'JetBrains Mono', 'Fira Code', monospace`;

// ─── WORKED EXAMPLE DATA ────────────────────────────────────────────
// A fictional mid-market manufacturing company. Same entity, priced both ways.

const ENTITY = {
  name: "Hargrove Industrial Group",
  desc: "Diversified manufacturer — plastics, packaging, precision components",
  revenue: 280_000_000,
  employees: 1850,
  locations: 6,
};

// Traditional: SOV with per-asset rates
const SOV_ASSETS = [
  { id: 1, name: "HQ & Admin — Charlotte, NC", construction: "Fire Resistive", occupancy: "Office", tiv: 18_500_000, rate: 0.00042, protection: "Sprinklered" },
  { id: 2, name: "Plant 1 — Plastics Extrusion, Gastonia, NC", construction: "Non-Combustible", occupancy: "Manufacturing — Moderate", tiv: 65_000_000, rate: 0.00095, protection: "Sprinklered" },
  { id: 3, name: "Plant 2 — Packaging, Greenville, SC", construction: "Non-Combustible", occupancy: "Manufacturing — Light", tiv: 42_000_000, rate: 0.00078, protection: "Sprinklered" },
  { id: 4, name: "Plant 3 — Precision Components, Roanoke, VA", construction: "Fire Resistive", occupancy: "Manufacturing — Light", tiv: 55_000_000, rate: 0.00072, protection: "Sprinklered" },
  { id: 5, name: "Warehouse — Distribution, Spartanburg, SC", construction: "Metal Frame", occupancy: "Storage — Moderate", tiv: 28_000_000, rate: 0.00088, protection: "Partial Sprinkler" },
  { id: 6, name: "R&D Lab — Charlotte, NC", construction: "Fire Resistive", occupancy: "Lab/Light Industrial", tiv: 15_000_000, rate: 0.00055, protection: "Sprinklered" },
];

const tradTotal = SOV_ASSETS.reduce((s, a) => s + a.tiv, 0);
const tradPremiums = SOV_ASSETS.map(a => ({ ...a, premium: a.tiv * a.rate }));
const tradBasePremium = tradPremiums.reduce((s, a) => s + a.premium, 0);

// Traditional modifiers (applied after asset-level sum)
const TRAD_MODS = [
  { name: "Experience modifier", value: 0.95, rationale: "Favourable loss history" },
  { name: "Schedule credit", value: 0.90, rationale: "Underwriter discretion — 'good account'" },
  { name: "Market adjustment", value: 1.05, rationale: "Hardening market conditions" },
];
const tradModProduct = TRAD_MODS.reduce((p, m) => p * m.value, 1);
const tradFinalPremium = tradBasePremium * tradModProduct;

// Weighted average rate (what the UW actually applied in aggregate)
const tradWeightedRate = tradBasePremium / tradTotal;

// DSI approach: same entity
const DSI_SIGNALS = [
  { cat: "Technical Infrastructure", score: 74, detail: "Mixed OT/IT, legacy SCADA in Plant 1, modern elsewhere" },
  { cat: "Network Authority", score: 82, detail: "ISO 9001/14001 certified, Tier-1 supply chain partners" },
  { cat: "Corporate Footprint", score: 78, detail: "6 locations, 3 states, moderate complexity" },
  { cat: "Behavioural", score: 71, detail: "OSHA incident rate declining, active safety investment" },
  { cat: "Public Records", score: 85, detail: "No material litigation, 1 minor EPA action (resolved)" },
  { cat: "Structured Data", score: 68, detail: "AM Best rated suppliers, no credit watch" },
];

const DSI_COMPOSITE = 742;
const DSI_TIER = 2;
const DSI_BASE_RATE = 0.00075; // rate per $ of signal-inferred TIV
const DSI_EXPOSURE_BAND = "$150M–$300M";
const DSI_EXPOSURE_MIDPOINT = 225_000_000; // midpoint of inferred band
const DSI_CONFIDENCE = 0.79;

const DSI_MODS = [
  { name: "Exposure Size", value: 0.94, source: "Scale credit (6 locations, diversified)" },
  { name: "Loss Propensity", value: 0.92, source: "Behavioural: declining incident rate, safety investment" },
  { name: "Complexity", value: 1.08, source: "Multi-state, mixed occupancy, OT/IT convergence" },
];
const dsiModProduct = DSI_MODS.reduce((p, m) => p * m.value, 1);
const dsiBasePremium = DSI_EXPOSURE_MIDPOINT * DSI_BASE_RATE;
const dsiFinalPremium = dsiBasePremium * dsiModProduct;

// For the "what the UW really did" analysis
const assetRates = SOV_ASSETS.map(a => a.rate * 10000); // in bps
const rateMin = Math.min(...assetRates);
const rateMax = Math.max(...assetRates);
const rateSpread = rateMax - rateMin;
const rateWeightedAvg = tradWeightedRate * 10000;

const fmt = (n) => n.toLocaleString("en-US", { maximumFractionDigits: 0 });
const fmtPct = (n) => (n * 100).toFixed(2) + "%";
const fmtBps = (n) => n.toFixed(1) + " bps";

// ─── SECTIONS ───────────────────────────────────────────────────────
const SECTIONS = [
  { id: "thesis", label: "The Argument" },
  { id: "trad", label: "Traditional Method" },
  { id: "dsi", label: "DSI Method" },
  { id: "compare", label: "Side-by-Side" },
  { id: "illusion", label: "The Precision Illusion" },
  { id: "conclusion", label: "Conclusion" },
];

// ─── COMPONENTS ─────────────────────────────────────────────────────
const Tag = ({ children, color = C.accent }) => (
  <span style={{
    display: "inline-block", padding: "3px 10px", borderRadius: 3,
    fontSize: 10, fontFamily: mono, fontWeight: 600, letterSpacing: "0.06em",
    color, background: color === C.trad ? C.tradBg : color === C.dsi ? C.dsiBg : C.accentDim,
    border: `1px solid ${color === C.trad ? C.tradBorder : color === C.dsi ? C.dsiBorder : "transparent"}`,
    textTransform: "uppercase",
  }}>{children}</span>
);

const Divider = () => <div style={{ height: 1, background: C.border, margin: "24px 0" }} />;

const Prose = ({ children }) => (
  <p style={{ fontFamily: serif, fontSize: 15, color: C.ink, lineHeight: 1.75, margin: "0 0 16px", maxWidth: 640 }}>
    {children}
  </p>
);

const Emphasis = ({ children }) => (
  <span style={{ color: C.accent, fontWeight: 600 }}>{children}</span>
);

const MathBlock = ({ children }) => (
  <div style={{
    fontFamily: mono, fontSize: 13, color: C.ink, padding: "16px 20px",
    background: C.surfaceAlt, border: `1px solid ${C.border}`, borderRadius: 6,
    margin: "16px 0", lineHeight: 1.8, overflowX: "auto", whiteSpace: "pre-wrap",
  }}>{children}</div>
);

const AssetRow = ({ asset, showPremium, highlight }) => (
  <div style={{
    display: "grid", gridTemplateColumns: "2fr 1fr 1fr 0.8fr 1fr",
    gap: 8, padding: "10px 12px", fontSize: 12, fontFamily: sans,
    background: highlight ? C.tradBg : "transparent",
    borderBottom: `1px solid ${C.border}`, alignItems: "center",
  }}>
    <div>
      <div style={{ fontWeight: 600, color: C.ink, fontSize: 12 }}>{asset.name}</div>
      <div style={{ color: C.inkMuted, fontSize: 10, marginTop: 2 }}>{asset.construction} · {asset.occupancy}</div>
    </div>
    <div style={{ fontFamily: mono, color: C.ink, textAlign: "right" }}>${fmt(asset.tiv)}</div>
    <div style={{ fontFamily: mono, color: C.trad, textAlign: "right" }}>{fmtBps(asset.rate * 10000)}</div>
    <div style={{ color: C.inkMuted, textAlign: "center", fontSize: 11 }}>{asset.protection}</div>
    {showPremium && (
      <div style={{ fontFamily: mono, color: C.ink, textAlign: "right", fontWeight: 600 }}>
        ${fmt(asset.premium)}
      </div>
    )}
  </div>
);

const RateBar = ({ label, bps, maxBps, color, isAvg }) => {
  const pct = (bps / maxBps) * 100;
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
        <span style={{ fontFamily: sans, fontSize: 11, color: isAvg ? C.accent : C.inkDim,
          fontWeight: isAvg ? 700 : 400 }}>{label}</span>
        <span style={{ fontFamily: mono, fontSize: 11, color: isAvg ? C.accent : C.inkDim,
          fontWeight: isAvg ? 700 : 400 }}>{fmtBps(bps)}</span>
      </div>
      <div style={{ height: isAvg ? 6 : 4, borderRadius: 3, background: C.border }}>
        <div style={{
          height: "100%", borderRadius: 3, width: `${pct}%`,
          background: isAvg ? C.accent : color,
          transition: "width 0.5s ease",
        }} />
      </div>
    </div>
  );
};

// ─── MAIN ───────────────────────────────────────────────────────────
export default function PricingEquivalence() {
  const [section, setSection] = useState(0);
  const [showPremiums, setShowPremiums] = useState(false);
  const [showMods, setShowMods] = useState(false);

  useEffect(() => {
    setShowPremiums(false);
    setShowMods(false);
  }, [section]);

  const sec = SECTIONS[section];
  const diff = Math.abs(tradFinalPremium - dsiFinalPremium);
  const diffPct = (diff / tradFinalPremium * 100);

  return (
    <div style={{ fontFamily: sans, background: C.bg, color: C.ink, minHeight: "100vh" }}>
      {/* ── HEADER ── */}
      <div style={{ padding: "36px 32px 28px", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ fontFamily: mono, fontSize: 10, color: C.inkMuted, letterSpacing: "0.1em",
          textTransform: "uppercase", marginBottom: 8 }}>Pricing Methodology Comparison</div>
        <h1 style={{
          fontFamily: serif, fontSize: 28, fontWeight: 400, color: C.ink,
          lineHeight: 1.2, margin: "0 0 8px", letterSpacing: "-0.01em", maxWidth: 520,
        }}>
          The Precision Illusion
        </h1>
        <p style={{ fontFamily: sans, fontSize: 14, color: C.inkDim, margin: 0, maxWidth: 540, lineHeight: 1.5 }}>
          Why asset-level granularity in traditional pricing doesn't produce more accurate premiums
          than organisational-level signal assessment — and costs orders of magnitude more.
        </p>
      </div>

      {/* ── NAV ── */}
      <div style={{
        padding: "0 32px", borderBottom: `1px solid ${C.border}`, background: C.surface,
        overflowX: "auto", whiteSpace: "nowrap", WebkitOverflowScrolling: "touch",
      }}>
        {SECTIONS.map((s, i) => (
          <button key={s.id} onClick={() => setSection(i)}
            style={{
              fontFamily: sans, fontSize: 12, fontWeight: section === i ? 600 : 400,
              padding: "14px 16px", border: "none", cursor: "pointer", background: "transparent",
              color: section === i ? C.accent : C.inkMuted,
              borderBottom: section === i ? `2px solid ${C.accent}` : "2px solid transparent",
              transition: "all 0.2s", display: "inline-block",
            }}>
            {s.label}
          </button>
        ))}
      </div>

      {/* ── ENTITY BANNER ── */}
      <div style={{ padding: "14px 32px", background: C.surfaceAlt, borderBottom: `1px solid ${C.border}`,
        display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
        <span style={{ fontFamily: serif, fontSize: 14, fontWeight: 600, color: C.ink }}>{ENTITY.name}</span>
        <span style={{ fontFamily: sans, fontSize: 11, color: C.inkMuted }}>
          {ENTITY.desc} · ${fmt(ENTITY.revenue)} revenue · {fmt(ENTITY.employees)} employees · {ENTITY.locations} locations
        </span>
      </div>

      {/* ── CONTENT ── */}
      <div style={{ padding: "28px 32px", maxWidth: 760, margin: "0 auto" }}>

        {/* ═══ THESIS ═══ */}
        {section === 0 && (
          <div>
            <Prose>
              All property and casualty pricing, regardless of methodology, reduces to the same 
              fundamental operation: <Emphasis>apply a rate to an exposure basis, then adjust for 
              modifying factors</Emphasis>.
            </Prose>
            <MathBlock>
              Premium = Exposure × Rate × Modifiers
            </MathBlock>
            <Prose>
              The traditional model and DSI differ not in this formula — they share it — but in 
              <Emphasis> where the inputs come from</Emphasis> and <Emphasis>at what level of 
              aggregation</Emphasis> they're applied.
            </Prose>
            <Divider />
            <Prose>
              Traditional underwriting gathers a Statement of Values — a schedule of individual 
              assets with declared replacement costs — and applies rates per asset based on 
              construction, occupancy, protection, and location. The rates themselves are selected 
              by the underwriter from experience, reference tables, and judgement. The sum of these 
              individual asset premiums, modified by experience and market factors, produces the 
              final price.
            </Prose>
            <Prose>
              DSI assesses the <Emphasis>organisation</Emphasis> — not its individual assets — 
              through observable digital signals. It produces a composite risk score, maps it to a 
              tier, selects a base rate, and applies it to a signal-inferred exposure basis. 
              Modifiers for risk quality, loss propensity, and exposure complexity adjust the final 
              premium deterministically.
            </Prose>
            <Divider />
            <div style={{
              padding: "20px 24px", background: C.equalBg, border: `1px solid ${C.equal}`,
              borderRadius: 6, marginTop: 8,
            }}>
              <div style={{ fontFamily: mono, fontSize: 10, color: C.equal, textTransform: "uppercase",
                letterSpacing: "0.08em", marginBottom: 8 }}>Core Thesis</div>
              <p style={{ fontFamily: serif, fontSize: 15, color: C.ink, lineHeight: 1.7, margin: 0 }}>
                The asset-level granularity in traditional pricing creates an <em>appearance</em> of 
                precision without delivering superior predictive accuracy. The underwriter's per-asset 
                rates cluster around an organisational judgement they've already made. DSI makes that 
                organisational judgement explicit, observable, and repeatable — at a fraction of the 
                cost and time.
              </p>
            </div>
          </div>
        )}

        {/* ═══ TRADITIONAL ═══ */}
        {section === 1 && (
          <div>
            <Tag color={C.trad}>Traditional Method</Tag>
            <h2 style={{ fontFamily: serif, fontSize: 20, fontWeight: 400, color: C.ink, margin: "16px 0 12px" }}>
              Asset-Level Rating from Statement of Values
            </h2>
            <Prose>
              The underwriter receives a six-location SOV from the broker. Each asset has a declared 
              Total Insurable Value (TIV), construction type, occupancy class, and protection grade. 
              The underwriter applies a rate per asset based on their assessment of each location's 
              risk characteristics.
            </Prose>

            {/* SOV Table */}
            <div style={{ border: `1px solid ${C.border}`, borderRadius: 6, overflow: "hidden", marginBottom: 16 }}>
              <div style={{
                display: "grid", gridTemplateColumns: "2fr 1fr 1fr 0.8fr 1fr",
                gap: 8, padding: "10px 12px", fontSize: 10, fontFamily: mono,
                color: C.inkMuted, background: C.surfaceAlt, borderBottom: `1px solid ${C.border}`,
                textTransform: "uppercase", letterSpacing: "0.06em",
              }}>
                <span>Location</span><span style={{ textAlign: "right" }}>TIV</span>
                <span style={{ textAlign: "right" }}>Rate (bps)</span>
                <span style={{ textAlign: "center" }}>Protection</span>
                {showPremiums && <span style={{ textAlign: "right" }}>Premium</span>}
              </div>
              {tradPremiums.map((a, i) => (
                <AssetRow key={a.id} asset={a} showPremium={showPremiums}
                  highlight={a.rate === Math.max(...SOV_ASSETS.map(x => x.rate))} />
              ))}
              <div style={{
                display: "grid", gridTemplateColumns: "2fr 1fr 1fr 0.8fr 1fr",
                gap: 8, padding: "12px 12px", fontSize: 12, fontFamily: mono,
                fontWeight: 700, background: C.surfaceAlt, borderTop: `1px solid ${C.borderStrong}`,
              }}>
                <span>Total</span>
                <span style={{ textAlign: "right" }}>${fmt(tradTotal)}</span>
                <span style={{ textAlign: "right", color: C.accent }}>{fmtBps(rateWeightedAvg)}</span>
                <span></span>
                {showPremiums && <span style={{ textAlign: "right" }}>${fmt(tradBasePremium)}</span>}
              </div>
            </div>

            {!showPremiums && (
              <button onClick={() => setShowPremiums(true)} style={{
                fontFamily: sans, fontSize: 12, padding: "8px 16px", borderRadius: 6,
                border: `1px solid ${C.accent}`, background: C.accentDim, color: C.accent,
                cursor: "pointer", marginBottom: 16,
              }}>Show calculated premiums →</button>
            )}

            {showPremiums && (
              <>
                <Prose>
                  The asset-level sum produces a base premium of <Emphasis>${fmt(tradBasePremium)}</Emphasis> on 
                  a total TIV of ${fmt(tradTotal)}. But this isn't the final price — the underwriter now applies 
                  account-level modifiers.
                </Prose>

                {!showMods && (
                  <button onClick={() => setShowMods(true)} style={{
                    fontFamily: sans, fontSize: 12, padding: "8px 16px", borderRadius: 6,
                    border: `1px solid ${C.accent}`, background: C.accentDim, color: C.accent,
                    cursor: "pointer", marginBottom: 16,
                  }}>Apply modifiers →</button>
                )}

                {showMods && (
                  <div style={{ border: `1px solid ${C.border}`, borderRadius: 6, overflow: "hidden", marginBottom: 16 }}>
                    <div style={{ padding: "10px 12px", background: C.surfaceAlt, fontFamily: mono, fontSize: 10,
                      color: C.inkMuted, textTransform: "uppercase", letterSpacing: "0.06em",
                      borderBottom: `1px solid ${C.border}` }}>
                      Account-Level Modifiers
                    </div>
                    {TRAD_MODS.map((m, i) => (
                      <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "10px 12px",
                        borderBottom: `1px solid ${C.border}`, alignItems: "center" }}>
                        <div>
                          <div style={{ fontFamily: sans, fontSize: 12, fontWeight: 600, color: C.ink }}>{m.name}</div>
                          <div style={{ fontFamily: sans, fontSize: 11, color: C.inkMuted, marginTop: 2 }}>{m.rationale}</div>
                        </div>
                        <span style={{ fontFamily: mono, fontSize: 14, color: m.value < 1 ? C.trad : C.accent,
                          fontWeight: 600 }}>×{m.value.toFixed(2)}</span>
                      </div>
                    ))}
                    <div style={{ padding: "12px", background: C.surfaceAlt, borderTop: `1px solid ${C.borderStrong}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontFamily: sans, fontSize: 13, fontWeight: 700, color: C.ink }}>Final Premium</span>
                        <span style={{ fontFamily: mono, fontSize: 20, fontWeight: 700, color: C.accent }}>
                          ${fmt(tradFinalPremium)}
                        </span>
                      </div>
                      <div style={{ fontFamily: mono, fontSize: 11, color: C.inkMuted, marginTop: 4 }}>
                        ${fmt(tradBasePremium)} × {tradModProduct.toFixed(4)} = ${fmt(tradFinalPremium)}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {showMods && (
              <div style={{ padding: "16px 20px", background: C.tradBg, border: `1px solid ${C.tradBorder}`,
                borderRadius: 6 }}>
                <div style={{ fontFamily: mono, fontSize: 10, color: C.trad, textTransform: "uppercase",
                  letterSpacing: "0.08em", marginBottom: 8 }}>Note the structure</div>
                <p style={{ fontFamily: serif, fontSize: 14, color: C.ink, lineHeight: 1.7, margin: 0 }}>
                  After all the per-asset work, the underwriter applied <em>account-level</em> modifiers 
                  that moved the price by {fmtPct(Math.abs(1 - tradModProduct))}. The "schedule credit" 
                  of 10% is a subjective, undocumented adjustment. This is the pricing decision that actually 
                  matters — and it was made at the organisational level, not the asset level.
                </p>
              </div>
            )}
          </div>
        )}

        {/* ═══ DSI ═══ */}
        {section === 2 && (
          <div>
            <Tag color={C.dsi}>DSI Method</Tag>
            <h2 style={{ fontFamily: serif, fontSize: 20, fontWeight: 400, color: C.ink, margin: "16px 0 12px" }}>
              Organisational-Level Signal Assessment
            </h2>
            <Prose>
              DSI assesses the same entity — Hargrove Industrial Group — through its observable digital 
              signals. No SOV is required. The exposure basis is inferred from signals with stated 
              confidence, and the rate is determined by the composite risk score.
            </Prose>

            {/* Signal Scores */}
            <div style={{ border: `1px solid ${C.border}`, borderRadius: 6, padding: 16, marginBottom: 16 }}>
              <div style={{ fontFamily: mono, fontSize: 10, color: C.inkMuted, textTransform: "uppercase",
                letterSpacing: "0.06em", marginBottom: 12 }}>Signal Assessment</div>
              {DSI_SIGNALS.map((s, i) => (
                <div key={i} style={{ marginBottom: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                    <span style={{ fontFamily: sans, fontSize: 12, color: C.inkDim }}>{s.cat}</span>
                    <span style={{ fontFamily: mono, fontSize: 12, color: C.dsi, fontWeight: 600 }}>{s.score}/100</span>
                  </div>
                  <div style={{ height: 4, borderRadius: 2, background: C.border }}>
                    <div style={{ height: 4, borderRadius: 2, width: `${s.score}%`,
                      background: s.score >= 80 ? C.dsi : s.score >= 65 ? C.equal : C.accent,
                      transition: "width 0.5s ease" }} />
                  </div>
                  <div style={{ fontFamily: sans, fontSize: 10, color: C.inkMuted, marginTop: 3 }}>{s.detail}</div>
                </div>
              ))}
              <div style={{ marginTop: 16, padding: "12px 16px", background: C.dsiBg, borderRadius: 4,
                border: `1px solid ${C.dsiBorder}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontFamily: sans, fontSize: 13, fontWeight: 600, color: C.ink }}>Composite Score</span>
                  <span style={{ fontFamily: mono, fontSize: 22, fontWeight: 700, color: C.dsi }}>{DSI_COMPOSITE}/1000</span>
                </div>
                <div style={{ fontFamily: mono, fontSize: 11, color: C.inkDim, marginTop: 4 }}>
                  Tier {DSI_TIER} — Standard · Confidence {DSI_CONFIDENCE}
                </div>
              </div>
            </div>

            {/* Pricing Calc */}
            <div style={{ border: `1px solid ${C.border}`, borderRadius: 6, overflow: "hidden", marginBottom: 16 }}>
              <div style={{ padding: "10px 12px", background: C.surfaceAlt, fontFamily: mono, fontSize: 10,
                color: C.inkMuted, textTransform: "uppercase", letterSpacing: "0.06em",
                borderBottom: `1px solid ${C.border}` }}>Pricing Calculation</div>
              
              <div style={{ padding: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0",
                  borderBottom: `1px solid ${C.border}` }}>
                  <span style={{ fontFamily: sans, fontSize: 12, color: C.inkDim }}>Exposure Band (signal-inferred)</span>
                  <span style={{ fontFamily: mono, fontSize: 12, color: C.dsi }}>{DSI_EXPOSURE_BAND} @ {(DSI_CONFIDENCE * 100)}% conf.</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0",
                  borderBottom: `1px solid ${C.border}` }}>
                  <span style={{ fontFamily: sans, fontSize: 12, color: C.inkDim }}>Exposure Midpoint (pricing basis)</span>
                  <span style={{ fontFamily: mono, fontSize: 12, color: C.ink }}>${fmt(DSI_EXPOSURE_MIDPOINT)}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0",
                  borderBottom: `1px solid ${C.border}` }}>
                  <span style={{ fontFamily: sans, fontSize: 12, color: C.inkDim }}>Tier {DSI_TIER} Base Rate</span>
                  <span style={{ fontFamily: mono, fontSize: 12, color: C.dsi }}>{fmtBps(DSI_BASE_RATE * 10000)}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0",
                  borderBottom: `1px solid ${C.border}` }}>
                  <span style={{ fontFamily: sans, fontSize: 12, fontWeight: 600, color: C.ink }}>Base Premium</span>
                  <span style={{ fontFamily: mono, fontSize: 14, fontWeight: 600, color: C.ink }}>${fmt(dsiBasePremium)}</span>
                </div>

                <div style={{ margin: "12px 0 8px", fontFamily: mono, fontSize: 10, color: C.inkMuted,
                  textTransform: "uppercase", letterSpacing: "0.06em" }}>Modifiers</div>
                {DSI_MODS.map((m, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0",
                    borderBottom: `1px solid ${C.border}`, alignItems: "center" }}>
                    <div>
                      <span style={{ fontFamily: sans, fontSize: 12, color: C.ink }}>{m.name}</span>
                      <div style={{ fontFamily: sans, fontSize: 10, color: C.inkMuted, marginTop: 2 }}>{m.source}</div>
                    </div>
                    <span style={{ fontFamily: mono, fontSize: 13, color: m.value < 1 ? C.dsi : C.accent, fontWeight: 600 }}>
                      ×{m.value.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>

              <div style={{ padding: "12px", background: C.surfaceAlt, borderTop: `1px solid ${C.borderStrong}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontFamily: sans, fontSize: 13, fontWeight: 700, color: C.ink }}>Final Premium</span>
                  <span style={{ fontFamily: mono, fontSize: 20, fontWeight: 700, color: C.dsi }}>
                    ${fmt(dsiFinalPremium)}
                  </span>
                </div>
                <div style={{ fontFamily: mono, fontSize: 11, color: C.inkMuted, marginTop: 4 }}>
                  ${fmt(dsiBasePremium)} × {dsiModProduct.toFixed(4)} = ${fmt(dsiFinalPremium)}
                </div>
              </div>
            </div>

            <div style={{ padding: "16px 20px", background: C.dsiBg, border: `1px solid ${C.dsiBorder}`,
              borderRadius: 6 }}>
              <div style={{ fontFamily: mono, fontSize: 10, color: C.dsi, textTransform: "uppercase",
                letterSpacing: "0.08em", marginBottom: 8 }}>Key difference</div>
              <p style={{ fontFamily: serif, fontSize: 14, color: C.ink, lineHeight: 1.7, margin: 0 }}>
                Every input is observable, every modifier is deterministic, and the exposure basis carries 
                a stated confidence level. The same entity scored twice produces the same result. No SOV 
                was required, no documents were exchanged, and the entire assessment completed in under 
                60 seconds.
              </p>
            </div>
          </div>
        )}

        {/* ═══ SIDE-BY-SIDE ═══ */}
        {section === 3 && (
          <div>
            <h2 style={{ fontFamily: serif, fontSize: 20, fontWeight: 400, color: C.ink, margin: "0 0 16px" }}>
              Same Entity, Same Formula, Same Neighbourhood
            </h2>

            <div style={{
              display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0,
              border: `1px solid ${C.border}`, borderRadius: 6, overflow: "hidden", marginBottom: 20,
            }}>
              {/* Headers */}
              <div style={{ padding: "12px 16px", background: C.tradBg, borderBottom: `1px solid ${C.border}`,
                borderRight: `1px solid ${C.border}` }}>
                <Tag color={C.trad}>Traditional</Tag>
              </div>
              <div style={{ padding: "12px 16px", background: C.dsiBg, borderBottom: `1px solid ${C.border}` }}>
                <Tag color={C.dsi}>DSI</Tag>
              </div>

              {/* Row: Exposure Basis */}
              {[
                { label: "Exposure Basis", trad: `SOV: $${fmt(tradTotal)} declared TIV`, dsi: `Signals: ${DSI_EXPOSURE_BAND} inferred (${DSI_CONFIDENCE * 100}% conf.)` },
                { label: "Rate Selection", trad: `Per-asset: ${fmtBps(rateMin)}–${fmtBps(rateMax)} range`, dsi: `Tier ${DSI_TIER}: ${fmtBps(DSI_BASE_RATE * 10000)} (deterministic)` },
                { label: "Effective Wtd Rate", trad: fmtBps(rateWeightedAvg), dsi: fmtBps(DSI_BASE_RATE * 10000) },
                { label: "Base Premium", trad: `$${fmt(tradBasePremium)}`, dsi: `$${fmt(dsiBasePremium)}` },
                { label: "Modifier Product", trad: `×${tradModProduct.toFixed(4)} (incl. subjective credit)`, dsi: `×${dsiModProduct.toFixed(4)} (deterministic)` },
                { label: "Final Premium", trad: `$${fmt(tradFinalPremium)}`, dsi: `$${fmt(dsiFinalPremium)}`, bold: true },
              ].map((row, i) => (
                <div key={i} style={{ display: "contents" }}>
                  <div style={{ padding: "10px 16px", borderBottom: `1px solid ${C.border}`,
                    borderRight: `1px solid ${C.border}`, background: row.bold ? C.tradBg : C.surface }}>
                    <div style={{ fontFamily: sans, fontSize: 10, color: C.inkMuted, marginBottom: 3 }}>{row.label}</div>
                    <div style={{ fontFamily: mono, fontSize: row.bold ? 16 : 12,
                      color: row.bold ? C.trad : C.ink, fontWeight: row.bold ? 700 : 400 }}>{row.trad}</div>
                  </div>
                  <div style={{ padding: "10px 16px", borderBottom: `1px solid ${C.border}`,
                    background: row.bold ? C.dsiBg : C.surface }}>
                    <div style={{ fontFamily: sans, fontSize: 10, color: C.inkMuted, marginBottom: 3 }}>{row.label}</div>
                    <div style={{ fontFamily: mono, fontSize: row.bold ? 16 : 12,
                      color: row.bold ? C.dsi : C.ink, fontWeight: row.bold ? 700 : 400 }}>{row.dsi}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Delta */}
            <div style={{
              padding: "20px 24px", background: C.equalBg, border: `1px solid ${C.equal}`,
              borderRadius: 6, textAlign: "center", marginBottom: 20,
            }}>
              <div style={{ fontFamily: mono, fontSize: 10, color: C.equal, textTransform: "uppercase",
                letterSpacing: "0.08em", marginBottom: 8 }}>Price Difference</div>
              <div style={{ fontFamily: mono, fontSize: 28, fontWeight: 700, color: C.equal }}>
                {diffPct.toFixed(1)}%
              </div>
              <div style={{ fontFamily: sans, fontSize: 13, color: C.inkDim, marginTop: 4 }}>
                ${fmt(diff)} on a ${fmt(tradFinalPremium)} programme
              </div>
            </div>

            {/* Cost comparison */}
            <div style={{ border: `1px solid ${C.border}`, borderRadius: 6, overflow: "hidden" }}>
              <div style={{ padding: "10px 12px", background: C.surfaceAlt, fontFamily: mono, fontSize: 10,
                color: C.inkMuted, textTransform: "uppercase", borderBottom: `1px solid ${C.border}` }}>
                But consider the cost to arrive there
              </div>
              {[
                { metric: "Information gathered", trad: "6-asset SOV, loss runs, questionnaire", dsi: "Domain name" },
                { metric: "Time to price", trad: "15–30 days", dsi: "47 seconds" },
                { metric: "Cost to place", trad: "$350–$650", dsi: "< $10" },
                { metric: "Reproducibility", trad: "No — different UW, different price", dsi: "Yes — deterministic" },
                { metric: "Audit trail", trad: "Reconstructed", dsi: "Immutable, versioned" },
              ].map((row, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: 8,
                  padding: "10px 12px", borderBottom: `1px solid ${C.border}`, fontSize: 12 }}>
                  <span style={{ fontFamily: sans, color: C.inkDim }}>{row.metric}</span>
                  <span style={{ fontFamily: mono, color: C.trad, textAlign: "center" }}>{row.trad}</span>
                  <span style={{ fontFamily: mono, color: C.dsi, textAlign: "center" }}>{row.dsi}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══ ILLUSION ═══ */}
        {section === 4 && (
          <div>
            <h2 style={{ fontFamily: serif, fontSize: 20, fontWeight: 400, color: C.ink, margin: "0 0 16px" }}>
              What the Underwriter Actually Did
            </h2>
            <Prose>
              Look at the per-asset rate distribution. The underwriter applied rates ranging 
              from {fmtBps(rateMin)} to {fmtBps(rateMax)} — a spread 
              of {fmtBps(rateSpread)}. This looks like granular, asset-level 
              analysis. But examine what's really happening:
            </Prose>

            {/* Rate Distribution Chart */}
            <div style={{ border: `1px solid ${C.border}`, borderRadius: 6, padding: 16, marginBottom: 20 }}>
              <div style={{ fontFamily: mono, fontSize: 10, color: C.inkMuted, textTransform: "uppercase",
                letterSpacing: "0.06em", marginBottom: 12 }}>Per-Asset Rate Distribution (bps)</div>
              {SOV_ASSETS.map((a, i) => (
                <RateBar key={i} label={a.name.split("—")[0].trim()} bps={a.rate * 10000}
                  maxBps={12} color={C.trad} />
              ))}
              <div style={{ height: 1, background: C.border, margin: "12px 0" }} />
              <RateBar label="TIV-Weighted Average" bps={rateWeightedAvg} maxBps={12} color={C.accent} isAvg />
              <RateBar label="DSI Tier 2 Rate" bps={DSI_BASE_RATE * 10000} maxBps={12} color={C.dsi} isAvg />
            </div>

            <Prose>
              The rates aren't truly independent assessments. They follow a predictable pattern: 
              offices are cheaper than manufacturing, manufacturing is cheaper than warehousing. These 
              relativities are <Emphasis>occupancy-driven tables</Emphasis> — not individual risk 
              analysis. The underwriter selected a central rate (around {fmtBps(rateWeightedAvg)}) and 
              spread it across assets using standard construction/occupancy relativities.
            </Prose>

            <Prose>
              Then, having done all that per-asset work, the underwriter applied a <Emphasis>10% schedule 
              credit</Emphasis> at the account level — a subjective, undocumented discount that says "this 
              is a good account." That single adjustment moved the premium more than the entire 
              asset-level rate differentiation.
            </Prose>

            <div style={{
              padding: "20px 24px", background: C.accentDim, border: `1px solid ${C.accent}`,
              borderRadius: 6, margin: "20px 0",
            }}>
              <div style={{ fontFamily: mono, fontSize: 10, color: C.accent, textTransform: "uppercase",
                letterSpacing: "0.08em", marginBottom: 8 }}>The critical question</div>
              <p style={{ fontFamily: serif, fontSize: 16, color: C.ink, lineHeight: 1.7, margin: 0 }}>
                If the organisational judgement (the schedule credit, the experience modifier) is the 
                decision that actually drives the final price — why not make it the <em>primary</em> method 
                rather than an afterthought applied on top of illusory asset-level precision?
              </p>
            </div>

            <Prose>
              That is exactly what DSI does. The composite risk score <em>is</em> the organisational 
              judgement — made explicit, observable, and deterministic. The signal-inferred exposure 
              band replaces the self-reported SOV. And the modifiers for loss propensity and complexity 
              replace the subjective schedule credit with traceable, auditable adjustments.
            </Prose>

            <Divider />

            <div style={{ fontFamily: mono, fontSize: 10, color: C.inkMuted, textTransform: "uppercase",
              letterSpacing: "0.06em", marginBottom: 12 }}>Consider also</div>
            
            <Prose>
              Two identical buildings — same construction, same occupancy, same TIV — owned by different 
              organisations will have different loss outcomes. The building doesn't cause the loss. 
              The <Emphasis>organisation's behaviour</Emphasis> does: their maintenance practices, safety 
              culture, incident response capability, investment in protection. Traditional pricing 
              assesses the building. DSI assesses the organisation. Which is more likely to predict the loss?
            </Prose>
          </div>
        )}

        {/* ═══ CONCLUSION ═══ */}
        {section === 5 && (
          <div>
            <h2 style={{ fontFamily: serif, fontSize: 20, fontWeight: 400, color: C.ink, margin: "0 0 16px" }}>
              Equivalent Accuracy, Radically Different Efficiency
            </h2>

            <Prose>
              This comparison demonstrates three things:
            </Prose>

            <div style={{ margin: "16px 0 20px" }}>
              {[
                {
                  num: "1",
                  title: "The formula is identical",
                  body: "Both methods apply a rate to an exposure basis and adjust with modifiers. The mathematical structure is the same. Premium = Exposure × Rate × Modifiers.",
                },
                {
                  num: "2",
                  title: "The granularity is illusory",
                  body: `Traditional per-asset rating produces a weighted average rate of ${fmtBps(rateWeightedAvg)} — within ${fmtBps(Math.abs(rateWeightedAvg - DSI_BASE_RATE * 10000))} of DSI's tier rate of ${fmtBps(DSI_BASE_RATE * 10000)}. The asset-level differentiation creates an appearance of precision, but the underwriter's real pricing decision was an organisational judgement applied as a schedule credit.`,
                },
                {
                  num: "3",
                  title: "The efficiency difference is structural",
                  body: "The traditional method required weeks of document assembly, subjective interpretation by multiple parties, and produced a non-reproducible result. DSI produced an equivalent price in under a minute from observable signals, with a complete audit trail and stated confidence bounds.",
                },
              ].map((item, i) => (
                <div key={i} style={{
                  display: "flex", gap: 16, padding: "16px 0",
                  borderBottom: i < 2 ? `1px solid ${C.border}` : "none",
                }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: "50%", background: C.accentDim,
                    border: `1px solid ${C.accent}`, display: "flex", alignItems: "center",
                    justifyContent: "center", fontFamily: mono, fontSize: 14, color: C.accent,
                    fontWeight: 700, flexShrink: 0,
                  }}>{item.num}</div>
                  <div>
                    <div style={{ fontFamily: sans, fontSize: 14, fontWeight: 700, color: C.ink, marginBottom: 4 }}>
                      {item.title}
                    </div>
                    <p style={{ fontFamily: serif, fontSize: 14, color: C.inkDim, lineHeight: 1.7, margin: 0 }}>
                      {item.body}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div style={{
              padding: "24px", background: `linear-gradient(135deg, ${C.surface} 0%, ${C.surfaceAlt} 100%)`,
              border: `1px solid ${C.accent}`, borderRadius: 6,
            }}>
              <p style={{ fontFamily: serif, fontSize: 16, color: C.ink, lineHeight: 1.7, margin: 0, textAlign: "center" }}>
                DSI does not claim to be more accurate than traditional underwriting. 
                It claims to be <Emphasis>equally accurate, demonstrably faster, reproducible, 
                and auditable</Emphasis> — at a fraction of the cost. The asset-level SOV process 
                adds time and expense without adding predictive power.
              </p>
            </div>

            <div style={{ marginTop: 20, padding: "16px 20px", background: C.surfaceAlt,
              border: `1px solid ${C.border}`, borderRadius: 6 }}>
              <div style={{ fontFamily: mono, fontSize: 10, color: C.inkMuted, textTransform: "uppercase",
                letterSpacing: "0.06em", marginBottom: 8 }}>What DSI adds that traditional cannot</div>
              {[
                "Confidence scoring — DSI states how sure it is. Traditional pricing implies certainty it doesn't have.",
                "Behavioural loss inference — losses are predicted from organisational behaviour, not historical frequency on sparse data.",
                "Continuous monitoring — signals are re-assessed automatically, not once per renewal cycle.",
                "Reproducibility — the same entity scored by any participant produces the same result.",
              ].map((item, i) => (
                <div key={i} style={{ display: "flex", gap: 10, marginBottom: 8 }}>
                  <span style={{ color: C.dsi, fontWeight: 700, flexShrink: 0 }}>→</span>
                  <span style={{ fontFamily: sans, fontSize: 13, color: C.ink, lineHeight: 1.5 }}>{item}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── NAV ── */}
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 28, paddingTop: 16,
          borderTop: `1px solid ${C.border}` }}>
          <button onClick={() => setSection(Math.max(0, section - 1))}
            disabled={section === 0}
            style={{ fontFamily: sans, fontSize: 12, padding: "8px 16px", borderRadius: 6,
              border: `1px solid ${C.border}`, background: C.surface, cursor: "pointer",
              color: section === 0 ? C.inkMuted : C.ink, opacity: section === 0 ? 0.4 : 1 }}>
            ← Previous
          </button>
          <span style={{ fontFamily: mono, fontSize: 11, color: C.inkMuted, alignSelf: "center" }}>
            {section + 1} / {SECTIONS.length}
          </span>
          <button onClick={() => setSection(Math.min(SECTIONS.length - 1, section + 1))}
            disabled={section === SECTIONS.length - 1}
            style={{ fontFamily: sans, fontSize: 12, padding: "8px 16px", borderRadius: 6,
              border: `1px solid ${C.accent}`, background: C.accentDim, color: C.accent,
              cursor: "pointer", opacity: section === SECTIONS.length - 1 ? 0.4 : 1 }}>
            Next →
          </button>
        </div>
      </div>

      {/* ── FOOTER ── */}
      <div style={{ padding: "20px 32px", borderTop: `1px solid ${C.border}`, textAlign: "center", marginTop: 20 }}>
        <span style={{ fontFamily: mono, fontSize: 10, color: C.inkMuted }}>
          © John Walker — All rights reserved. Digital Signal Intelligence (DSI) is proprietary IP.
        </span>
      </div>
    </div>
  );
}
