import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiGet, apiPost } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useNotification } from '../context/NotificationContext.jsx'
import Badge from '../components/Badge.jsx'
import DemoDataBanner from '../components/DemoDataBanner.jsx'
import StudentAvatar from '../components/StudentAvatar.jsx'

export default function WarningReviewPage() {
  const { t } = useTranslation()
  const { user, role } = useAuth()
  const { notify, confirm } = useNotification()

  // Main Tabs: 'indicators' | 'corrections' | 'patterns'
  const [activeTab, setActiveTab] = useState('indicators')

  // Indicators State
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [category, setCategory] = useState('')
  const [priority, setPriority] = useState('')
  const [status, setStatus] = useState('Needs Review')
  const [dataOrigin, setDataOrigin] = useState('')
  const [page, setPage] = useState(1)

  // Selected indicator detail & review modal
  const [selectedInd, setSelectedInd] = useState(null)
  const [reviewNotes, setReviewNotes] = useState('')
  const [newStatus, setNewStatus] = useState('Under Review')
  const [submittingReview, setSubmittingReview] = useState(false)

  // Evidence Records Modal State (Feature 1)
  const [evidenceData, setEvidenceData] = useState(null)
  const [loadingEvidence, setLoadingEvidence] = useState(false)
  const [showEvidenceModal, setShowEvidenceModal] = useState(false)

  // Create Case from Indicator Modal (Feature 1)
  const [showCaseModal, setShowCaseModal] = useState(false)
  const [caseTargetInd, setCaseTargetInd] = useState(null)
  const [caseReason, setCaseReason] = useState('')
  const [submittingCase, setSubmittingCase] = useState(false)
  const [caseConflictMsg, setCaseConflictMsg] = useState(null)

  // Correction Centre State (Feature 2)
  const [correctionsList, setCorrectionsList] = useState([])
  const [loadingCorrections, setLoadingCorrections] = useState(false)
  const [correctionFilter, setCorrectionFilter] = useState('pending')
  const [decidingId, setDecidingId] = useState(null)
  const [adminNotes, setAdminNotes] = useState('')
  const [activeDecideTarget, setActiveDecideTarget] = useState(null)

  // Propose Correction Modal
  const [showProposeModal, setShowProposeModal] = useState(false)
  const [propRecordType, setPropRecordType] = useState('attendance')
  const [propRecordId, setPropRecordId] = useState('')
  const [propField, setPropField] = useState('days_present')
  const [propValue, setPropValue] = useState('')
  const [propReason, setPropReason] = useState('')
  const [submittingProposal, setSubmittingProposal] = useState(false)

  // Multi-Indicator Pattern Analysis (Feature 6)
  const [patternsData, setPatternsData] = useState(null)
  const [loadingPatterns, setLoadingPatterns] = useState(false)

  const fetchIndicators = useCallback(() => {
    setLoading(true)
    const params = new URLSearchParams({ page, page_size: 25 })
    if (category) params.set('category', category)
    if (priority) params.set('priority', priority)
    if (status) params.set('status', status)
    if (dataOrigin) params.set('data_origin', dataOrigin)

    apiGet(`/api/indicators?${params}`)
      .then(res => { setData(res); setError(null) })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [category, priority, status, dataOrigin, page])

  const fetchCorrections = useCallback(() => {
    setLoadingCorrections(true)
    const params = new URLSearchParams()
    if (correctionFilter) params.set('status', correctionFilter)
    apiGet(`/api/corrections?${params}`)
      .then(res => setCorrectionsList(res.items || []))
      .catch(err => console.error(err))
      .finally(() => setLoadingCorrections(false))
  }, [correctionFilter])

  const fetchPatterns = useCallback(() => {
    setLoadingPatterns(true)
    apiGet('/api/indicators/patterns')
      .then(res => setPatternsData(res))
      .catch(err => console.error(err))
      .finally(() => setLoadingPatterns(false))
  }, [])

  useEffect(() => {
    if (activeTab === 'indicators') {
      fetchIndicators()
    } else if (activeTab === 'corrections') {
      fetchCorrections()
    } else if (activeTab === 'patterns') {
      fetchPatterns()
    }
  }, [activeTab, fetchIndicators, fetchCorrections, fetchPatterns])

  const openIndicatorDetail = async (id) => {
    try {
      const detail = await apiGet(`/api/indicators/${id}`)
      setSelectedInd(detail)
      setReviewNotes('')
      setNewStatus(detail.status === 'Needs Review' ? 'Under Review' : 'Support Recommended')
    } catch (err) {
      notify.parseError(err, 'Failed to Load Indicator Detail')
    }
  }

  const handleInspectEvidence = async (indId) => {
    setLoadingEvidence(true)
    setShowEvidenceModal(true)
    try {
      const res = await apiGet(`/api/indicators/${indId}/evidence-records`)
      setEvidenceData(res)
    } catch (err) {
      notify.parseError(err, 'Failed to Load Evidence Records')
      setShowEvidenceModal(false)
    } finally {
      setLoadingEvidence(false)
    }
  }

  const handleOpenCaseModal = (ind) => {
    setCaseTargetInd(ind)
    setCaseReason(`Support initiated following review of indicator ${ind.rule_code}: ${ind.plain_explanation}`)
    setCaseConflictMsg(null)
    setShowCaseModal(true)
  }

  const handleCreateCaseFromIndicator = async (e) => {
    e.preventDefault()
    if (!caseTargetInd) return
    setSubmittingCase(true)
    setCaseConflictMsg(null)
    try {
      await apiPost('/api/cases', {
        student_id: caseTargetInd.student_id,
        indicator_id: caseTargetInd.id,
        assigned_staff_id: user?.id,
        category: caseTargetInd.category || 'attendance',
        priority: caseTargetInd.priority || 'High',
        reason: caseReason.trim(),
      })
      notify.success('Support Case created successfully and linked to indicator.', 'Case Created')
      setShowCaseModal(false)
      if (selectedInd?.id === caseTargetInd.id) setSelectedInd(null)
      fetchIndicators()
    } catch (err) {
      setCaseConflictMsg(err.message)
      notify.parseError(err, 'Failed to Create Case')
    } finally {
      setSubmittingCase(false)
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
      notify.success(`Indicator status updated to "${newStatus}".`, 'Review Saved')
      setSelectedInd(null)
      fetchIndicators()
    } catch (err) {
      notify.parseError(err, 'Failed to Save Review')
    } finally {
      setSubmittingReview(false)
    }
  }

  const handleDecideCorrection = async (decision) => {
    if (!activeDecideTarget) return
    setDecidingId(activeDecideTarget.id)
    try {
      await apiPost(`/api/corrections/${activeDecideTarget.id}/decide`, {
        decision,
        review_notes: adminNotes.trim() || undefined,
      })
      notify.success(`Correction proposal successfully ${decision}d.`, 'Decision Recorded')
      setActiveDecideTarget(null)
      setAdminNotes('')
      fetchCorrections()
      if (activeTab === 'indicators') fetchIndicators()
    } catch (err) {
      notify.parseError(err, 'Decision Error')
    } finally {
      setDecidingId(null)
    }
  }

  const handleSubmitProposal = async (e) => {
    e.preventDefault()
    if (!propRecordId || !propValue || !propReason.trim()) {
      notify.warning('Please fill in all required fields.', 'Incomplete Form')
      return
    }
    setSubmittingProposal(true)
    try {
      let val = propValue
      if (propField === 'score' || propField === 'days_present') {
        const num = parseFloat(propValue)
        if (!isNaN(num)) val = num
      }

      await apiPost('/api/corrections', {
        record_type: propRecordType,
        record_id: parseInt(propRecordId, 10),
        proposed_changes: { [propField]: val },
        reason: propReason.trim(),
      })
      notify.success('Correction proposed successfully. Awaiting administrator review.', 'Proposal Submitted')
      setShowProposeModal(false)
      fetchCorrections()
    } catch (err) {
      notify.parseError(err, 'Failed to Submit Proposal')
    } finally {
      setSubmittingProposal(false)
    }
  }

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <div>
          <span className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            {activeTab === 'indicators'
              ? t('nav.early_warnings')
              : activeTab === 'corrections'
              ? t('corrections.title')
              : 'Multi-Indicator Pattern Analysis'}
          </span>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            {activeTab === 'indicators'
              ? t('app.disclaimer')
              : activeTab === 'corrections'
              ? t('corrections.subtitle')
              : 'Co-occurring indicators across domains prompting coordinated multidisciplinary review. No artificial risk scores or automated rankings.'}
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex items-center bg-surface-container-low p-1 rounded-lg border border-outline-variant">
          <button
            onClick={() => setActiveTab('indicators')}
            className={`px-4 py-1.5 rounded-md font-label-md text-label-md transition-all flex items-center gap-1.5 ${activeTab === 'indicators'
                ? 'bg-surface-container-lowest text-secondary shadow-sm font-semibold'
                : 'text-on-surface-variant hover:text-on-surface'
              }`}
          >
            <span className="material-symbols-outlined text-[18px]">flag</span>
            <span>Early Warning Indicators</span>
          </button>
          <button
            onClick={() => setActiveTab('patterns')}
            className={`px-4 py-1.5 rounded-md font-label-md text-label-md transition-all flex items-center gap-1.5 ${
              activeTab === 'patterns'
                ? 'bg-surface-container-lowest text-secondary shadow-sm font-semibold'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">hub</span>
            <span>Multi-Indicator Patterns</span>
          </button>
          <button
            onClick={() => setActiveTab('corrections')}
            className={`px-4 py-1.5 rounded-md font-label-md text-label-md transition-all flex items-center gap-1.5 ${activeTab === 'corrections'
                ? 'bg-surface-container-lowest text-secondary shadow-sm font-semibold'
                : 'text-on-surface-variant hover:text-on-surface'
              }`}
          >
            <span className="material-symbols-outlined text-[18px]">published_with_changes</span>
            <span>{t('corrections.title')}</span>
          </button>
        </div>
      </div>

      {/* TAB 1: WARNING INDICATORS (FEATURE 1) */}
      {activeTab === 'indicators' && (
        <>
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
          </div>

          {/* Demo data banner */}
          {(dataOrigin === 'mock' || data?.items?.some(i => i.data_origin === 'mock')) && (
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
              <div className="py-10 text-center font-body-sm text-body-sm text-on-surface-variant">
                {t('common.no_data')}
              </div>
            ) : (
              <div className="overflow-x-auto w-full">
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
                        <div className="flex items-center gap-2.5">
                          <StudentAvatar student={ind.student} size={32} />
                          <div>
                            <Link to={`/students/${ind.student?.id}`} className="font-label-md text-label-md text-secondary hover:underline">
                              {ind.student?.full_name}
                            </Link>
                            <div className="font-body-sm text-body-sm text-on-surface-variant">
                              {ind.student?.grade}-{ind.student?.section} (EMIS: {ind.student?.emis_id})
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-2 font-label-md text-label-md text-on-surface font-semibold">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span>{ind.rule_code}</span>
                          {ind.rule_version && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface-container font-mono text-outline">
                              v{ind.rule_version}
                            </span>
                          )}
                          {ind.data_origin === 'mock' && (
                            <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-700/50">
                              DEMO
                            </span>
                          )}
                          {ind.data_origin === 'dataset' && (
                            <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-700/50">
                              DATASET
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-2 font-body-sm text-body-sm text-on-surface max-w-md">
                        {ind.plain_explanation}
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Badge variant={ind.priority?.toLowerCase()}>{ind.priority}</Badge>
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Badge variant={ind.status === 'Needs Review' ? 'needs_review' : 'in_progress'}>{ind.status}</Badge>
                      </td>
                      <td className="px-4 py-2 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleInspectEvidence(ind.id)}
                            title="Inspect Underlying Records"
                            className="px-2.5 py-1 bg-surface-container-low hover:bg-surface-container text-on-surface-variant hover:text-on-surface rounded font-label-sm text-label-sm transition-colors flex items-center gap-1"
                          >
                            <span className="material-symbols-outlined text-[15px]">database</span>
                            <span>Evidence</span>
                          </button>
                          <button
                            onClick={() => openIndicatorDetail(ind.id)}
                            className="px-3 py-1 bg-surface-container text-on-surface hover:bg-surface-container-high rounded font-label-md text-label-md transition-colors"
                          >
                            Review
                          </button>
                        </div>
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

      {/* TAB 3: MULTI-INDICATOR PATTERNS (FEATURE 6) */}
      {activeTab === 'patterns' && (
        <>
          {/* Civic Mandate Banner */}
          <div className="mb-4 px-4 py-3 bg-surface-container-low rounded-xl border-l-4 border-secondary flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary text-[20px]">verified_user</span>
              <strong className="text-on-surface font-label-md text-label-md">Non-Predictive Decision Support Mandate</strong>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              THULIR strictly forbids composite risk scores, dropout probability percentages, and automated student rankings. Patterns represent explainable, co-occurring concrete indicators across domains (such as concurrent attendance dips and assessment challenges) to prompt coordinated staff action.
            </p>
          </div>

          {loadingPatterns ? (
            <div className="flex items-center justify-center py-16">
              <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
            </div>
          ) : !patternsData || patternsData.patterns?.length === 0 ? (
            <div className="py-12 text-center text-on-surface-variant bg-surface-container-lowest rounded-xl">
              No multi-indicator patterns detected across current records.
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between px-1">
                <span className="font-label-md text-label-md text-on-surface font-semibold">
                  Active Cross-Domain Patterns ({patternsData.total_active_patterns} total instances across {patternsData.reporting_period})
                </span>
              </div>

              {patternsData.patterns.map(pattern => (
                <div key={pattern.pattern_key} className="bg-surface-container-lowest rounded-xl p-5 shadow-sm border border-outline-variant">
                  <div className="flex flex-col md:flex-row md:items-start justify-between gap-3 mb-3 pb-3 border-b border-outline-variant">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-headline-sm text-headline-sm text-on-surface">{pattern.pattern_name}</span>
                        <span className="px-2 py-0.5 rounded-full text-label-sm font-semibold bg-surface-container text-secondary">
                          {pattern.affected_students_count} Students
                        </span>
                      </div>
                      <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                        {pattern.description}
                      </p>
                    </div>
                    <div className="shrink-0 flex items-center gap-2">
                      <span className="font-label-sm text-label-sm text-outline">Target Support Domain:</span>
                      <span className="px-2.5 py-1 rounded bg-secondary/10 text-secondary font-label-sm font-semibold capitalize">
                        {pattern.recommended_intervention_domain.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>

                  <div className="mb-4 p-3 bg-surface-container-low rounded-lg font-body-sm text-body-sm text-on-surface">
                    <strong className="text-secondary">Contextual Support Explanation: </strong>
                    {pattern.plain_explanation}
                  </div>

                  {pattern.matches.length === 0 ? (
                    <div className="py-4 text-center text-on-surface-variant font-body-sm text-body-sm bg-surface-container-low/50 rounded-lg">
                      No students currently exhibit this co-occurring pattern.
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left font-body-sm text-body-sm">
                        <thead>
                          <tr className="border-b border-outline-variant text-on-surface-variant font-label-sm">
                            <th className="py-2 px-3">Student</th>
                            <th className="py-2 px-3">Class</th>
                            <th className="py-2 px-3">Period</th>
                            <th className="py-2 px-3">Triggering Concurrent Indicators</th>
                            <th className="py-2 px-3 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-outline-variant/60">
                          {pattern.matches.map((match, mIdx) => (
                            <tr key={mIdx} className="hover:bg-surface-container-low/40 transition-colors">
                              <td className="py-3 px-3">
                                <div className="flex items-center gap-2.5">
                                  <StudentAvatar student={match.student} size={32} />
                                  <div>
                                    <div className="font-semibold text-on-surface">{match.student.full_name}</div>
                                    <div className="font-numeric-table text-label-sm text-outline">EMIS: {match.student.emis_id}</div>
                                  </div>
                                </div>
                              </td>
                              <td className="py-3 px-3">
                                <span className="px-2 py-0.5 rounded bg-surface-container font-label-sm">
                                  {match.student.class_section ? `Grade ${match.student.class_section.grade}-${match.student.class_section.section}` : '—'}
                                </span>
                              </td>
                              <td className="py-3 px-3 font-label-sm text-on-surface-variant">
                                {match.reporting_period}
                              </td>
                              <td className="py-3 px-3">
                                <div className="flex flex-wrap gap-1.5">
                                  {match.indicators.map((ind, iIdx) => (
                                    <span key={iIdx} className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container text-label-sm border border-outline-variant" title={ind.explanation}>
                                      <strong className="text-on-surface">{ind.rule_code}</strong>
                                      <span className={`text-[10px] px-1 rounded ${ind.priority === 'High' ? 'bg-error text-on-error' : 'bg-secondary text-on-secondary'}`}>
                                        {ind.priority}
                                      </span>
                                    </span>
                                  ))}
                                </div>
                              </td>
                              <td className="py-3 px-3 text-right">
                                <Link
                                  to={`/students/${match.student.id}`}
                                  className="inline-flex items-center gap-1 px-3 py-1 bg-surface-container hover:bg-surface-tint hover:text-on-primary text-secondary rounded font-label-sm font-semibold transition-colors"
                                >
                                  <span>View Profile</span>
                                  <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                                </Link>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* TAB 2: CORRECTION CENTRE (FEATURE 2) */}
      {activeTab === 'corrections' && (
        <>
          {/* Civic Trust Banner */}
          <div className="mb-4 px-4 py-3 bg-surface-container-low rounded-xl border-l-4 border-secondary flex flex-col md:flex-row md:items-center justify-between gap-3">
            <p className="font-body-sm text-body-sm text-on-surface-variant max-w-3xl">
              <strong className="text-on-surface">ℹ Immutable Verification Guardrail:</strong>{' '}
              {t('corrections.superseded_notice')} Teachers can propose corrections for assigned classes; administrators verify and apply.
            </p>
            <button
              onClick={() => setShowProposeModal(true)}
              className="px-4 py-2 bg-secondary text-on-secondary rounded font-label-md text-label-md hover:bg-on-secondary-container transition-colors flex items-center gap-1.5 self-start md:self-auto shrink-0"
            >
              <span className="material-symbols-outlined text-[18px]">add_circle</span>
              <span>{t('corrections.propose')}</span>
            </button>
          </div>

          {/* Filter Bar */}
          <div className="flex items-center gap-2 mb-4">
            {['pending', 'approved', 'rejected', ''].map(statusKey => (
              <button
                key={statusKey}
                onClick={() => setCorrectionFilter(statusKey)}
                className={`px-3 py-1 rounded font-label-sm text-label-sm capitalize transition-colors ${correctionFilter === statusKey
                    ? 'bg-secondary text-on-secondary font-semibold'
                    : 'bg-surface-container-lowest text-on-surface hover:bg-surface-container'
                  }`}
              >
                {statusKey === '' ? 'All Proposals' : statusKey}
              </button>
            ))}
          </div>

          {/* Table */}
          <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
            {loadingCorrections ? (
              <div className="flex items-center justify-center py-16">
                <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
              </div>
            ) : correctionsList.length === 0 ? (
              <div className="py-12 text-center font-body-sm text-body-sm text-on-surface-variant">
                No correction proposals match this filter.
              </div>
            ) : (
              <div className="overflow-x-auto w-full">
                <table className="w-full">
                <thead>
                  <tr className="bg-surface-container border-b border-outline-variant text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
                    <th className="px-4 py-3 text-left">Record Domain</th>
                    <th className="px-4 py-3 text-left">Side-by-Side Values</th>
                    <th className="px-4 py-3 text-left">Justification Reason</th>
                    <th className="px-4 py-3 text-left">Proposed By</th>
                    <th className="px-4 py-3 text-center">Status</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {correctionsList.map((corr, idx) => (
                    <tr key={corr.id} className={`${idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'} hover:bg-surface-container transition-colors`}>
                      <td className="px-4 py-3 font-label-md text-label-md text-on-surface capitalize">
                        <span className="font-semibold block">{corr.record_type}</span>
                        <span className="font-body-sm text-body-sm text-on-surface-variant">ID #{corr.record_id}</span>
                      </td>
                      <td className="px-4 py-3 font-body-sm text-body-sm">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-error/10 text-error font-mono text-xs">
                            Orig: {JSON.stringify(corr.original_data || {})}
                          </span>
                          <span className="material-symbols-outlined text-[16px] text-outline">arrow_forward</span>
                          <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-mono text-xs font-semibold">
                            Prop: {JSON.stringify(corr.proposed_changes || {})}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 font-body-sm text-body-sm text-on-surface max-w-sm">
                        {corr.reason}
                        {corr.admin_notes && (
                          <div className="mt-1 text-xs text-outline italic">
                            Admin note: {corr.admin_notes}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 font-body-sm text-body-sm text-on-surface">
                        <span className="font-semibold block">{corr.proposed_by?.full_name}</span>
                        <span className="text-on-surface-variant text-xs">
                          {new Date(corr.proposed_at).toLocaleDateString()}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Badge variant={corr.status === 'approved' ? 'stable' : corr.status === 'rejected' ? 'critical' : 'moderate'}>
                          {corr.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right">
                        {corr.status === 'pending' && role?.role_name === 'admin' ? (
                          <button
                            onClick={() => { setActiveDecideTarget(corr); setAdminNotes('') }}
                            className="px-3 py-1 bg-secondary text-on-secondary rounded font-label-md text-label-md hover:bg-on-secondary-container transition-colors"
                          >
                            Review & Decide
                          </button>
                        ) : (
                          <span className="font-label-sm text-label-sm text-outline">
                            {corr.status === 'approved' ? `Applied by ${corr.reviewed_by?.full_name || 'Admin'}` : 'Archived'}
                          </span>
                        )}
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

      {/* EVIDENCE RECORDS MODAL (FEATURE 1) */}
      {showEvidenceModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-2xl w-full p-6 shadow-xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-outline-variant pb-3 mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-[24px]">database</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">Underlying Evidence Records</span>
              </div>
              <button onClick={() => setShowEvidenceModal(false)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            {loadingEvidence || !evidenceData ? (
              <div className="flex flex-col items-center justify-center py-12 gap-2">
                <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
                <span className="text-body-sm text-on-surface-variant">Loading concrete evidence records...</span>
              </div>
            ) : (
              <div className="space-y-4 font-body-sm text-body-sm">
                {/* Rule & Threshold Header Card */}
                <div className="p-3.5 bg-surface-container-low rounded-xl border border-outline-variant/30 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-secondary/15 text-secondary font-mono text-xs font-bold">
                        {evidenceData.rule_code}
                      </span>
                      <span className="text-xs text-on-surface-variant font-medium">v{evidenceData.rule_version || 1}</span>
                      <span className="px-2 py-0.5 rounded bg-surface-container text-xs font-semibold text-on-surface uppercase">
                        {evidenceData.priority} Priority
                      </span>
                    </div>
                    <span className="text-xs text-on-surface-variant font-medium">
                      Period: <strong className="text-on-surface">{evidenceData.reporting_period || 'Current Term'}</strong>
                    </span>
                  </div>
                  {evidenceData.plain_explanation && (
                    <p className="text-xs text-on-surface font-medium leading-relaxed bg-surface-container-lowest p-2.5 rounded-lg border border-outline-variant/20">
                      {evidenceData.plain_explanation}
                    </p>
                  )}
                </div>

                {/* Concrete Records List */}
                <div>
                  {(() => {
                    const recordsList = evidenceData.evidence_records || evidenceData.records || []
                    return (
                      <>
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-label-md text-label-md font-semibold text-on-surface">
                            Audited Source Records ({recordsList.length})
                          </h4>
                          <span className="text-[11px] text-on-surface-variant">Deterministic verification basis</span>
                        </div>

                        {recordsList.length === 0 ? (
                          <div className="p-6 text-center bg-surface-container-low rounded-xl border border-outline-variant/20">
                            <span className="material-symbols-outlined text-outline text-[28px] block mb-1">inventory_2</span>
                            <p className="text-on-surface-variant text-xs">No concrete records logged for this indicator.</p>
                          </div>
                        ) : (
                          <div className="space-y-2 max-h-[45vh] overflow-y-auto pr-1">
                            {recordsList.map((rec, i) => (
                              <div
                                key={rec.id || i}
                                className="p-3 bg-surface-container-lowest rounded-xl border border-outline-variant/30 hover:border-outline-variant/60 shadow-xs transition-colors flex flex-col gap-1.5"
                              >
                                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                                  <div className="flex items-center gap-2">
                                    <span className="font-mono text-[11px] font-semibold text-secondary">
                                      #{rec.id}
                                    </span>
                                    <span className="font-medium text-on-surface">
                                      {rec.subject || rec.record_type?.toUpperCase() || 'Record'}
                                    </span>
                                    {rec.assessment_name && (
                                      <span className="text-on-surface-variant text-[11px]">
                                        • {rec.assessment_name}
                                      </span>
                                    )}
                                  </div>
                                  <span className="text-[11px] text-on-surface-variant font-mono">
                                    {rec.date} {rec.period ? `(${rec.period})` : ''}
                                  </span>
                                </div>

                                <div className="flex items-center justify-between text-xs pt-1 border-t border-outline-variant/20">
                                  <span className="font-semibold text-on-surface text-[13px]">
                                    {rec.metric || `${rec.percentage ?? rec.score ?? '-'}%`}
                                  </span>
                                  <div className="flex items-center gap-1.5">
                                    {rec.has_pending_correction && (
                                      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/15 text-amber-800 border border-amber-300">
                                        Correction Pending
                                      </span>
                                    )}
                                    {rec.is_superseded && (
                                      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-surface-container text-outline">
                                        Superseded
                                      </span>
                                    )}
                                    <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-surface-container text-on-surface-variant">
                                      Verified
                                    </span>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </>
                    )
                  })()}
                </div>

                <div className="flex justify-end pt-2 border-t border-outline-variant/30">
                  <button
                    onClick={() => setShowEvidenceModal(false)}
                    className="px-4 py-1.5 bg-secondary text-on-secondary font-label-md text-label-md rounded-lg hover:bg-on-secondary-container transition-colors shadow-xs"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* REVIEW MODAL (FEATURE 1) */}
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

              <div className="flex items-center justify-between pt-2">
                {selectedInd.status === 'Support Recommended' || newStatus === 'Support Recommended' ? (
                  <button
                    type="button"
                    onClick={() => handleOpenCaseModal(selectedInd)}
                    className="px-3 py-1.5 bg-primary-container text-on-primary-container font-label-md text-label-md rounded hover:opacity-90 flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-[16px]">support_agent</span>
                    <span>Open Support Case</span>
                  </button>
                ) : <div />}

                <div className="flex gap-2">
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
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CREATE CASE MODAL WITH DUPLICATE PREVENTION (FEATURE 1) */}
      {showCaseModal && caseTargetInd && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-lg w-full p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-outline-variant pb-3 mb-4">
              <span className="font-headline-sm text-headline-sm text-on-surface">Connect Indicator to Support Case</span>
              <button onClick={() => setShowCaseModal(false)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            {caseConflictMsg && (
              <div className="mb-4 p-3 rounded bg-error/10 border border-error text-error font-body-sm text-body-sm flex items-center gap-2">
                <span className="material-symbols-outlined text-[18px]">block</span>
                <span>{caseConflictMsg}</span>
              </div>
            )}

            <form onSubmit={handleCreateCaseFromIndicator} className="space-y-3 font-body-sm text-body-sm">
              <div className="p-3 bg-surface-container-low rounded">
                <div>Student: <strong>{caseTargetInd.student?.full_name}</strong></div>
                <div>Trigger Indicator: <strong>{caseTargetInd.rule_code}</strong></div>
              </div>

              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">Case Justification</label>
                <textarea
                  required
                  rows={3}
                  value={caseReason}
                  onChange={e => setCaseReason(e.target.value)}
                  className="w-full p-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCaseModal(false)}
                  className="px-3 py-1.5 bg-surface-container text-on-surface font-label-md text-label-md rounded hover:bg-surface-container-high transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCase}
                  className="px-4 py-1.5 bg-secondary text-on-secondary font-label-md text-label-md rounded hover:bg-on-secondary-container transition-colors disabled:opacity-60"
                >
                  {submittingCase ? 'Creating Case...' : 'Create Support Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADMIN CORRECTION DECISION MODAL (FEATURE 2) */}
      {activeDecideTarget && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h3 className="font-headline-sm text-headline-sm text-on-surface mb-2">Review Correction Proposal</h3>
            <div className="p-3 bg-surface-container-low rounded mb-3 font-body-sm text-body-sm space-y-1">
              <div>Domain: <strong className="capitalize">{activeDecideTarget.record_type} #{activeDecideTarget.record_id}</strong></div>
              <div>Proposed By: <strong>{activeDecideTarget.proposed_by?.full_name}</strong></div>
              <div>Reason: <em>{activeDecideTarget.reason}</em></div>
              <div className="pt-1 font-mono text-xs">
                Proposed Change: {JSON.stringify(activeDecideTarget.proposed_changes)}
              </div>
            </div>

            <div className="mb-4">
              <label className="block font-label-md text-label-md text-on-surface mb-1">Admin Audit Notes (Optional)</label>
              <textarea
                rows={2}
                value={adminNotes}
                onChange={e => setAdminNotes(e.target.value)}
                placeholder="Optional administrative review note..."
                className="w-full p-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
              />
            </div>

            <div className="flex justify-between items-center pt-2">
              <button
                type="button"
                onClick={() => setActiveDecideTarget(null)}
                className="px-3 py-1.5 bg-surface-container text-on-surface rounded font-label-md text-label-md hover:bg-surface-container-high transition-colors"
              >
                Cancel
              </button>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleDecideCorrection('reject')}
                  disabled={decidingId === activeDecideTarget.id}
                  className="px-3 py-1.5 bg-error text-on-error rounded font-label-md text-label-md hover:opacity-90 transition-colors disabled:opacity-60"
                >
                  Reject Proposal
                </button>
                <button
                  type="button"
                  onClick={() => handleDecideCorrection('approve')}
                  disabled={decidingId === activeDecideTarget.id}
                  className="px-4 py-1.5 bg-emerald-600 text-white rounded font-label-md text-label-md hover:bg-emerald-700 transition-colors disabled:opacity-60"
                >
                  Approve & Recalculate
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* PROPOSE CORRECTION MODAL (FEATURE 2) */}
      {showProposeModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-lg w-full p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-outline-variant pb-3 mb-4">
              <span className="font-headline-sm text-headline-sm text-on-surface">{t('corrections.propose')}</span>
              <button onClick={() => setShowProposeModal(false)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <p className="font-body-sm text-body-sm text-on-surface-variant mb-4 bg-surface-container-low p-2.5 rounded">
              {t('corrections.superseded_notice')}
            </p>

            <form onSubmit={handleSubmitProposal} className="space-y-3 font-body-sm text-body-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-1">Record Domain</label>
                  <select
                    value={propRecordType}
                    onChange={e => setPropRecordType(e.target.value)}
                    className="w-full h-9 px-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                  >
                    <option value="attendance">Attendance Register</option>
                    <option value="assessment">Assessment Score</option>
                    <option value="assignment">Assignment Record</option>
                  </select>
                </div>

                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-1">Record ID</label>
                  <input
                    type="number"
                    required
                    value={propRecordId}
                    onChange={e => setPropRecordId(e.target.value)}
                    placeholder="e.g. 142"
                    className="w-full h-9 px-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-1">Field to Amend</label>
                  <input
                    type="text"
                    required
                    value={propField}
                    onChange={e => setPropField(e.target.value)}
                    placeholder="e.g. days_present or score"
                    className="w-full h-9 px-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                  />
                </div>

                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-1">Corrected Value</label>
                  <input
                    type="text"
                    required
                    value={propValue}
                    onChange={e => setPropValue(e.target.value)}
                    placeholder="e.g. 68 or 45.5"
                    className="w-full h-9 px-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">
                  Justification Reason (Mandatory Audit Trail)
                </label>
                <textarea
                  required
                  rows={3}
                  value={propReason}
                  onChange={e => setPropReason(e.target.value)}
                  placeholder="Explain why this record is being amended (e.g. verified with physical attendance register)..."
                  className="w-full p-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowProposeModal(false)}
                  className="px-3 py-1.5 bg-surface-container text-on-surface font-label-md text-label-md rounded hover:bg-surface-container-high transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingProposal}
                  className="px-4 py-1.5 bg-secondary text-on-secondary font-label-md text-label-md rounded hover:bg-on-secondary-container transition-colors disabled:opacity-60"
                >
                  {submittingProposal ? 'Submitting...' : 'Submit Proposal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

