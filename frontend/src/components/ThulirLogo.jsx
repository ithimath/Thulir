import React from 'react'

export default function ThulirLogo({ size = 36, className = '', showGlow = true }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`flex-shrink-0 transition-transform duration-300 hover:scale-105 ${className}`}
      aria-label="THULIR Logo - Education & Student Growth"
      role="img"
    >
      <defs>
        <linearGradient id="thulirLeafGrad" x1="16" y1="40" x2="44" y2="12" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#059669" />
          <stop offset="60%" stopColor="#10B981" />
          <stop offset="100%" stopColor="#34D399" />
        </linearGradient>
        <linearGradient id="thulirBookGrad" x1="12" y1="46" x2="52" y2="56" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0F766E" />
          <stop offset="50%" stopColor="#0D9488" />
          <stop offset="100%" stopColor="#14B8A6" />
        </linearGradient>
        <linearGradient id="thulirSunGrad" x1="32" y1="12" x2="32" y2="24" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FDE047" />
          <stop offset="100%" stopColor="#F59E0B" />
        </linearGradient>
        {showGlow && (
          <filter id="thulirGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="1.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        )}
      </defs>

      {/* Golden Dawn / Sun of Knowledge */}
      <circle
        cx="32"
        cy="18"
        r="7.5"
        fill="url(#thulirSunGrad)"
        filter={showGlow ? "url(#thulirGlow)" : undefined}
      />
      <circle
        cx="32"
        cy="18"
        r="11"
        stroke="#FDE047"
        strokeOpacity="0.35"
        strokeWidth="1.2"
        strokeDasharray="2 3"
      />

      {/* Central Stem */}
      <path
        d="M32 46 C32 38 32 30 32 24"
        stroke="#059669"
        strokeWidth="2.5"
        strokeLinecap="round"
      />

      {/* Left Sprout Leaf (Thulir) */}
      <path
        d="M32 34 C24 33 16 26 19 18 C26 17 31 25 32 34 Z"
        fill="url(#thulirLeafGrad)"
      />
      <path
        d="M22 23 C26 27 29 30 32 32"
        stroke="#A7F3D0"
        strokeWidth="0.8"
        strokeLinecap="round"
        strokeOpacity="0.8"
      />

      {/* Right Sprout Leaf (Tender New Shoot) */}
      <path
        d="M32 29 C38 27 46 21 44 14 C37 13 33 21 32 29 Z"
        fill="url(#thulirLeafGrad)"
      />
      <path
        d="M41 18 C38 22 35 25 32 28"
        stroke="#A7F3D0"
        strokeWidth="0.8"
        strokeLinecap="round"
        strokeOpacity="0.8"
      />

      {/* Open Book Base (Foundation of Learning & School Records) */}
      {/* Left Page */}
      <path
        d="M32 46 C24 43 14 44 10 47 C10 49.5 11 54 11 54 C16 51 25 50.5 32 53 Z"
        fill="url(#thulirBookGrad)"
      />
      {/* Right Page */}
      <path
        d="M32 46 C40 43 50 44 54 47 C54 49.5 53 54 53 54 C48 51 39 50.5 32 53 Z"
        fill="url(#thulirBookGrad)"
      />
      {/* Center Book Spine */}
      <path
        d="M32 46 V55"
        stroke="#042F2E"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="32" cy="46" r="1.5" fill="#34D399" />
    </svg>
  )
}

