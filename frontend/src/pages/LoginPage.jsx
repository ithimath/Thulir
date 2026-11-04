import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext.jsx'

export default function LoginPage() {
  const { t } = useTranslation()
  const { login } = useAuth()
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
        <div className="mb-8 text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-primary-container mb-4">
            <span className="material-symbols-outlined text-on-primary text-[28px]">school</span>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface">{t('app.name')}</h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">{t('app.subtitle')}</p>
        </div>

        {/* Card */}
        <div className="bg-surface-container-lowest rounded-xl shadow-sm p-6">
          <h2 className="font-headline-sm text-headline-sm text-on-surface mb-6">{t('auth.title')}</h2>

          {error && (
            <div className="mb-4 px-3 py-2 rounded bg-error-container text-on-error-container font-body-sm text-body-sm flex items-start gap-2">
              <span className="material-symbols-outlined text-[16px] mt-0.5 text-error">error</span>
              {error}
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
        </div>

        {/* Disclaimer */}
        <p className="mt-6 font-body-sm text-body-sm text-on-surface-variant text-center px-2">
          {t('app.disclaimer')}
        </p>
      </div>
    </div>
  )
}

