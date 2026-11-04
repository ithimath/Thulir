import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { apiGet } from '../api/client.js'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend
} from 'recharts'

const COLORS = ['#ba1a1a', '#006a61', '#131b2e', '#f59e0b', '#3b82f6']

export default function ReportsPage() {
  const { t } = useTranslation()
  const [stats, setStats] = useState(null)
  const [trajectory, setTrajectory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      apiGet('/api/reports/dashboard-stats'),
      apiGet('/api/reports/trajectory'),
    ])
      .then(([statsRes, trajRes]) => {
        setStats(statsRes)
        setTrajectory(trajRes.trajectory || [])
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const downloadCSV = (type) => {
    window.open(`/api/reports/export?report_type=${type}`, '_blank')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
      </div>
    )
  }

  if (error) {
    return <div className="py-10 text-center font-body-sm text-body-sm text-error">{error}</div>
  }

  const categoryData = Object.entries(stats?.indicators_by_category || {}).map(([key, val]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value: val,
  }))

  const interventionData = Object.entries(stats?.interventions_by_type || {}).map(([key, val]) => ({
    name: key.replace('_', ' ').toUpperCase(),
    count: val,
  }))

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <div>
          <span className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            {t('nav.reports')} & Analytics
          </span>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Aggregated institutional indicators, longitudinal progress, and compliance summaries.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => downloadCSV('students_review')}
            className="h-9 px-3 bg-surface-container text-on-surface hover:bg-surface-container-high rounded font-label-md text-label-md flex items-center gap-1 shadow-sm transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">file_download</span>
            <span>Export Indicators</span>
          </button>
          <button
            onClick={() => downloadCSV('cases_summary')}
            className="h-9 px-3 bg-surface-container text-on-surface hover:bg-surface-container-high rounded font-label-md text-label-md flex items-center gap-1 shadow-sm transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">file_download</span>
            <span>Export Cases</span>
          </button>
          <button
            onClick={() => downloadCSV('interventions_log')}
            className="h-9 px-3 bg-surface-container text-on-surface hover:bg-surface-container-high rounded font-label-md text-label-md flex items-center gap-1 shadow-sm transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">file_download</span>
            <span>Export Interventions</span>
          </button>
          <button
            onClick={() => downloadCSV('attendance_summary')}
            className="h-9 px-3 bg-secondary text-on-secondary hover:bg-on-secondary-container rounded font-label-md text-label-md flex items-center gap-1 shadow-sm transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">file_download</span>
            <span>Export Attendance</span>
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm">
          <span className="font-label-sm text-label-sm uppercase text-outline">Total Enrolled Cohort</span>
          <div className="font-numeric-metric text-numeric-metric text-on-surface mt-1">{stats?.total_enrolled}</div>
        </div>
        <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm">
          <span className="font-label-sm text-label-sm uppercase text-outline">Requiring Review</span>
          <div className="font-numeric-metric text-numeric-metric text-error mt-1">{stats?.requiring_review}</div>
        </div>
        <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm">
          <span className="font-label-sm text-label-sm uppercase text-outline">Active Support Cases</span>
          <div className="font-numeric-metric text-numeric-metric text-secondary mt-1">{stats?.active_cases}</div>
        </div>
        <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm">
          <span className="font-label-sm text-label-sm uppercase text-outline">Overdue Follow-ups</span>
          <div className="font-numeric-metric text-numeric-metric text-amber-600 mt-1">{stats?.overdue_follow_ups}</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        {/* Longitudinal Trajectory */}
        <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm">
          <h2 className="font-headline-sm text-headline-sm text-on-surface mb-1">
            {t('overview.chart_trajectory_title')}
          </h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant mb-4">
            {t('overview.chart_trajectory_desc')}
          </p>
          <div className="h-64 w-full">
            {trajectory.length === 0 ? (
              <div className="flex items-center justify-center h-full font-body-sm text-body-sm text-on-surface-variant">
                No historical periods recorded
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trajectory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="period" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="avg_attendance" stroke="#006a61" strokeWidth={2} name="Avg Attendance %" />
                  <Line type="monotone" dataKey="avg_assessment" stroke="#ba1a1a" strokeWidth={2} name="Avg Assessment %" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Indicators Breakdown by Category */}
        <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm">
          <h2 className="font-headline-sm text-headline-sm text-on-surface mb-1">
            {t('overview.chart_drivers_title')}
          </h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant mb-4">
            Distribution of early-warning alerts across risk domains.
          </p>
          <div className="h-64 w-full">
            {categoryData.length === 0 ? (
              <div className="flex items-center justify-center h-full font-body-sm text-body-sm text-on-surface-variant">
                No active indicators
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

