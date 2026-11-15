import React from 'react'

/**
 * Consistent Student Illustration: Neutral / Unisex Default
 * - Used when gender information is unspecified or preferred neutral
 * - Matches the exact canvas (120x120), artistic style, crisp school uniform,
 *   badge, and subtle animations (idle float and gentle blink) of the student illustrations
 * - Respects prefers-reduced-motion
 */
export default function StudentNeutralIllustration({ size = 48, animate = true, className = '' }) {
  const floatClass = animate ? 'anim-float' : ''
  const blinkClass = animate ? 'anim-blink' : ''

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`inline-block flex-shrink-0 select-none ${floatClass} ${className}`}
      aria-label="Student illustration"
    >
      <defs>
        <radialGradient id="neutral_bg_glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#0D9488" stopOpacity="0.18" />
          <stop offset="100%" stopColor="#042F2E" stopOpacity="0.04" />
        </radialGradient>
        <linearGradient id="neutral_skin" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#F5C6A5" />
          <stop offset="100%" stopColor="#E2AC89" />
        </linearGradient>
        <linearGradient id="neutral_shirt" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="100%" stopColor="#E2E8F0" />
        </linearGradient>
        <linearGradient id="neutral_hair" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#2A2A2E" />
          <stop offset="100%" stopColor="#141416" />
        </linearGradient>
        <linearGradient id="neutral_collar" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#0F766E" />
          <stop offset="100%" stopColor="#042F2E" />
        </linearGradient>
      </defs>

      {/* Background circular halo */}
      <circle cx="60" cy="60" r="56" fill="url(#neutral_bg_glow)" stroke="#0D9488" strokeWidth="1.5" strokeOpacity="0.25" />

      {/* Shoulders & White Uniform Shirt */}
      <path
        d="M20 114 C20 95, 36 86, 60 86 C84 86, 100 95, 100 114 Z"
        fill="url(#neutral_shirt)"
      />
      {/* Uniform Teal Collar Outer */}
      <path d="M20 114 C20 98, 28 92, 38 90 L42 114 Z" fill="url(#neutral_collar)" />
      <path d="M100 114 C100 98, 92 92, 82 90 L78 114 Z" fill="url(#neutral_collar)" />

      {/* White V-Collar Center Fold */}
      <polygon points="60,88 46,99 56,103" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1" />
      <polygon points="60,88 74,99 64,103" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1" />
      <polygon points="60,94 54,114 66,114" fill="#042F2E" />

      {/* School Badge on Chest */}
      <circle cx="34" cy="104" r="3" fill="#F59E0B" />
      <circle cx="34" cy="104" r="1.5" fill="#B45309" />

      {/* Neck */}
      <rect x="54" y="74" width="12" height="15" rx="3" fill="#E2AC89" />

      {/* Head / Face */}
      <ellipse cx="60" cy="58" rx="22" ry="24" fill="url(#neutral_skin)" />

      {/* Unisex Student Haircut (Neat, clean, rounded crop) */}
      <path
        d="M38 54 C36 34, 46 27, 60 27 C74 27, 84 34, 82 54 C78 44, 70 38, 60 38 C50 38, 42 44, 38 54 Z"
        fill="url(#neutral_hair)"
      />
      <path
        d="M40 44 C45 32, 60 30, 78 36 C73 40, 64 36, 52 38 C46 39, 41 42, 40 44 Z"
        fill="#2A2A2E"
      />

      {/* Ears */}
      <circle cx="38" cy="59" r="3.5" fill="#E2AC89" />
      <circle cx="82" cy="59" r="3.5" fill="#E2AC89" />

      {/* Eyebrows */}
      <path d="M49 50 Q53 47 57 49" stroke="#2D2520" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M63 49 Q67 47 71 50" stroke="#2D2520" strokeWidth="1.8" strokeLinecap="round" />

      {/* Eyes with Animated Blinking */}
      <g className={blinkClass}>
        {/* Left Eye */}
        <ellipse cx="52" cy="56" rx="2.8" ry="3.2" fill="#1E293B" />
        <circle cx="51.2" cy="55" r="1" fill="#FFFFFF" />
        {/* Right Eye */}
        <ellipse cx="68" cy="56" rx="2.8" ry="3.2" fill="#1E293B" />
        <circle cx="67.2" cy="55" r="1" fill="#FFFFFF" />
      </g>

      {/* Cheeks */}
      <circle cx="47" cy="63" r="3.5" fill="#F87171" fillOpacity="0.25" />
      <circle cx="73" cy="63" r="3.5" fill="#F87171" fillOpacity="0.25" />

      {/* Small Nose */}
      <path d="M60 58 Q61 62 59 63" stroke="#D18E66" strokeWidth="1.3" strokeLinecap="round" />

      {/* Friendly Smile */}
      <path d="M54 67 Q60 72 66 67" stroke="#A83F3F" strokeWidth="2" strokeLinecap="round" fill="none" />
    </svg>
  )
}
