import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiGet } from '../api/client.js'
import Badge from '../components/Badge.jsx'
import DemoDataBanner from '../components/DemoDataBanner.jsx'
import StudentAvatar from '../components/StudentAvatar.jsx'

export default function StudentDirectoryPage() {
  const { t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filter state
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [grade, setGrade] = useState('')
  const [section, setSection] = useState('')
  const [dataOrigin, setDataOrigin] = useState('')
  const [page, setPage] = useState(1)

  const fetchStudents = useCallback(() => {
    setLoading(true)
    const params = new URLSearchParams({ page, page_size: 25 })
    if (search) params.set('search', search)
    if (grade) params.set('grade', grade)
    if (section) params.set('section', section)
    if (dataOrigin) params.set('data_origin', dataOrigin)

    apiGet(`/api/students?${params}`)
      .then(res => { setData(res); setError(null) })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [search, grade, section, dataOrigin, page])

  useEffect(() => { fetchStudents() }, [fetchStudents])

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    setSearchParams(search ? { search } : {})
    fetchStudents()
  }

  const clearFilters = () => {
    setSearch(''); setGrade(''); setSection(''); setDataOrigin(''); setPage(1)
    setSearchParams({})
  }

  const isMockActive = dataOrigin === 'mock' || (data?.items?.some(s => s.data_origin === 'mock'))

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <div>
          <span className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            {t('nav.students')}
          </span>
          {data && (
            <span className="ml-2 font-label-sm text-label-sm text-on-surface-variant">
              {data.total} records
            </span>
          )}
        </div>
      </div>

      {/* Filters */}
      <form onSubmit={handleSearch} className="flex flex-wrap gap-2 mb-4">
        <div className="relative">
          <span className="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-[16px] text-outline">search</span>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={t('header.search_placeholder')}
            className="h-9 pl-7 pr-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary w-64"
          />
        </div>
        <select
          value={grade}
          onChange={e => { setGrade(e.target.value); setPage(1) }}
          className="h-9 px-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant focus:outline-none"
        >
          <option value="">All Grades</option>
          {[6,7,8,9,10,11,12].map(g => <option key={g} value={g}>Grade {g}</option>)}
        </select>
        <select
          value={section}
          onChange={e => { setSection(e.target.value); setPage(1) }}
          className="h-9 px-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant focus:outline-none"
        >
          <option value="">All Sections</option>
          {['A','B','C','D'].map(s => <option key={s} value={s}>Section {s}</option>)}
        </select>
        <select
          value={dataOrigin}
          onChange={e => { setDataOrigin(e.target.value); setPage(1) }}
          className="h-9 px-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant focus:outline-none"
          title="Filter by Data Origin"
        >
          <option value="">All Data Origins</option>
          <option value="dataset">Cleaned Datasets Only</option>
          <option value="mock">Synthetic / Demo Mock Only</option>
          <option value="user">User Created Only</option>
        </select>
        <button
          type="submit"
          className="h-9 px-4 bg-secondary text-on-secondary font-label-md text-label-md rounded hover:bg-on-secondary-container transition-colors"
        >
          {t('common.search')}
        </button>
        <button
          type="button"
          onClick={clearFilters}
          className="h-9 px-3 bg-surface-container text-on-surface font-label-md text-label-md rounded hover:bg-surface-container-high transition-colors"
        >
          {t('common.clear_filters')}
        </button>
      </form>

      {/* Demo data banner */}
      {isMockActive && (
        <DemoDataBanner
          origin={dataOrigin}
          onClearFilter={dataOrigin === 'mock' ? () => setDataOrigin('') : null}
        />
      )}

      {/* Table */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
          </div>
        ) : error ? (
          <div className="py-10 text-center font-body-sm text-body-sm text-error">{error}</div>
        ) : data?.items?.length === 0 ? (
          <div className="py-10 text-center font-body-sm text-body-sm text-on-surface-variant">{t('common.no_data')}</div>
        ) : (
          <>
            <div className="overflow-x-auto w-full">
              <table className="w-full">
              <thead>
                <tr className="bg-surface-container border-b border-outline-variant">
                  <th className="px-4 py-3 text-left font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">EMIS ID</th>
                  <th className="px-4 py-3 text-left font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">{t('common.student')}</th>
                  <th className="px-4 py-3 text-left font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">{t('common.class_sec')}</th>
                  <th className="px-4 py-3 text-right font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Attendance</th>
                  <th className="px-4 py-3 text-center font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Indicators</th>
                  <th className="px-4 py-3 text-center font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Cases</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((s, idx) => (
                  <tr
                    key={s.id}
                    className={`${idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'} hover:bg-surface-container transition-colors`}
                  >
                    <td className="px-4 py-2 font-numeric-table text-numeric-table text-on-surface-variant">{s.emis_id}</td>
                    <td className="px-4 py-2">
                      <div className="flex items-center gap-3">
                        <StudentAvatar student={s} size={36} />
                        <div>
                          <div className="flex items-center gap-2">
                            <Link
                              to={`/students/${s.id}`}
                              className="font-label-md text-label-md text-secondary hover:underline"
                            >
                              {s.full_name}
                            </Link>
                            {s.data_origin === 'mock' && (
                              <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-700/50">
                                DEMO
                              </span>
                            )}
                            {s.data_origin === 'dataset' && (
                              <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-700/50">
                                DATASET
                              </span>
                            )}
                          </div>
                          <div className="font-body-sm text-body-sm text-on-surface-variant">{s.gender}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-2 font-label-md text-label-md text-on-surface">
                      {s.class_section ? `${s.class_section.grade}-${s.class_section.section}` : '—'}
                    </td>
                    <td className="px-4 py-2 text-right">
                      {s.latest_attendance_pct != null ? (
                        <span className={`font-numeric-table text-numeric-table ${s.latest_attendance_pct < 75 ? 'text-error font-semibold' : 'text-on-surface'}`}>
                          {s.latest_attendance_pct.toFixed(1)}%
                        </span>
                      ) : (
                        <span className="font-body-sm text-body-sm text-on-surface-variant">{t('common.insufficient_data')}</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {s.open_indicators_count > 0 ? (
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-error text-on-error font-label-sm text-label-sm">
                          {s.open_indicators_count}
                        </span>
                      ) : (
                        <span className="font-body-sm text-body-sm text-on-surface-variant">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {s.open_cases_count > 0 ? (
                        <Badge variant="in_progress">{s.open_cases_count}</Badge>
                      ) : (
                        <span className="font-body-sm text-body-sm text-on-surface-variant">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="px-4 py-3 border-t border-outline-variant flex items-center justify-between">
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  Page {data.page} of {data.total_pages} ({data.total} total)
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="h-8 px-3 rounded bg-surface-container text-on-surface font-label-md text-label-md hover:bg-surface-container-high disabled:opacity-50 transition-colors"
                  >
                    ← Prev
                  </button>
                  <button
                    onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                    disabled={page === data.total_pages}
                    className="h-8 px-3 rounded bg-surface-container text-on-surface font-label-md text-label-md hover:bg-surface-container-high disabled:opacity-50 transition-colors"
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

