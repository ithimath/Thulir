import React from 'react';
import { useTranslation } from 'react-i18next';

export const Badge = ({ variant = 'default', text, count, children, className = '' }) => {
  const { t } = useTranslation();

  // Variants mapped strictly from Stitch Design System:
  // Critical Risk: bg-[#FEE2E2] text-[#991B1B] border-[#FECACA]
  // Early Warning (Moderate): bg-[#FEF3C7] text-[#92400E] border-[#FDE68A]
  // Stable / Monitored: bg-[#D1FAE5] text-[#065F46] border-[#A7F3D0]
  // Administrative / Neutral: bg-[#F1F5F9] text-[#334155] border-[#E2E8F0]
  // High / Red Alert: bg-error-container text-on-error-container

  const variantStyles = {
    critical: 'bg-error-container text-on-error-container border border-error/20 font-semibold',
    high: 'bg-error-container text-on-error-container border border-error/20 font-semibold',
    moderate: 'bg-amber-100 text-amber-900 border border-amber-200 font-semibold',
    low: 'bg-surface-container text-on-surface-variant border border-outline-variant/40',
    monitoring: 'bg-surface-container-high text-on-surface-variant border border-outline-variant/30 font-semibold',
    stable: 'bg-emerald-100 text-emerald-900 border border-emerald-200 font-semibold',
    needs_review: 'bg-error-container text-on-error-container border border-error/20 font-semibold',
    under_review: 'bg-amber-100 text-amber-900 border border-amber-200 font-semibold',
    support_recommended: 'bg-amber-100 text-amber-900 border border-amber-300 font-semibold',
    referred: 'bg-teal-100 text-teal-900 border border-teal-200 font-semibold',
    reviewed: 'bg-emerald-100 text-emerald-900 border border-emerald-200 font-semibold',
    closed: 'bg-surface-container-high text-on-surface-variant border border-outline-variant/40',
    default: 'bg-surface-container text-on-surface border border-outline-variant/30',
  };

  const selectedClass = variantStyles[variant] || variantStyles.default;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] leading-tight font-medium tracking-wide uppercase ${selectedClass} ${className}`}
    >
      {text || children}
      {count !== undefined && (
        <span className="ml-1 px-1.5 py-0.2 rounded-full text-[10px] bg-black/10 dark:bg-white/10">
          {count}
        </span>
      )}
    </span>
  );
};

export default Badge;

