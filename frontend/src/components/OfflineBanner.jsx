import { useNetwork } from '../context/NetworkContext.jsx'

export default function OfflineBanner() {
  const { isOnline } = useNetwork()

  if (isOnline) return null

  return (
    <div
      role="alert"
      data-testid="offline-banner"
      className="bg-amber-600 text-white px-4 py-2.5 shadow-md flex items-center justify-between z-50 text-label-md"
    >
      <div className="flex items-center gap-2">
        <span className="material-symbols-outlined text-[20px]">cloud_off</span>
        <span>
          <strong>Offline Shell Mode:</strong> Network disconnected. Data-entry and live data updates are disabled to safeguard records and student privacy. No student personal data is stored offline.
        </span>
      </div>
      <span className="bg-amber-800/60 px-2 py-0.5 rounded text-label-sm font-semibold uppercase">
        Read-Only / Disabled
      </span>
    </div>
  )
}

