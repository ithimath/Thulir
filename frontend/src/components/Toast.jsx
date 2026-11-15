import { useState, useEffect } from 'react'

const TYPE_CONFIG = {
  error: {
    icon: 'error',
    iconColor: 'text-rose-600 dark:text-rose-400',
    borderColor: 'border-rose-300 dark:border-rose-800/80',
    bgColor: 'bg-rose-50/95 dark:bg-rose-950/90',
    textColor: 'text-rose-950 dark:text-rose-100',
    titleColor: 'text-rose-900 dark:text-rose-200',
    accentBar: 'bg-rose-600 dark:bg-rose-500',
    badgeBg: 'bg-rose-100 dark:bg-rose-900/60 text-rose-800 dark:text-rose-200 border-rose-300 dark:border-rose-700/60',
  },
  warning: {
    icon: 'warning',
    iconColor: 'text-amber-600 dark:text-amber-400',
    borderColor: 'border-amber-300 dark:border-amber-800/80',
    bgColor: 'bg-amber-50/95 dark:bg-amber-950/90',
    textColor: 'text-amber-950 dark:text-amber-100',
    titleColor: 'text-amber-900 dark:text-amber-200',
    accentBar: 'bg-amber-500 dark:bg-amber-400',
    badgeBg: 'bg-amber-100 dark:bg-amber-900/60 text-amber-900 dark:text-amber-200 border-amber-300 dark:border-amber-700/60',
  },
  success: {
    icon: 'check_circle',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    borderColor: 'border-emerald-300 dark:border-emerald-800/80',
    bgColor: 'bg-emerald-50/95 dark:bg-emerald-950/90',
    textColor: 'text-emerald-950 dark:text-emerald-100',
    titleColor: 'text-emerald-900 dark:text-emerald-200',
    accentBar: 'bg-emerald-600 dark:bg-emerald-500',
    badgeBg: 'bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200 border-emerald-300 dark:border-emerald-700/60',
  },
  info: {
    icon: 'info',
    iconColor: 'text-sky-600 dark:text-sky-400',
    borderColor: 'border-sky-300 dark:border-sky-800/80',
    bgColor: 'bg-sky-50/95 dark:bg-sky-950/90',
    textColor: 'text-sky-950 dark:text-sky-100',
    titleColor: 'text-sky-900 dark:text-sky-200',
    accentBar: 'bg-sky-600 dark:bg-sky-500',
    badgeBg: 'bg-sky-100 dark:bg-sky-900/60 text-sky-800 dark:text-sky-200 border-sky-300 dark:border-sky-700/60',
  },
}

export default function Toast({ notification, onDismiss }) {
  const {
    id,
    type = 'info',
    title,
    message,
    listItems,
    suggestion,
    action,
    duration = 5000,
  } = notification

  const config = TYPE_CONFIG[type] || TYPE_CONFIG.info
  const [isPaused, setIsPaused] = useState(false)
  const [remaining, setRemaining] = useState(duration)

  // Progress countdown timer with pause-on-hover
  useEffect(() => {
    if (duration <= 0 || isPaused) return

    const interval = 50
    const timer = setInterval(() => {
      setRemaining(prev => {
        if (prev <= interval) {
          clearInterval(timer)
          onDismiss(id)
          return 0
        }
        return prev - interval
      })
    }, interval)

    return () => clearInterval(timer)
  }, [id, duration, isPaused, onDismiss])

  const progressPct = duration > 0 ? (remaining / duration) * 100 : 0

  return (
    <div
      role="alert"
      aria-live="assertive"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      className={`relative w-full sm:max-w-md rounded-xl border shadow-lg backdrop-blur-md overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-top-4 ${config.bgColor} ${config.borderColor} ${config.textColor}`}
    >
      {/* Top accent bar */}
      <div className={`h-1 w-full ${config.accentBar}`} />

      <div className="p-4 flex items-start gap-3">
        {/* Type Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <span className={`material-symbols-outlined text-[24px] ${config.iconColor}`}>
            {config.icon}
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 pr-2">
          {title && (
            <h4 className={`font-label-md text-sm font-bold tracking-tight ${config.titleColor}`}>
              {title}
            </h4>
          )}
          {message && (
            <p className="font-body-sm text-xs mt-1 leading-relaxed opacity-90 break-words">
              {message}
            </p>
          )}

          {/* Structured List Items (e.g. missing columns) */}
          {Array.isArray(listItems) && listItems.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {listItems.map((item, idx) => (
                <span
                  key={idx}
                  className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold border ${config.badgeBg}`}
                >
                  <span className="material-symbols-outlined text-[13px] mr-1 opacity-75">
                    {type === 'error' ? 'close' : 'check'}
                  </span>
                  {item}
                </span>
              ))}
            </div>
          )}

          {/* Actionable Suggestion */}
          {suggestion && (
            <p className="mt-2 text-[11px] font-medium opacity-80 italic">
              💡 {suggestion}
            </p>
          )}

          {/* Optional Action Button */}
          {action && (
            <div className="mt-3">
              <button
                onClick={() => {
                  action.onClick?.()
                  onDismiss(id)
                }}
                className={`text-xs font-semibold px-2.5 py-1 rounded border shadow-sm transition-colors ${config.badgeBg} hover:opacity-90`}
              >
                {action.label}
              </button>
            </div>
          )}
        </div>

        {/* Dismiss Button */}
        <button
          onClick={() => onDismiss(id)}
          aria-label="Dismiss notification"
          className="flex-shrink-0 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded p-1 transition-colors"
        >
          <span className="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      {/* Countdown progress line */}
      {duration > 0 && (
        <div className="h-0.5 w-full bg-black/5 dark:bg-white/10">
          <div
            className={`h-full transition-all duration-75 ${config.accentBar}`}
            style={{ width: `${progressPct}%` }}
          />
        </div>
      )}
    </div>
  )
}

