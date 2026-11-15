import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiGet, apiPost } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import Badge from '../components/Badge.jsx'
import StudentAvatar from '../components/StudentAvatar.jsx'

function KPICard({ label, value, icon, iconClass, sub, subClass, accentBorder }) {
  return (
    <div className={`bg-surface-container-lowest p-4 rounded-xl shadow-sm border border-outline-variant/25 hover:shadow-md hover:border-outline-variant/40 transition-all duration-200 flex flex-col justify-between ${accentBorder || ''}`}>
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline font-semibold">{label}</span>
          <div className="w-8 h-8 rounded-lg bg-surface-container-low flex items-center justify-center">
            <span className={`material-symbols-outlined text-[20px] ${iconClass}`}>{icon}</span>
          </div>
        </div>
        <div className="flex items-baseline gap-2 mt-1">
          <span className="font-numeric-metric text-numeric-metric text-on-surface font-bold tracking-tight">{value}</span>
        </div>
      </div>
      {sub && (
        <div className={`mt-3 pt-1.5 bg-surface-container-low px-2.5 py-1 rounded-lg flex justify-between items-center font-label-sm text-label-sm ${subClass || 'text-on-surface-variant'}`}>
          {sub}
        </div>
      )}
    </div>
  )
}

export default function OverviewPage() {
  const { t } = useTranslation()
  const { role } = useAuth()

  const [stats, setStats] = useState(null)
  const [qualityStats, setQualityStats] = useState(null)
  const [indicators, setIndicators] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [runningEngine, setRunningEngine] = useState(false)
  const [engineResult, setEngineResult] = useState(null)

  useEffect(() => {
    Promise.all([
      apiGet('/api/students?page_size=1'),
      apiGet('/api/indicators?page_size=5&status=Needs+Review'),
      apiGet('/api/indicators?page_size=1'),
      apiGet('/api/data-quality/summary').catch(() => null),
    ])
      .then(([studentsRes, needsReviewRes, allIndRes, qualityRes]) => {
        setStats({
          total_students: studentsRes.total,
          needs_review: needsReviewRes.total,
          all_indicators: allIndRes.total,
        })
        setQualityStats(qualityRes)
        setIndicators(needsReviewRes.items || [])
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const handleRunEngine = async () => {
    setRunningEngine(true)
    setEngineResult(null)
    try {
      const res = await apiPost('/api/indicators/run-engine', {})
      setEngineResult(res.message)
      // Refresh stats
      const [needsReviewRes, allIndRes] = await Promise.all([
        apiGet('/api/indicators?page_size=5&status=Needs+Review'),
        apiGet('/api/indicators?page_size=1'),
      ])
      setStats(s => ({ ...s, needs_review: needsReviewRes.total, all_indicators: allIndRes.total }))
      setIndicators(needsReviewRes.items || [])
    } catch (err) {
      setEngineResult('Error: ' + err.message)
    } finally {
      setRunningEngine(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-10 text-center font-body-sm text-body-sm text-error">
        {t('common.error')}: {error}
      </div>
    )
  }

  return (
    <div className="flex flex-col w-full">
      {/* Header bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
              {t('overview.title')}
            </span>
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
              {t('overview.live_sync')}
            </span>
          </div>
          <p className="font-body-md text-body-md text-on-surface-variant">{t('overview.subtitle')}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {role?.role_name === 'admin' && (
            <button
              onClick={handleRunEngine}
              disabled={runningEngine}
              className="h-9 px-4 bg-secondary text-on-secondary hover:bg-on-secondary-container font-label-md text-label-md rounded flex items-center gap-2 shadow-sm transition-colors disabled:opacity-60"
            >
              {runningEngine ? (
                <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
              ) : (
                <span className="material-symbols-outlined text-[16px]">assignment_turned_in</span>
              )}
              {t('overview.initiate_review')}
            </button>
          )}
        </div>
      </div>

      {/* Engine result message */}
      {engineResult && (
        <div className="mb-4 px-3 py-2 rounded bg-surface-container text-on-surface font-body-sm text-body-sm">
          {engineResult}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 mb-4">
        <KPICard
          label={t('overview.kpi_total_enrolled')}
          value={stats?.total_students ?? '—'}
          icon="groups"
          iconClass="text-secondary"
          sub={<span>{t('common.student')}</span>}
        />
        <KPICard
          label={t('overview.kpi_requiring_review')}
          value={stats?.needs_review ?? '—'}
          icon="notification_important"
          iconClass="text-error"
          sub={
            <span className="text-error font-medium">
              {t('status.needs_review')}
            </span>
          }
        />
        <KPICard
          label="Total Indicators"
          value={stats?.all_indicators ?? '—'}
          icon="flag"
          iconClass="text-secondary"
          sub={<span>{t('common.awaiting_review')}</span>}
        />
        <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm border border-outline-variant/25 hover:shadow-md hover:border-outline-variant/40 transition-all duration-200 flex flex-col justify-between border-l-4 border-l-amber-500">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline font-semibold">
                {t('data_quality.title')}
              </span>
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <span className="material-symbols-outlined text-[20px] text-amber-600">verified_user</span>
              </div>
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="font-numeric-metric text-numeric-metric text-on-surface font-bold tracking-tight">
                {qualityStats ? `${qualityStats.profile_completeness_pct}%` : '—'}
              </span>
              <span className="font-label-sm text-label-sm text-on-surface-variant font-medium">profile completeness</span>
            </div>
          </div>
          <div className="mt-3 pt-1.5 bg-surface-container-low px-2.5 py-1 rounded-lg flex justify-between items-center font-label-sm text-label-sm">
            <span className={qualityStats?.total_issues_count > 0 ? 'text-amber-700 font-semibold' : 'text-emerald-700 font-medium'}>
              {qualityStats?.total_issues_count ?? 0} {t('data_quality.total_issues')}
            </span>
            <Link to="/data-import?tab=quality" className="text-secondary hover:underline font-semibold flex items-center gap-0.5">
              Inspect <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Warning disclaimer */}
      <div className="mb-4 px-4 py-3 bg-surface-container-low rounded-xl border-l-4 border-secondary">
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          <strong className="text-on-surface">ℹ {t('app.name')}:</strong> {t('app.disclaimer')}
        </p>
      </div>

      {/* Recent indicators needing review */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-outline-variant flex items-center justify-between">
          <span className="font-headline-sm text-headline-sm text-on-surface">
            {t('overview.chart_drivers_title')}
          </span>
          <Link
            to="/early-warnings"
            className="font-label-md text-label-md text-secondary hover:underline"
          >
            View all →
          </Link>
        </div>
        {indicators.length === 0 ? (
          <div className="px-4 py-8 text-center font-body-sm text-body-sm text-on-surface-variant">
            {t('common.no_data')}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="bg-surface-container">
                <th className="px-4 py-2 text-left font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                  {t('common.student')}
                </th>
                <th className="px-4 py-2 text-left font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                  Rule
                </th>
                <th className="px-4 py-2 text-left font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                  {t('common.priority')}
                </th>
                <th className="px-4 py-2 text-left font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                  {t('common.status')}
                </th>
              </tr>
            </thead>
            <tbody>
              {indicators.map((ind, idx) => (
                <tr key={ind.id} className={idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'}>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2.5">
                      <StudentAvatar student={ind.student} size={32} />
                      <div>
                        <Link
                          to={`/students/${ind.student?.id}`}
                          className="font-label-md text-label-md text-secondary hover:underline"
                        >
                          {ind.student?.full_name}
                        </Link>
                        <div className="font-body-sm text-body-sm text-on-surface-variant">
                          {ind.student?.grade}-{ind.student?.section}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    <span className="font-label-sm text-label-sm text-on-surface">{ind.rule_code}</span>
                    <div className="font-body-sm text-body-sm text-on-surface-variant truncate max-w-xs">
                      {ind.plain_explanation}
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    <Badge variant={ind.priority?.toLowerCase()}>{ind.priority}</Badge>
                  </td>
                  <td className="px-4 py-2">
                    <Badge variant="needs_review">{ind.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

