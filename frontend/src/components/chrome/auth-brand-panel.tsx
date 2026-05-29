/**
 * Brand panel for the split-screen auth surface. Deep navy regardless of
 * theme — it's chrome, not content. Forced classes (no token swaps) keep
 * dark mode from inverting the panel.
 */
export function AuthBrandPanel() {
  const pulseHeights = [10, 18, 12, 26, 16, 22, 14, 30, 20];
  return (
    
    <div
      className="relative hidden w-[50%] shrink-0 flex-col overflow-hidden p-11 text-[#F1ECE0] lg:flex"
      style={{ background: "#051322" }}
    >
      <div className="flex">
        {/* Use the imported brand SVG; falls back to wordmark if SVG missing. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/dsi-logo.svg"
          alt="Generate — Digital Signal Intelligence"
          className="absolute top-[5%] left-[0%] h-20 w-auto"
        />
      </div>

      
      <div className="flex flex-1 flex-col justify-center">
        
        <h1
          className="max-w-[500px] font-semibold tracking-[-0.015em]"
          style={{ font: "600 38px/1.15 'IBM Plex Sans', sans-serif" }}
        >
          Risk,
          <br />
          <span style={{ color: "#39D3BA" }}>illuminated by digital signals.</span>
        </h1>

        <p
          className="mt-4 max-w-[420px]"
          style={{
            font: "400 14px/1.6 'IBM Plex Sans', sans-serif",
            color: "rgba(241,236,224,0.7)",
          }}
        >
          A continuous signal engine for risk in the agentic era.
        </p>
        
      </div>

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
