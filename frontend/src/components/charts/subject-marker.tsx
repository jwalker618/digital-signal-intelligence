import { memo } from "react";

/**
 * High-contrast "YOU" callout for cohort scatter plots (revised pack —
 * wb_b / wb_c). Halo + connector + point + label pill so the subject
 * reads against the cohort cloud. Rendered inside an <svg>.
 */
export const SubjectMarker = memo(function SubjectMarker({
  cx,
  cy,
  label,
  pillW = 92,
}: {
  cx: number;
  cy: number;
  label: string;
  pillW?: number;
}) {
  const pillH = 22;
  const pillCy = cy - 32;
  return (
    <g>
      <circle cx={cx} cy={cy} r={15} fill="var(--color-info)" opacity={0.16} />
      <line
        x1={cx}
        y1={pillCy + pillH / 2}
        x2={cx}
        y2={cy - 9}
        stroke="var(--color-info)"
        strokeWidth={1.5}
      />
      <circle
        cx={cx}
        cy={cy}
        r={7}
        fill="var(--color-info)"
        stroke="var(--color-surface)"
        strokeWidth={2.5}
      />
      <rect
        x={cx - pillW / 2}
        y={pillCy - pillH / 2}
        width={pillW}
        height={pillH}
        rx={6}
        fill="var(--color-info)"
      />
      <text
        x={cx}
        y={pillCy + 4}
        textAnchor="middle"
        style={{
          font: "700 11.5px IBM Plex Sans",
          fill: "#fff",
          letterSpacing: "0.02em",
        }}
      >
        {label}
      </text>
    </g>
  );
});
