"use client";

import Link from "next/link";

export default function Hero() {
  return (
    <section className="hero" id="hero">
      <div className="hero-content">
        <div className="hero-text">
          <div className="hero-badge">
            <span>🔬</span> CDC BRFSS Validated · 253,680 Records
          </div>

          <h1 className="hero-title">
            Know Your Diabetes Risk in 5 Minutes —{" "}
            <span>No Blood Test Required</span>
          </h1>

          <p className="hero-subtitle">
            Clinically validated screening using CDC health indicators. Get your
            personalized risk report instantly with AI-powered explainability.
          </p>

          <div className="hero-cta-group">
            <Link href="/assess" className="btn btn-primary btn-lg">
              🩺 Start Free Assessment
            </Link>
            <Link href="#how-it-works" className="btn btn-secondary">
              Learn More
            </Link>
          </div>

          <div className="hero-stats">
            <div className="hero-stat">
              <div className="hero-stat-value">34.1M</div>
              <div className="hero-stat-label">US Adults with Diabetes</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-value">88M</div>
              <div className="hero-stat-label">Have Prediabetes</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-value">82%</div>
              <div className="hero-stat-label">Model Accuracy (AUROC)</div>
            </div>
          </div>
        </div>

        <div className="hero-visual">
          <div
            style={{
              width: "100%",
              maxWidth: 480,
              aspectRatio: "1 / 1",
              borderRadius: "var(--radius-xl)",
              background:
                "linear-gradient(135deg, rgba(13,148,136,0.08) 0%, rgba(94,234,212,0.06) 50%, rgba(13,148,136,0.04) 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Animated medical wave pattern */}
            <svg
              viewBox="0 0 400 400"
              style={{ width: "100%", height: "100%" }}
            >
              {/* Background circles */}
              <circle
                cx="200"
                cy="200"
                r="150"
                fill="none"
                stroke="rgba(13,148,136,0.08)"
                strokeWidth="1"
              />
              <circle
                cx="200"
                cy="200"
                r="120"
                fill="none"
                stroke="rgba(13,148,136,0.06)"
                strokeWidth="1"
              />
              <circle
                cx="200"
                cy="200"
                r="90"
                fill="none"
                stroke="rgba(13,148,136,0.04)"
                strokeWidth="1"
              />

              {/* Heart rate / pulse line */}
              <path
                d="M40,200 L100,200 L120,200 L140,160 L160,240 L180,150 L200,250 L220,170 L240,200 L260,200 L360,200"
                fill="none"
                stroke="rgba(13,148,136,0.5)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <animate
                  attributeName="stroke-dashoffset"
                  from="600"
                  to="0"
                  dur="3s"
                  repeatCount="indefinite"
                />
                <animate
                  attributeName="stroke-dasharray"
                  values="0 600;300 600;600 600"
                  dur="3s"
                  repeatCount="indefinite"
                />
              </path>

              {/* Center cross / medical symbol */}
              <g transform="translate(200,200)">
                <rect
                  x="-20"
                  y="-5"
                  width="40"
                  height="10"
                  rx="3"
                  fill="rgba(13,148,136,0.25)"
                />
                <rect
                  x="-5"
                  y="-20"
                  width="10"
                  height="40"
                  rx="3"
                  fill="rgba(13,148,136,0.25)"
                />
              </g>

              {/* Floating dots */}
              <circle cx="100" cy="120" r="4" fill="rgba(13,148,136,0.2)">
                <animate
                  attributeName="cy"
                  values="120;110;120"
                  dur="3s"
                  repeatCount="indefinite"
                />
              </circle>
              <circle cx="300" cy="150" r="3" fill="rgba(94,234,212,0.3)">
                <animate
                  attributeName="cy"
                  values="150;140;150"
                  dur="2.5s"
                  repeatCount="indefinite"
                />
              </circle>
              <circle cx="320" cy="280" r="5" fill="rgba(13,148,136,0.15)">
                <animate
                  attributeName="cy"
                  values="280;270;280"
                  dur="4s"
                  repeatCount="indefinite"
                />
              </circle>
              <circle cx="80" cy="300" r="3" fill="rgba(94,234,212,0.2)">
                <animate
                  attributeName="cy"
                  values="300;290;300"
                  dur="3.5s"
                  repeatCount="indefinite"
                />
              </circle>

              {/* Shield / trust icon */}
              <g transform="translate(200,320) scale(0.6)">
                <path
                  d="M0,-30 L25,-15 L25,10 C25,25 0,40 0,40 C0,40 -25,25 -25,10 L-25,-15 Z"
                  fill="rgba(13,148,136,0.12)"
                  stroke="rgba(13,148,136,0.3)"
                  strokeWidth="1"
                />
                <path
                  d="M-8,5 L-3,10 L8,-5"
                  fill="none"
                  stroke="rgba(13,148,136,0.4)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>

              {/* DNA helix hint */}
              <g transform="translate(80,200) scale(0.5)" opacity="0.3">
                <path
                  d="M0,-60 C20,-40 -20,-20 0,0 C20,20 -20,40 0,60"
                  fill="none"
                  stroke="rgba(13,148,136,0.5)"
                  strokeWidth="2"
                />
                <path
                  d="M0,-60 C-20,-40 20,-20 0,0 C-20,20 20,40 0,60"
                  fill="none"
                  stroke="rgba(94,234,212,0.4)"
                  strokeWidth="2"
                />
              </g>
            </svg>
          </div>
        </div>
      </div>
    </section>
  );
}
