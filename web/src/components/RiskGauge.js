"use client";

import { useEffect, useState } from "react";

export default function RiskGauge({ score = 0, size = 240 }) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    let frame;
    let start = null;
    const duration = 1500;

    const animate = (timestamp) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(score * eased));
      if (progress < 1) frame = requestAnimationFrame(animate);
    };

    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const center = size / 2;
  const strokeWidth = 14;
  const radius = center - strokeWidth - 8;
  const circumference = 2 * Math.PI * radius;

  // Arc goes from 135° to 405° (270° sweep)
  const sweepAngle = 270;
  const startAngle = 135;
  const arcLength = (sweepAngle / 360) * circumference;
  const filledLength = (animatedScore / 100) * arcLength;
  const dashOffset = arcLength - filledLength;

  // Color based on score
  const getColor = (s) => {
    if (s < 30) return "var(--risk-low)";
    if (s < 70) return "var(--risk-moderate)";
    return "var(--risk-high)";
  };

  const getGlow = (s) => {
    if (s < 30) return "rgba(56, 161, 105, 0.3)";
    if (s < 70) return "rgba(214, 158, 46, 0.3)";
    return "rgba(229, 62, 62, 0.3)";
  };

  const getRiskLabel = (s) => {
    if (s < 30) return "Low Risk";
    if (s < 70) return "Moderate Risk";
    return "High Risk";
  };

  const color = getColor(animatedScore);
  const glow = getGlow(animatedScore);

  // SVG arc path helper
  const describeArc = (cx, cy, r, startDeg, endDeg) => {
    const startRad = ((startDeg - 90) * Math.PI) / 180;
    const endRad = ((endDeg - 90) * Math.PI) / 180;
    const x1 = cx + r * Math.cos(startRad);
    const y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad);
    const y2 = cy + r * Math.sin(endRad);
    const largeArc = endDeg - startDeg > 180 ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
  };

  return (
    <div className="gauge-container">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ filter: `drop-shadow(0 4px 20px ${glow})` }}
      >
        {/* Background track */}
        <path
          d={describeArc(center, center, radius, startAngle, startAngle + sweepAngle)}
          fill="none"
          stroke="var(--bg-tertiary)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Color zone indicators (subtle) */}
        <path
          d={describeArc(center, center, radius, startAngle, startAngle + sweepAngle * 0.3)}
          fill="none"
          stroke="rgba(56, 161, 105, 0.12)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        <path
          d={describeArc(center, center, radius, startAngle + sweepAngle * 0.3, startAngle + sweepAngle * 0.7)}
          fill="none"
          stroke="rgba(214, 158, 46, 0.12)"
          strokeWidth={strokeWidth}
        />
        <path
          d={describeArc(center, center, radius, startAngle + sweepAngle * 0.7, startAngle + sweepAngle)}
          fill="none"
          stroke="rgba(229, 62, 62, 0.12)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Filled arc */}
        <path
          d={describeArc(center, center, radius, startAngle, startAngle + sweepAngle)}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${arcLength}`}
          strokeDashoffset={dashOffset}
          style={{ transition: "stroke 0.3s ease" }}
        />

        {/* Center score text */}
        <text
          x={center}
          y={center - 10}
          textAnchor="middle"
          dominantBaseline="central"
          style={{
            fontSize: size * 0.22,
            fontWeight: 800,
            fontFamily: "var(--font-heading)",
            fill: color,
          }}
        >
          {animatedScore}
        </text>

        {/* "/ 100" label */}
        <text
          x={center}
          y={center + size * 0.1}
          textAnchor="middle"
          dominantBaseline="central"
          style={{
            fontSize: size * 0.07,
            fontWeight: 500,
            fontFamily: "var(--font-body)",
            fill: "var(--text-muted)",
          }}
        >
          out of 100
        </text>

        {/* Risk label */}
        <text
          x={center}
          y={center + size * 0.22}
          textAnchor="middle"
          dominantBaseline="central"
          style={{
            fontSize: size * 0.065,
            fontWeight: 700,
            fontFamily: "var(--font-body)",
            fill: color,
            letterSpacing: "1px",
            textTransform: "uppercase",
          }}
        >
          {getRiskLabel(animatedScore)}
        </text>
      </svg>
    </div>
  );
}
