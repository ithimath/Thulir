import Toast from './Toast.jsx'

export default function ToastContainer({ notifications, onDismiss }) {
  if (!notifications || notifications.length === 0) return null

  return (
    <aside
      aria-label="Notifications"
      className="fixed top-4 right-4 z-[9999] flex flex-col gap-2.5 max-w-full w-[calc(100%-2rem)] sm:w-[440px] pointer-events-none"
    >
      {notifications.map(notif => (
        <div key={notif.id} className="pointer-events-auto">
          <Toast notification={notif} onDismiss={onDismiss} />
        </div>
      ))}
    </aside>
  )
}

