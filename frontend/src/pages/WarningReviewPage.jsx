import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiGet, apiPost } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import Badge from '../components/Badge.jsx'

export default function WarningReviewPage() {
  const { t } = useTranslation()
  const { role } = useAuth()

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [category, setCategory] = useState('')
  const [priority, setPriority] = useState('')
  const [status, setStatus] = useState('Needs Review')
  const [page, setPage] = useState(1)

  // Selected indicator detail modal
  const [selectedInd, setSelectedInd] = useState(null)
  const [reviewNotes, setReviewNotes] = useState('')
  const [newStatus, setNewStatus] = useState('Under Review')
  const [submittingReview, setSubmittingReview] = useState(false)

  const fetchIndicators = useCallback(() => {
    setLoading(true)
    const params = new URLSearchParams({ page, page_size: 25 })
    if (category) params.set('category', category)
    if (priority) params.set('priority', priority)
    if (status) params.set('status', status)

    apiGet(`/api/indicators?${params}`)
      .then(res => { setData(res); setError(null) })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [category, priority, status, page])

  useEffect(() => { fetchIndicators() }, [fetchIndicators])

  const openIndicatorDetail = async (id) => {
    try {
      const detail = await apiGet(`/api/indicators/${id}`)
      setSelectedInd(detail)
      setReviewNotes('')
      setNewStatus(detail.status === 'Needs Review' ? 'Under Review' : 'Support Recommended')
    } catch (err) {
      alert('Error: ' + err.message)
    }
  }

  const handleRecordReview = async (e) => {
    e.preventDefault()
    if (!selectedInd) return
    setSubmittingReview(true)
    try {
      await apiPost(`/api/indicators/${selectedInd.id}/review`, {
        new_status: newStatus,
        review_notes: reviewNotes.trim(),
      })
      setSelectedInd(null)
      fetchIndicators()
    } catch (err) {
      alert('Error: ' + err.message)
    } finally {
      setSubmittingReview(false)
    }
  }

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <div>
          <span className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            {t('nav.early_warnings')}
          </span>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            {t('app.disclaimer')}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        <select
          value={status}
          onChange={e => { setStatus(e.target.value); setPage(1) }}
          className="h-9 px-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant focus:outline-none"
        >
          <option value="">All Statuses</option>
          <option value="Needs Review">Needs Review</option>
          <option value="Under Review">Under Review</option>
          <option value="Support Recommended">Support Recommended</option>
          <option value="Reviewed - No Action">Reviewed - No Action</option>
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
          <option value="attendance">Attendance</option>
          <option value="academic">Academic</option>
          <option value="assignment">Assignment</option>
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
          <table className="w-full">
            <thead>
              <tr className="bg-surface-container border-b border-outline-variant text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
                <th className="px-4 py-3 text-left">{t('common.student')}</th>
                <th className="px-4 py-3 text-left">Rule Code</th>
                <th className="px-4 py-3 text-left">Explanation & Evidence</th>
                <th className="px-4 py-3 text-center">{t('common.priority')}</th>
                <th className="px-4 py-3 text-center">{t('common.status')}</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((ind, idx) => (
                <tr key={ind.id} className={`${idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'} hover:bg-surface-container transition-colors`}>
                  <td className="px-4 py-2">
                    <Link to={`/students/${ind.student?.id}`} className="font-label-md text-label-md text-secondary hover:underline">
                      {ind.student?.full_name}
                    </Link>
                    <div className="font-body-sm text-body-sm text-on-surface-variant">
                      {ind.student?.grade}-{ind.student?.section} (EMIS: {ind.student?.emis_id})
                    </div>
                  </td>
                  <td className="px-4 py-2 font-label-md text-label-md text-on-surface font-semibold">
                    {ind.rule_code}
                  </td>
                  <td className="px-4 py-2 font-body-sm text-body-sm text-on-surface max-w-md">
                    {ind.plain_explanation}
                  </td>
                  <td className="px-4 py-2 text-center">
                    <Badge variant={ind.priority?.toLowerCase()}>{ind.priority}</Badge>
                  </td>
                  <td className="px-4 py-2 text-center">
                    <Badge variant="needs_review">{ind.status}</Badge>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => openIndicatorDetail(ind.id)}
                      className="px-3 py-1 bg-surface-container text-on-surface hover:bg-surface-container-high rounded font-label-md text-label-md transition-colors"
                    >
                      Review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Review Modal */}
      {selectedInd && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h2 className="font-headline-sm text-headline-sm text-on-surface mb-2">
              Review Indicator: {selectedInd.rule_code}
            </h2>
            <p className="font-body-sm text-body-sm text-on-surface-variant mb-4">
              Student: <strong>{selectedInd.student?.full_name}</strong> (EMIS: {selectedInd.student?.emis_id})
            </p>

            <div className="p-3 bg-surface-container-low rounded mb-4">
              <span className="font-label-sm text-label-sm uppercase text-outline block mb-1">Plain Explanation</span>
              <p className="font-body-sm text-body-sm text-on-surface">{selectedInd.plain_explanation}</p>
            </div>

            <form onSubmit={handleRecordReview} className="space-y-4">
              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">Decision / New Status</label>
                <select
                  value={newStatus}
                  onChange={e => setNewStatus(e.target.value)}
                  className="w-full h-9 px-3 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                >
                  <option value="Under Review">Under Review</option>
                  <option value="Support Recommended">Support Recommended</option>
                  <option value="Reviewed - No Action">Reviewed - No Action</option>
                  <option value="Closed">Closed</option>
                </select>
              </div>

              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">Human Review Notes (Required)</label>
                <textarea
                  required
                  rows={3}
                  value={reviewNotes}
                  onChange={e => setReviewNotes(e.target.value)}
                  placeholder="Record your discussion, context, or decision reason..."
                  className="w-full p-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedInd(null)}
                  className="px-4 py-2 bg-surface-container text-on-surface font-label-md text-label-md rounded hover:bg-surface-container-high transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReview || !reviewNotes.trim()}
                  className="px-4 py-2 bg-secondary text-on-secondary font-label-md text-label-md rounded hover:bg-on-secondary-container transition-colors disabled:opacity-60"
                >
                  {submittingReview ? 'Saving...' : 'Record Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

