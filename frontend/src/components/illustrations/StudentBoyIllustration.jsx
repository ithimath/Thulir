import React from 'react'

/**
 * Consistent Animated Student Illustration: Boy Student
 * - Style: Professional, friendly, age-appropriate Tamil Nadu school uniform
 * - Uniform: Crisp white shirt with dark navy/teal collar, tie, and school badge
 * - Character: Neatly styled short black hair, friendly smile
 * - Subtle Animation: Gentle eyelid blink, subtle idle float
 * - Accessibility: Pauses animations when prefers-reduced-motion is active
 */
export default function StudentBoyIllustration({ size = 48, animate = true, className = '' }) {
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
      aria-label="Boy student illustration"
    >
      <defs>
        <radialGradient id="boy_bg_glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#0284C7" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#0369A1" stopOpacity="0.05" />
        </radialGradient>
        <linearGradient id="boy_skin" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#F5C6A5" />
          <stop offset="100%" stopColor="#E2AC89" />
        </linearGradient>
        <linearGradient id="boy_shirt" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="100%" stopColor="#E2E8F0" />
        </linearGradient>
        <linearGradient id="boy_tie" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#0F766E" />
          <stop offset="100%" stopColor="#042F2E" />
        </linearGradient>
        <linearGradient id="boy_hair" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#242124" />
          <stop offset="100%" stopColor="#111113" />
        </linearGradient>
      </defs>

      {/* Background circular halo */}
      <circle cx="60" cy="60" r="56" fill="url(#boy_bg_glow)" stroke="#0284C7" strokeWidth="1.5" strokeOpacity="0.3" />

      {/* Shoulders & White Uniform Shirt */}
      <path
        d="M20 114 C20 95, 36 86, 60 86 C84 86, 100 95, 100 114 Z"
        fill="url(#boy_shirt)"
      />
      {/* Dark Navy Uniform Vest / Shoulder Straps */}
      <path d="M20 114 C20 98, 28 92, 38 90 L42 114 Z" fill="#042F2E" />
      <path d="M100 114 C100 98, 92 92, 82 90 L78 114 Z" fill="#042F2E" />

      {/* White Shirt Collar Wings */}
      <polygon points="60,88 44,98 55,102" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1" />
      <polygon points="60,88 76,98 65,102" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1" />

      {/* School Tie */}
      <polygon points="57,98 63,98 65,114 55,114" fill="url(#boy_tie)" />
      {/* Tie Knot */}
      <rect x="56" y="94" width="8" height="6" rx="1.5" fill="#0F766E" />

      {/* School Badge / Pin on Chest */}
      <circle cx="34" cy="104" r="3" fill="#F59E0B" />
      <circle cx="34" cy="104" r="1.5" fill="#B45309" />

      {/* Neck */}
      <rect x="54" y="74" width="12" height="15" rx="3" fill="#E2AC89" />

      {/* Head / Face */}
      <ellipse cx="60" cy="58" rx="22" ry="24" fill="url(#boy_skin)" />

      {/* Neat Hair (Short, clean-cut, combed to the side) */}
      <path
        d="M37 54 C36 34, 46 28, 60 28 C74 28, 83 34, 83 54 C80 44, 72 40, 60 40 C48 40, 40 44, 37 54 Z"
        fill="url(#boy_hair)"
      />
      {/* Side parting hair volume */}
      <path
        d="M38 46 C44 33, 62 32, 79 38 C75 42, 65 37, 50 39 C43 40, 39 43, 38 46 Z"
        fill="#242124"
      />
      {/* Sideburns */}
      <path d="M38 52 L38 58" stroke="url(#boy_hair)" strokeWidth="3" strokeLinecap="round" />
      <path d="M82 52 L82 58" stroke="url(#boy_hair)" strokeWidth="3" strokeLinecap="round" />

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

      {/* Cute Rosy Cheeks */}
      <circle cx="47" cy="63" r="3.5" fill="#F87171" fillOpacity="0.30" />
      <circle cx="73" cy="63" r="3.5" fill="#F87171" fillOpacity="0.30" />

      {/* Small Nose */}
      <path d="M60 58 Q61 62 59 63" stroke="#D18E66" strokeWidth="1.3" strokeLinecap="round" />

      {/* Friendly Smile */}
      <path d="M54 67 Q60 72 66 67" stroke="#A83F3F" strokeWidth="2" strokeLinecap="round" fill="none" />
    </svg>
  )
}
