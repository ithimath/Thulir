import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext.jsx'
import ThulirLogo from '../components/ThulirLogo.jsx'

export default function LoginPage() {
  const { t } = useTranslation()
  const { login, loginDemo } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(username.trim(), password)
      navigate('/overview', { replace: true })
    } catch (err) {
      if (err.status === 401) {
        setError(t('auth.invalid_credentials'))
      } else if (err.status === 404 || err.message === 'HTTP 404' || err.message?.includes('404')) {
        setError(t('auth.server_unavailable'))
      } else if (err.status === 503 || err.status === 502 || err.message?.includes('unreachable') || err.message?.includes('Failed to fetch')) {
        setError(t('auth.connection_error'))
      } else {
        setError(err.message || t('common.error'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Logo area */}
        <div className="mb-8 text-center flex flex-col items-center">
          <div className="relative p-3 rounded-2xl bg-gradient-to-br from-slate-900 to-teal-950 ring-1 ring-teal-500/30 shadow-lg shadow-teal-950/20 mb-3 flex items-center justify-center">
            <ThulirLogo size={48} />
          </div>
          <div className="flex items-center gap-2 justify-center">
            <h1 className="font-brand font-extrabold text-[28px] text-on-surface tracking-wider">
              {t('app.name')}
            </h1>
            <span className="px-2 py-0.5 rounded text-xs font-semibold bg-secondary/15 text-secondary border border-secondary/30">
              துளிர்
            </span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{t('app.subtitle')}</p>
        </div>

        {/* Card */}
        <div className="bg-surface-container-lowest rounded-xl shadow-sm p-6">
          <h2 className="font-headline-sm text-headline-sm text-on-surface mb-6">{t('auth.title')}</h2>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-error-container text-on-error-container font-body-sm text-body-sm space-y-2">
              <div className="flex items-start gap-2">
                <span className="material-symbols-outlined text-[18px] mt-0.5 text-error flex-shrink-0">error</span>
                <span className="leading-snug">{error}</span>
              </div>
              {(error.includes('unreachable') || error.includes('backend') || error.includes('404') || error.includes('503') || error.includes('connect')) && (
                <div className="pt-2 border-t border-error/20 flex items-center justify-between">
                  <span className="text-[11px] text-on-error-container/80">Evaluate offline?</span>
                  <button
                    type="button"
                    onClick={() => {
                      loginDemo(username || 'admin')
                      navigate('/overview', { replace: true })
                    }}
                    className="px-2.5 py-1 text-[11px] font-semibold bg-surface-container-lowest text-on-surface hover:bg-surface-container rounded transition-colors shadow-sm"
                  >
                    Enter Demo Mode →
                  </button>
                </div>
              )}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block font-label-md text-label-md text-on-surface mb-1">
                {t('auth.username')}
              </label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                autoComplete="username"
                className="w-full h-10 px-3 bg-surface-container-low text-on-surface font-body-md text-body-md rounded border border-outline-variant focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary"
                disabled={loading}
              />
            </div>
            <div>
              <label className="block font-label-md text-label-md text-on-surface mb-1">
                {t('auth.password')}
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full h-10 px-3 bg-surface-container-low text-on-surface font-body-md text-body-md rounded border border-outline-variant focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary"
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full h-10 bg-secondary text-on-secondary font-label-md text-label-md rounded flex items-center justify-center gap-2 hover:bg-on-secondary-container transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading && (
                <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
              )}
              {loading ? t('auth.logging_in') : t('auth.login_button')}
            </button>
          </form>

          {/* Quick Fill Demo Roles */}
          <div className="mt-4 pt-4 border-t border-outline-variant/30">
            <span className="text-[11px] font-semibold text-outline uppercase tracking-wider block mb-2">
              Demo Access Quick-Fill:
            </span>
            <div className="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                onClick={() => { setUsername('admin'); setPassword('Password123!'); setError(null); }}
                className="px-2 py-1.5 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface text-[11px] font-medium transition-colors text-center"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => { setUsername('teacher'); setPassword('Password123!'); setError(null); }}
                className="px-2 py-1.5 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface text-[11px] font-medium transition-colors text-center"
              >
                Teacher
              </button>
              <button
                type="button"
                onClick={() => { setUsername('counsellor'); setPassword('Password123!'); setError(null); }}
                className="px-2 py-1.5 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface text-[11px] font-medium transition-colors text-center"
              >
                Counselor
              </button>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <p className="mt-6 font-body-sm text-body-sm text-on-surface-variant text-center px-2">
          {t('app.disclaimer')}
        </p>
      </div>
    </div>
  )
}

