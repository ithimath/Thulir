import React from 'react'

/**
 * Consistent Animated Student Illustration: Girl Student
 * - Style: Professional, friendly, age-appropriate Tamil Nadu school uniform
 * - Uniform: Crisp white collared shirt, teal/navy pinafore with school badge, braided hair with ribbons
 * - Subtle Animation: Gentle eyelid blink, subtle idle float
 * - Accessibility: Pauses animations when prefers-reduced-motion is active
 */
export default function StudentGirlIllustration({ size = 48, animate = true, className = '' }) {
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
      aria-label="Girl student illustration"
    >
      <defs>
        <radialGradient id="girl_bg_glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#14B8A6" stopOpacity="0.22" />
          <stop offset="100%" stopColor="#0D9488" stopOpacity="0.05" />
        </radialGradient>
        <linearGradient id="girl_skin" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#F5C6A5" />
          <stop offset="100%" stopColor="#E2AC89" />
        </linearGradient>
        <linearGradient id="girl_pinafore" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#0F766E" />
          <stop offset="100%" stopColor="#042F2E" />
        </linearGradient>
        <linearGradient id="girl_hair" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#242124" />
          <stop offset="100%" stopColor="#111113" />
        </linearGradient>
      </defs>

      {/* Background circular halo */}
      <circle cx="60" cy="60" r="56" fill="url(#girl_bg_glow)" stroke="#0D9488" strokeWidth="1.5" strokeOpacity="0.3" />

      {/* Shoulders & Uniform */}
      <path
        d="M20 114 C20 95, 36 86, 60 86 C84 86, 100 95, 100 114 Z"
        fill="url(#girl_pinafore)"
      />
      {/* Crisp White Shirt Collar & V-Neck Inset */}
      <polygon points="60,86 46,106 74,106" fill="#F8FAFC" />
      <polygon points="60,98 52,114 68,114" fill="#E2E8F0" />
      {/* Uniform Lapel Edges */}
      <path d="M46 88 L54 114" stroke="#0F766E" strokeWidth="2" strokeLinecap="round" />
      <path d="M74 88 L66 114" stroke="#0F766E" strokeWidth="2" strokeLinecap="round" />
      {/* School Crest / Badge */}
      <circle cx="75" cy="102" r="3.5" fill="#F59E0B" />
      <circle cx="75" cy="102" r="2" fill="#B45309" />

      {/* Braids (Left & Right Plaits with Ribbons) */}
      {/* Left braid */}
      <path d="M34 56 C26 66, 26 80, 29 96" stroke="url(#girl_hair)" strokeWidth="6" strokeLinecap="round" />
      <circle cx="29" cy="94" r="3.5" fill="#EF4444" /> {/* Ribbon */}
      {/* Right braid */}
      <path d="M86 56 C94 66, 94 80, 91 96" stroke="url(#girl_hair)" strokeWidth="6" strokeLinecap="round" />
      <circle cx="91" cy="94" r="3.5" fill="#EF4444" /> {/* Ribbon */}

      {/* Neck */}
      <rect x="54" y="74" width="12" height="15" rx="3" fill="#E2AC89" />

      {/* Head / Face */}
      <ellipse cx="60" cy="58" rx="22" ry="24" fill="url(#girl_skin)" />

      {/* Neat Hair (Bangs & Parting) */}
      <path
        d="M38 56 C38 34, 52 30, 60 30 C68 30, 82 34, 82 56 C82 50, 77 40, 60 40 C43 40, 38 50, 38 56 Z"
        fill="url(#girl_hair)"
      />
      {/* Front bangs detail */}
      <path d="M42 45 C48 41, 56 42, 60 46" stroke="#242124" strokeWidth="3" strokeLinecap="round" />
      <path d="M78 45 C72 41, 64 42, 60 46" stroke="#242124" strokeWidth="3" strokeLinecap="round" />

      {/* Small Ears */}
      <circle cx="38" cy="59" r="3.5" fill="#E2AC89" />
      <circle cx="82" cy="59" r="3.5" fill="#E2AC89" />
      <circle cx="38" cy="60" r="1.5" fill="#F59E0B" /> {/* Earring stud */}
      <circle cx="82" cy="60" r="1.5" fill="#F59E0B" />

      {/* Eyebrows */}
      <path d="M49 50 Q53 48 56 50" stroke="#2D2520" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M64 50 Q67 48 71 50" stroke="#2D2520" strokeWidth="1.6" strokeLinecap="round" />

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
      <circle cx="47" cy="63" r="3.5" fill="#F87171" fillOpacity="0.35" />
      <circle cx="73" cy="63" r="3.5" fill="#F87171" fillOpacity="0.35" />

      {/* Small Nose */}
      <path d="M60 58 Q61 62 59 63" stroke="#D18E66" strokeWidth="1.3" strokeLinecap="round" />

      {/* Friendly Smile */}
      <path d="M54 67 Q60 72 66 67" stroke="#A83F3F" strokeWidth="2" strokeLinecap="round" fill="none" />
    </svg>
  )
}
