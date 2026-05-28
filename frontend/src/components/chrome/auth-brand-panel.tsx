/**
 * Brand panel for the split-screen auth surface. Deep navy regardless of
 * theme — it's chrome, not content. Forced classes (no token swaps) keep
 * dark mode from inverting the panel.
 */
export function AuthBrandPanel() {
  const pulseHeights = [10, 18, 12, 26, 16, 22, 14, 30, 20];
  return (
    <div
      className="relative hidden w-[46%] shrink-0 flex-col overflow-hidden p-11 text-[#F1ECE0] lg:flex"
      style={{ background: "#051322" }}
    >
      <div className="flex items-center">
        {/* Use the imported brand SVG; falls back to wordmark if SVG missing. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/dsi-logo.svg"
          alt="Generate — Digital Signal Intelligence"
          className="block h-14 w-auto"
        />
      </div>

      <div className="flex flex-1 flex-col justify-center">
        <h1
          className="max-w-[460px] font-semibold tracking-[-0.015em]"
          style={{ font: "600 38px/1.15 'IBM Plex Sans', sans-serif" }}
        >
          Risk,
          <br />
          <span style={{ color: "#39D3BA" }}>illuminated by signal.</span>
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
        <div className="mt-9 flex items-end gap-2.5">
          {pulseHeights.map((h, i) => (
            <span
              key={i}
              className="block w-1 rounded-sm"
              style={{
                height: h,
                background:
                  i % 3 === 1 ? "#39D3BA" : "rgba(57,211,186,0.4)",
              }}
              aria-hidden
            />
          ))}
        </div>
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
