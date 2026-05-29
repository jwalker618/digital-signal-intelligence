/**
 * Brand panel for the split-screen auth surface (revised pack BrandPanel).
 * Deep navy regardless of theme — it's chrome, not content. Forced colours
 * (no token swaps) keep dark mode from inverting the panel.
 *
 * Layout mirrors reim_auth.jsx exactly: 46% width, logo in normal flow at
 * the top, the statement vertically centred via flex-1, footer pinned at
 * the bottom.
 */
export function AuthBrandPanel() {
  return (
    <div
      className="relative hidden w-[46%] shrink-0 flex-col overflow-hidden p-11 text-[#F1ECE0] lg:flex"
      style={{ background: "#051322" }}
    >
      {/* Wordmark — normal flow, top of the panel */}
      <div className="flex items-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/dsi-logo.svg"
          alt="Generate · DSI"
          className="block h-14 w-auto"
        />
      </div>

      {/* Centred statement */}
      <div className="flex flex-1 flex-col justify-center">
        <h1
          className="tracking-[-0.015em]"
          style={{ font: "600 34px/1.15 'IBM Plex Sans', sans-serif", maxWidth: 600 }}
        >
          Risk,
          <br />
          <span style={{ color: "#39D3BA", whiteSpace: "nowrap" }}>
            illuminated by digital signals.
          </span>
        </h1>
        <p
          className="mt-[18px]"
          style={{
            font: "400 14px/1.6 'IBM Plex Sans', sans-serif",
            color: "rgba(241,236,224,0.7)",
            maxWidth: 420,
          }}
        >
          A continuous signal engine for risk in the agentic era.
        </p>
      </div>

      {/* Footer */}
      <div
        className="flex gap-4"
        style={{ font: "11px 'IBM Plex Sans', sans-serif", color: "rgba(241,236,224,0.45)" }}
      >
        <span>v8.2.1 · build 2026.05</span>
        <span className="ml-auto">SOC 2 Type II · ISO 27001</span>
      </div>
    </div>
  );
}
