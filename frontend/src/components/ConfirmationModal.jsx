import { useEffect, useRef } from 'react'

export default function ConfirmationModal({ dialogState, onConfirm, onCancel }) {
  const confirmBtnRef = useRef(null)

  useEffect(() => {
    if (dialogState?.isOpen) {
      confirmBtnRef.current?.focus()

      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          onCancel()
        }
      }
      window.addEventListener('keydown', handleKeyDown)
      return () => window.removeEventListener('keydown', handleKeyDown)
    }
  }, [dialogState?.isOpen, onCancel])

  if (!dialogState?.isOpen) return null

  const {
    title = 'Confirm Action',
    message = 'Are you sure you want to proceed?',
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    type = 'primary', // 'primary' | 'danger' | 'warning'
  } = dialogState

  const typeConfig = {
    danger: {
      icon: 'warning',
      iconColor: 'text-rose-600 dark:text-rose-400',
      btnBg: 'bg-rose-600 hover:bg-rose-700 text-white shadow-rose-950/20',
      badgeBg: 'bg-rose-100 dark:bg-rose-950/60 text-rose-800 dark:text-rose-200',
    },
    warning: {
      icon: 'help',
      iconColor: 'text-amber-600 dark:text-amber-400',
      btnBg: 'bg-amber-600 hover:bg-amber-700 text-white shadow-amber-950/20',
      badgeBg: 'bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200',
    },
    primary: {
      icon: 'help',
      iconColor: 'text-teal-600 dark:text-teal-400',
      btnBg: 'bg-teal-600 hover:bg-teal-700 text-white shadow-teal-950/20',
      badgeBg: 'bg-teal-100 dark:bg-teal-950/60 text-teal-900 dark:text-teal-200',
    },
  }[type] || {
    icon: 'help',
    iconColor: 'text-teal-600 dark:text-teal-400',
    btnBg: 'bg-teal-600 hover:bg-teal-700 text-white',
    badgeBg: 'bg-teal-100 text-teal-900',
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      className="fixed inset-0 z-[10000] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
    >
      <div
        className="w-full max-w-md bg-surface-container-lowest border border-outline-variant/40 rounded-2xl shadow-2xl p-6 overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-start gap-4">
          <div className={`p-2.5 rounded-xl ${typeConfig.badgeBg} flex-shrink-0`}>
            <span className={`material-symbols-outlined text-[24px] ${typeConfig.iconColor}`}>
              {typeConfig.icon}
            </span>
          </div>

          <div className="flex-1 min-w-0">
            <h3 id="confirm-modal-title" className="font-headline-sm text-base font-bold text-on-surface">
              {title}
            </h3>
            <p className="mt-2 font-body-sm text-sm text-on-surface-variant leading-relaxed">
              {message}
            </p>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-outline-variant/20">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 rounded-lg font-label-md text-xs font-semibold text-on-surface hover:bg-surface-container border border-outline-variant/40 transition-colors"
          >
            {cancelText}
          </button>
          <button
            ref={confirmBtnRef}
            type="button"
            onClick={onConfirm}
            className={`px-4 py-2 rounded-lg font-label-md text-xs font-semibold shadow-sm transition-all ${typeConfig.btnBg}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}

