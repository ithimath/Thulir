import { createContext, useContext, useState, useCallback, useMemo } from 'react'
import ToastContainer from '../components/ToastContainer.jsx'
import ConfirmationModal from '../components/ConfirmationModal.jsx'
import { parseError } from '../utils/errorHandler.js'

const NotificationContext = createContext(null)

let nextId = 1

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([])
  const [dialogState, setDialogState] = useState(null)

  const dismiss = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const clearAll = useCallback(() => {
    setNotifications([])
  }, [])

  const showNotification = useCallback((payload) => {
    const id = payload.id || `notif_${Date.now()}_${nextId++}`
    const newNotif = {
      id,
      type: payload.type || 'info',
      title: payload.title || '',
      message: payload.message || '',
      listItems: payload.listItems || null,
      suggestion: payload.suggestion || null,
      action: payload.action || null,
      duration: payload.duration !== undefined
        ? payload.duration
        : payload.type === 'error'
        ? 7500
        : payload.type === 'warning'
        ? 6000
        : 4500,
    }

    setNotifications(prev => {
      // Limit to 4 visible toasts to avoid overwhelming screen
      const filtered = prev.filter(n => n.id !== id)
      return [newNotif, ...filtered].slice(0, 4)
    })

    return id
  }, [])

  // Convenience helper methods
  const notify = useMemo(() => ({
    success: (message, title = 'Success', options = {}) =>
      showNotification({ type: 'success', title, message, ...options }),

    error: (message, title = 'Error', options = {}) =>
      showNotification({ type: 'error', title, message, ...options }),

    warning: (message, title = 'Warning', options = {}) =>
      showNotification({ type: 'warning', title, message, ...options }),

    info: (message, title = 'Information', options = {}) =>
      showNotification({ type: 'info', title, message, ...options }),

    parseError: (err, defaultTitle = 'Action Failed') => {
      const parsed = parseError(err, defaultTitle)
      return showNotification(parsed)
    },
  }), [showNotification])

  // Native confirm() replacement returning Promise<boolean>
  const confirm = useCallback((options = {}) => {
    return new Promise((resolve) => {
      setDialogState({
        isOpen: true,
        title: options.title || 'Confirm Action',
        message: options.message || 'Are you sure you want to proceed?',
        confirmText: options.confirmText || 'Confirm',
        cancelText: options.cancelText || 'Cancel',
        type: options.type || 'primary',
        onResolve: (val) => {
          setDialogState(null)
          resolve(val)
        },
      })
    })
  }, [])

  const handleConfirm = () => {
    dialogState?.onResolve?.(true)
  }

  const handleCancel = () => {
    dialogState?.onResolve?.(false)
  }

  return (
    <NotificationContext.Provider
      value={{
        notify,
        showNotification,
        dismiss,
        clearAll,
        confirm,
      }}
    >
      {children}
      <ToastContainer notifications={notifications} onDismiss={dismiss} />
      <ConfirmationModal
        dialogState={dialogState}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </NotificationContext.Provider>
  )
}

export function useNotification() {
  const ctx = useContext(NotificationContext)
  if (!ctx) {
    throw new Error('useNotification must be used within a NotificationProvider')
  }
  return ctx
}

