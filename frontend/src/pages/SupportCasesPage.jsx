import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiGet, apiPost } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useNotification } from '../context/NotificationContext.jsx'
import Badge from '../components/Badge.jsx'
import EventTimeline from '../components/EventTimeline.jsx'
import StudentAvatar from '../components/StudentAvatar.jsx'

function InterventionEffectivenessCard({ caseId, interventionId }) {
  const { t } = useTranslation()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const handleToggle = async () => {
    if (!expanded && !data) {
      setLoading(true)
      try {
        const res = await apiGet(`/api/cases/${caseId}/interventions/${interventionId}/effectiveness`)
        setData(res)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    setExpanded(!expanded)
  }

  return (
    <div className="mt-2 border-t border-outline-variant/60 pt-2">
      <button
        type="button"
        onClick={handleToggle}
        className="text-secondary font-label-sm text-label-sm hover:underline flex items-center gap-1"
      >
        <span className="material-symbols-outlined text-[15px]">trending_up</span>
        <span>{expanded ? 'Hide Effectiveness Tracking' : 'View Effectiveness Comparison'}</span>
      </button>

      {expanded && (
        <div className="mt-2 p-3 bg-surface-container-lowest rounded-lg border border-outline-variant font-body-sm text-body-sm">
          {loading ? (
            <div className="py-2 flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px] text-secondary animate-spin">progress_activity</span>
            </div>
          ) : !data ? (
            <p className="text-on-surface-variant">No tracking data available.</p>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-label-sm text-label-sm font-semibold uppercase text-outline">
                  Metric: {data.metric_domain}
                </span>
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  data.status === 'improving' ? 'bg-emerald-50 text-emerald-700' :
                  data.status === 'declining' ? 'bg-error/10 text-error' :
                  data.status === 'insufficient_data' ? 'bg-amber-50 text-amber-800' :
                  'bg-surface-container text-on-surface'
                }`}>
                  {data.status === 'improving' ? t('effectiveness.status_improving') :
                   data.status === 'declining' ? t('effectiveness.status_declining') :
                   data.status === 'insufficient_data' ? t('effectiveness.status_insufficient_data') :
                   t('effectiveness.status_no_significant_change')}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 py-1 text-center font-numeric-table">
                <div className="bg-surface-container-low p-2 rounded">
                  <span className="text-xs text-on-surface-variant block">{t('effectiveness.baseline')}</span>
                  <strong className="text-on-surface text-sm">
                    {data.baseline_value != null ? `${data.baseline_value}` : '—'}
                  </strong>
                </div>
                <div className="bg-surface-container-low p-2 rounded">
                  <span className="text-xs text-on-surface-variant block">{t('effectiveness.current')}</span>
                  <strong className="text-on-surface text-sm">
                    {data.current_value != null ? `${data.current_value}` : '—'}
                  </strong>
                </div>
                <div className="bg-surface-container-low p-2 rounded">
                  <span className="text-xs text-on-surface-variant block">{t('effectiveness.change')}</span>
                  <strong className={`text-sm ${data.change_delta > 0 ? 'text-emerald-600' : data.change_delta < 0 ? 'text-error' : 'text-on-surface'}`}>
                    {data.change_delta != null ? `${data.change_delta > 0 ? '+' : ''}${data.change_delta}` : '—'}
                  </strong>
                </div>
              </div>

              <p className="text-xs text-outline italic pt-1 border-t border-outline-variant/40">
                ℹ {data.disclaimer || t('effectiveness.disclaimer')}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function SupportCasesPage() {
  const { t } = useTranslation()
  const { user, role } = useAuth()
  const { notify } = useNotification()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Main view toggle: 'cases' or 'requests'
  const [activeView, setActiveView] = useState('cases')
  const [supportRequests, setSupportRequests] = useState([])
  const [loadingRequests, setLoadingRequests] = useState(false)
  const [escalatingId, setEscalatingId] = useState(null)

  // Filters
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [priority, setPriority] = useState('')
  const [page, setPage] = useState(1)

  // Selected case drawer/detail modal
  const [selectedCase, setSelectedCase] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [newNote, setNewNote] = useState('')
  const [isSensitive, setIsSensitive] = useState(false)

  const fetchCases = useCallback(() => {
    setLoading(true)
    const params = new URLSearchParams({ page, page_size: 25 })
    if (status) params.set('status', status)
    if (category) params.set('category', category)
    if (priority) params.set('priority', priority)

    apiGet(`/api/cases?${params}`)
      .then(res => { setData(res); setError(null) })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [status, category, priority, page])

  const fetchSupportRequests = useCallback(() => {
    setLoadingRequests(true)
    apiGet('/api/support-requests')
      .then(res => setSupportRequests(res || []))
      .catch(err => console.error(err))
      .finally(() => setLoadingRequests(false))
  }, [])

  useEffect(() => {
    if (activeView === 'cases') {
      fetchCases()
    } else {
      fetchSupportRequests()
    }
  }, [activeView, fetchCases, fetchSupportRequests])

  const handleEscalateRequest = async (ssrId) => {
    setEscalatingId(ssrId)
    try {
      await apiPost(`/api/support-requests/${ssrId}/link-case`, {
        category: 'attendance',
        priority: 'High',
        reason: 'Escalated from staff-assisted student support request.',
      })
      fetchSupportRequests()
      notify.success('Support request successfully escalated to a formal Support Case.', 'Case Escalated')
    } catch (err) {
      notify.parseError(err, 'Failed to Escalate Request')
    } finally {
      setEscalatingId(null)
    }
  }

  useEffect(() => { fetchCases() }, [fetchCases])

  const openCaseDetail = async (id) => {
    setLoadingDetail(true)
    try {
      const detail = await apiGet(`/api/cases/${id}`)
      setSelectedCase(detail)
      setNewNote('')
      setIsSensitive(false)
    } catch (err) {
      notify.parseError(err, 'Failed to Load Case Details')
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleAddNote = async (e) => {
    e.preventDefault()
    if (!newNote.trim() || !selectedCase) return
    try {
      await apiPost(`/api/cases/${selectedCase.id}/notes`, {
        note_text: newNote.trim(),
        is_sensitive: isSensitive,
      })
      notify.success('Progress note saved to case timeline.', 'Note Added')
      // Refresh detail
      openCaseDetail(selectedCase.id)
    } catch (err) {
      notify.parseError(err, 'Failed to Add Note')
    }
  }

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <div>
          <span className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            {t('nav.support_cases')}
          </span>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Track student support plans, remedial actions, guardian meetings, and follow-ups.
          </p>
        </div>
        {/* View Switcher Tabs */}
        <div className="flex bg-surface-container-low p-1 rounded-xl">
          <button
            onClick={() => setActiveView('cases')}
            className={`px-4 py-1.5 rounded-lg font-label-md text-label-md transition-all ${activeView === 'cases' ? 'bg-surface-container-lowest text-on-surface shadow-sm font-semibold' : 'text-on-surface-variant hover:text-on-surface'}`}
          >
            Active Support Cases
          </button>
          <button
            onClick={() => setActiveView('requests')}
            className={`px-4 py-1.5 rounded-lg font-label-md text-label-md transition-all flex items-center gap-1.5 ${activeView === 'requests' ? 'bg-surface-container-lowest text-on-surface shadow-sm font-semibold' : 'text-on-surface-variant hover:text-on-surface'}`}
          >
            <span>Support Requests (SSR)</span>
            {supportRequests.length > 0 && (
              <span className="w-5 h-5 rounded-full bg-secondary text-on-secondary text-[11px] flex items-center justify-center font-bold">
                {supportRequests.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {activeView === 'requests' ? (
        /* Support Requests (SSR) Intake Table */
        <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
          <div className="px-4 py-3 bg-surface-container-low border-b border-outline-variant flex items-center justify-between">
            <span className="font-headline-sm text-headline-sm text-on-surface">
              Staff-Assisted Support Intake Queue
            </span>
            <span className="font-label-sm text-label-sm text-on-surface-variant">
              Provides anonymous tracking numbers for students and parents
            </span>
          </div>
          {loadingRequests ? (
            <div className="flex items-center justify-center py-16">
              <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
            </div>
          ) : supportRequests.length === 0 ? (
            <div className="py-10 text-center font-body-sm text-body-sm text-on-surface-variant">
              No pending student support requests.
            </div>
          ) : (
            <div className="overflow-x-auto w-full">
              <table className="w-full">
                <thead>
                  <tr className="bg-surface-container border-b border-outline-variant text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
                    <th className="px-4 py-3 text-left">Tracking Number</th>
                    <th className="px-4 py-3 text-left">Student</th>
                    <th className="px-4 py-3 text-left">Domain</th>
                    <th className="px-4 py-3 text-center">Urgency</th>
                    <th className="px-4 py-3 text-center">Status</th>
                    <th className="px-4 py-3 text-right">Escalation</th>
                  </tr>
                </thead>
                <tbody>
                  {supportRequests.map((req, idx) => (
                    <tr key={req.id} className={`${idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'} hover:bg-surface-container transition-colors`}>
                      <td className="px-4 py-2 font-mono text-[13px] font-semibold text-secondary">
                        {req.tracking_number}
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-2.5">
                          <StudentAvatar student={req.student} size={32} />
                          <div>
                            <Link to={`/students/${req.student?.id}`} className="font-label-md text-label-md text-secondary hover:underline">
                              {req.student?.full_name}
                            </Link>
                            <div className="font-body-sm text-body-sm text-on-surface-variant">
                              EMIS: {req.student?.emis_id}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-2 font-body-sm text-body-sm text-on-surface capitalize">
                        {req.support_domain.replace('_', ' ')}
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Badge variant={req.urgency_level === 'priority' ? 'high' : 'medium'}>
                          {req.urgency_level}
                        </Badge>
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Badge variant={req.status === 'Linked to Case' ? 'resolved' : 'under_review'}>
                          {req.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-2 text-right">
                        {req.status !== 'Linked to Case' && (
                          <button
                            onClick={() => handleEscalateRequest(req.id)}
                            disabled={escalatingId === req.id}
                            className="px-3 py-1 bg-secondary text-on-secondary rounded font-label-md text-label-md hover:bg-on-secondary-container transition-colors disabled:opacity-50"
                          >
                            {escalatingId === req.id ? 'Escalating...' : 'Escalate to Case'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <>
          {/* Filters */}
          <div className="flex flex-wrap gap-2 mb-4">
        <select
          value={status}
          onChange={e => { setStatus(e.target.value); setPage(1) }}
          className="h-9 px-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant focus:outline-none"
        >
          <option value="">All Statuses</option>
          <option value="Open">Open</option>
          <option value="In Progress">In Progress</option>
          <option value="Under Observation">Under Observation</option>
          <option value="Resolved">Resolved</option>
          <option value="Closed">Closed</option>
        </select>
        <select
          value={priority}
          onChange={e => { setPriority(e.target.value); setPage(1) }}
          className="h-9 px-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant focus:outline-none"
        >
          <option value="">All Priorities</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
        <select
          value={category}
          onChange={e => { setCategory(e.target.value); setPage(1) }}
          className="h-9 px-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant focus:outline-none"
        >
          <option value="">All Categories</option>
          <option value="attendance">Attendance Support</option>
          <option value="academic">Academic & Remedial</option>
          <option value="socio_welfare">Socio-Welfare</option>
          <option value="behavioral">Behavioral Support</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
          </div>
        ) : error ? (
          <div className="py-10 text-center font-body-sm text-body-sm text-error">{error}</div>
        ) : data?.items?.length === 0 ? (
          <div className="py-10 text-center font-body-sm text-body-sm text-on-surface-variant">
            {t('common.no_data')}
          </div>
        ) : (
          <div className="overflow-x-auto w-full">
            <table className="w-full">
              <thead>
                <tr className="bg-surface-container border-b border-outline-variant text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
                  <th className="px-4 py-3 text-left">Case #</th>
                  <th className="px-4 py-3 text-left">{t('common.student')}</th>
                  <th className="px-4 py-3 text-left">Category & Reason</th>
                  <th className="px-4 py-3 text-left">Assigned Staff</th>
                  <th className="px-4 py-3 text-center">{t('common.priority')}</th>
                  <th className="px-4 py-3 text-center">{t('common.status')}</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((c, idx) => (
                  <tr key={c.id} className={`${idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'} hover:bg-surface-container transition-colors`}>
                    <td className="px-4 py-2 font-label-md text-label-md font-semibold text-secondary">
                      {c.case_number}
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex items-center gap-2.5">
                        <StudentAvatar student={c.student} size={32} />
                        <div>
                          <Link to={`/students/${c.student?.id}`} className="font-label-md text-label-md text-secondary hover:underline">
                            {c.student?.full_name}
                          </Link>
                          <div className="font-body-sm text-body-sm text-on-surface-variant">
                            Grade {c.student?.grade}-{c.student?.section}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-2">
                      <span className="font-label-sm text-label-sm uppercase text-on-surface font-semibold">{c.category}</span>
                      <p className="font-body-sm text-body-sm text-on-surface-variant truncate max-w-xs">{c.reason}</p>
                    </td>
                    <td className="px-4 py-2 font-body-sm text-body-sm text-on-surface">
                      {c.assigned_staff?.full_name || '—'}
                    </td>
                    <td className="px-4 py-2 text-center">
                      <Badge variant={c.priority?.toLowerCase()}>{c.priority}</Badge>
                    </td>
                    <td className="px-4 py-2 text-center">
                      <Badge variant="in_progress">{c.status}</Badge>
                    </td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={() => openCaseDetail(c.id)}
                        className="px-3 py-1 bg-surface-container text-on-surface hover:bg-surface-container-high rounded font-label-md text-label-md transition-colors"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      </>
      )}

      {/* Detail Modal */}
      {selectedCase && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-2xl w-full p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-outline-variant pb-3 mb-4">
              <div>
                <span className="font-headline-sm text-headline-sm text-on-surface">{selectedCase.case_number}</span>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Student: <strong>{selectedCase.student?.full_name}</strong> (EMIS: {selectedCase.student?.emis_id})
                </p>
              </div>
              <button onClick={() => setSelectedCase(null)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            {/* Case Info */}
            <div className="grid grid-cols-2 gap-4 mb-4 font-body-sm text-body-sm">
              <div>Category: <strong className="text-on-surface">{selectedCase.category}</strong></div>
              <div>Priority: <Badge variant={selectedCase.priority?.toLowerCase()}>{selectedCase.priority}</Badge></div>
              <div>Status: <Badge variant="in_progress">{selectedCase.status}</Badge></div>
              <div>Assigned Staff: <strong className="text-on-surface">{selectedCase.assigned_staff?.full_name}</strong></div>
              <div className="col-span-2">Reason: <p className="text-on-surface mt-1">{selectedCase.reason}</p></div>
              {selectedCase.observations && (
                <div className="col-span-2">Observations: <p className="text-on-surface mt-1">{selectedCase.observations}</p></div>
              )}
            </div>

            {/* Interventions */}
            <div className="mb-4">
              <h3 className="font-headline-sm text-headline-sm text-on-surface mb-2">Interventions ({selectedCase.interventions.length})</h3>
              {selectedCase.interventions.length === 0 ? (
                <p className="font-body-sm text-body-sm text-on-surface-variant">No interventions planned yet.</p>
              ) : (
                <div className="space-y-2">
                  {selectedCase.interventions.map(i => (
                    <div key={i.id} className="p-3 bg-surface-container-low rounded">
                      <div className="flex items-center justify-between">
                        <span className="font-label-md text-label-md font-semibold text-on-surface">{i.title}</span>
                        <Badge variant="in_progress">{i.status}</Badge>
                      </div>
                      <p className="font-body-sm text-body-sm text-on-surface mt-1">{i.description}</p>
                      <span className="font-label-sm text-label-sm text-on-surface-variant mt-1 block">
                        Start: {i.start_date} {i.target_date ? `• Target: ${i.target_date}` : ''}
                      </span>
                      <InterventionEffectivenessCard caseId={selectedCase.id} interventionId={i.id} />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Case Notes */}
            <div className="mb-4">
              <h3 className="font-headline-sm text-headline-sm text-on-surface mb-2">Case Notes</h3>
              {selectedCase.case_notes.length === 0 ? (
                <p className="font-body-sm text-body-sm text-on-surface-variant">No notes logged yet.</p>
              ) : (
                <div className="space-y-2 mb-3">
                  {selectedCase.case_notes.map(n => (
                    <div key={n.id} className={`p-3 rounded ${n.is_sensitive ? 'bg-amber-50 border border-amber-200' : 'bg-surface-container-low'}`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-label-sm text-label-sm text-on-surface font-semibold">{n.author?.full_name}</span>
                        {n.is_sensitive && (
                          <span className="px-2 py-0.5 rounded bg-amber-200 text-amber-900 font-label-sm text-label-sm font-semibold">
                            CONFIDENTIAL
                          </span>
                        )}
                      </div>
                      <p className="font-body-sm text-body-sm text-on-surface">{n.note_text}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Add Note Form */}
              <form onSubmit={handleAddNote} className="space-y-2 pt-2 border-t border-outline-variant">
                <textarea
                  rows={2}
                  value={newNote}
                  onChange={e => setNewNote(e.target.value)}
                  placeholder="Add a case note or progress observation..."
                  className="w-full p-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                />
                {role?.role_name === 'counsellor' && (
                  <label className="flex items-center gap-2 font-label-sm text-label-sm text-on-surface">
                    <input
                      type="checkbox"
                      checked={isSensitive}
                      onChange={e => setIsSensitive(e.target.checked)}
                      className="rounded"
                    />
                    <span>Mark as sensitive / confidential (visible to assigned counsellor only)</span>
                  </label>
                )}
                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={!newNote.trim()}
                    className="px-4 py-1.5 bg-secondary text-on-secondary rounded font-label-md text-label-md hover:bg-on-secondary-container transition-colors disabled:opacity-60"
                  >
                    Add Note
                  </button>
                </div>
              </form>
            </div>

            {/* Case Event Timeline (Shared EventTimeline component) */}
            <div className="mt-6 pt-4 border-t border-outline-variant">
              <h3 className="font-headline-sm text-headline-sm text-on-surface mb-3 flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-secondary">timeline</span>
                <span>Case Event Timeline</span>
              </h3>
              <EventTimeline caseId={selectedCase.id} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

