// The RiskLens mark — a lens over a pulse line. Kept in sync with app/icon.svg.
// Pass a unique `id` when several instances render on the same page so the
// gradient defs don't collide.
export default function LogoMark({ id = "rl-mark-g" }) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#14B8A6" />
          <stop offset="1" stopColor="#0B5F58" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="14" fill={`url(#${id})`} />
      <circle cx="32" cy="26" r="13" fill="none" stroke="#FFFFFF" strokeWidth="5" />
      <circle cx="36.5" cy="21.5" r="4.5" fill="#5EEAD4" />
      <path
        d="M13 46h9l4-7 5 12 4-9 3 4h12"
        fill="none"
        stroke="#FFFFFF"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
