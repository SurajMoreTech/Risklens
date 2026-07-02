'use client';

import { useRef, useEffect } from 'react';

export default function GlucoseMolecule({ width = 220, height = 240 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const W = width;
    const H = height;
    canvas.width = W;
    canvas.height = H;

    // Glucose molecule atom positions (same as Streamlit)
    const atoms = [
      ['O', 0, 1.15, 0.2],
      ['C', 1, 0.58, -0.2],
      ['C', 1, -0.58, 0.2],
      ['C', 0, -1.15, -0.2],
      ['C', -1, -0.58, 0.2],
      ['C', -1, 0.58, -0.2],
      ['C', -1.7, 1.15, -0.5],
      ['O', 1.7, 0.58, -0.7],
      ['O', 1.7, -0.58, 0.7],
      ['O', 0, -1.9, -0.7],
      ['O', -1.7, -0.58, 0.7],
      ['O', -2.4, 1.7, -0.5],
    ];

    const bonds = [
      [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0],
      [5, 6], [1, 7], [2, 8], [3, 9], [4, 10], [6, 11],
    ];

    const col = { C: '#0D9488', O: '#E8927C' };
    const hi = { C: '#5eead4', O: '#f4a997' };
    const dk = { C: '#0a7a71', O: '#c0604a' };
    const sz = { C: 15, O: 13 };

    let ay = 0;
    let ax = 0;
    let animId;

    function rot(px, py, pz) {
      const x1 = px * Math.cos(ay) - pz * Math.sin(ay);
      const z1 = px * Math.sin(ay) + pz * Math.cos(ay);
      const y1 = py * Math.cos(ax) - z1 * Math.sin(ax);
      const z2 = py * Math.sin(ax) + z1 * Math.cos(ax);
      return [x1, y1, z2];
    }

    function prj(px, py, pz) {
      const s = 45;
      const d = 5;
      const f = d / (d + pz);
      return [W / 2 + px * s * f, H / 2 - py * s * f, f];
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);

      const ra = atoms.map((a) => {
        const r = rot(a[1], a[2], a[3]);
        return { t: a[0], rx: r[0], ry: r[1], rz: r[2] };
      });

      // Draw bonds
      bonds.forEach((b) => {
        const p1 = prj(ra[b[0]].rx, ra[b[0]].ry, ra[b[0]].rz);
        const p2 = prj(ra[b[1]].rx, ra[b[1]].ry, ra[b[1]].rz);
        ctx.beginPath();
        ctx.moveTo(p1[0], p1[1]);
        ctx.lineTo(p2[0], p2[1]);
        ctx.strokeStyle = 'rgba(180,200,220,0.45)';
        ctx.lineWidth = 2.5;
        ctx.stroke();
      });

      // Sort by z for depth rendering
      const idx = ra.map((_, i) => i).sort((a, b) => ra[a].rz - ra[b].rz);

      // Draw atoms
      idx.forEach((i) => {
        const a = ra[i];
        const p = prj(a.rx, a.ry, a.rz);
        const r = sz[a.t] * p[2];
        const g = ctx.createRadialGradient(
          p[0] - r * 0.3, p[1] - r * 0.3, r * 0.05,
          p[0], p[1], r
        );
        g.addColorStop(0, hi[a.t]);
        g.addColorStop(0.55, col[a.t]);
        g.addColorStop(1, dk[a.t]);
        ctx.beginPath();
        ctx.arc(p[0], p[1], r, 0, Math.PI * 2);
        ctx.fillStyle = g;
        ctx.fill();
      });

      ay += 0.007;
      ax += 0.003;
      animId = requestAnimationFrame(draw);
    }

    draw();

    return () => {
      if (animId) cancelAnimationFrame(animId);
    };
  }, [width, height]);

  return (
    <div className="glucose-container">
      <canvas
        ref={canvasRef}
        style={{
          display: 'block',
          margin: '0 auto',
          filter: 'drop-shadow(0 0 12px rgba(13,148,136,0.35))',
        }}
      />
      <p className="glucose-label">
        GLUCOSE · C₆H₁₂O₆
      </p>
    </div>
  );
}
