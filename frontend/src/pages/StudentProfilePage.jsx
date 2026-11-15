import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiGet, apiPost } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useNotification } from '../context/NotificationContext.jsx'
import Badge from '../components/Badge.jsx'
import EventTimeline from '../components/EventTimeline.jsx'
import StudentAvatar from '../components/StudentAvatar.jsx'

export default function StudentProfilePage() {
  const { studentId } = useParams()
  const { t } = useTranslation()
  const { user, role } = useAuth()
  const { notify } = useNotification()

  const [student, setStudent] = useState(null)
  const [indicators, setIndicators] = useState([])
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Active tab state: 'overview' | 'attendance' | 'academic' | 'cases' | 'timeline' | 'trends'
  const [activeTab, setActiveTab] = useState('overview')

  // Longitudinal Trends State (Feature 8)
  const [trendsData, setTrendsData] = useState(null)
  const [loadingTrends, setLoadingTrends] = useState(false)

  // AI-Assisted Summarization State (Feature 10)
  const [showAiModal, setShowAiModal] = useState(false)
  const [aiData, setAiData] = useState(null)
  const [loadingAi, setLoadingAi] = useState(false)
  const [editableDraft, setEditableDraft] = useState('')
  const [approvingAi, setApprovingAi] = useState(false)

  // Create Case Modal state
  const [showCaseModal, setShowCaseModal] = useState(false)
  const [caseCategory, setCaseCategory] = useState('attendance')
  const [casePriority, setCasePriority] = useState('High')
  const [caseReason, setCaseReason] = useState('')
  const [caseObservations, setCaseObservations] = useState('')
  const [submittingCase, setSubmittingCase] = useState(false)
  const [caseSuccess, setCaseSuccess] = useState(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      apiGet(`/api/students/${studentId}`),
      apiGet(`/api/indicators?student_id=${studentId}`),
      apiGet(`/api/cases?student_id=${studentId}`),
    ])
      .then(([stuData, indData, caseData]) => {
        setStudent(stuData)
        setIndicators(indData.items || [])
        setCases(caseData.items || [])
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [studentId])

  useEffect(() => {
    if (activeTab === 'trends' && !trendsData) {
      setLoadingTrends(true)
      apiGet(`/api/students/${studentId}/trends`)
        .then(res => setTrendsData(res))
        .catch(err => console.error(err))
        .finally(() => setLoadingTrends(false))
    }
  }, [activeTab, studentId, trendsData])

  const handleCreateCase = async (e) => {
    e.preventDefault()
    setSubmittingCase(true)
    try {
      await apiPost('/api/cases', {
        student_id: parseInt(studentId, 10),
        assigned_staff_id: user.id,
        category: caseCategory,
        priority: casePriority,
        reason: caseReason,
        observations: caseObservations || undefined,
      })
      notify.success('Support case created successfully and assigned.', 'Case Created')
      setShowCaseModal(false)
      // Refresh cases
      const updatedCases = await apiGet(`/api/cases?student_id=${studentId}`)
      setCases(updatedCases.items || [])
    } catch (err) {
      notify.parseError(err, 'Failed to Create Support Case')
    } finally {
      setSubmittingCase(false)
    }
  }

  const handleOpenAiModal = async () => {
    setShowAiModal(true)
    setLoadingAi(true)
    try {
      const res = await apiGet(`/api/students/${studentId}/ai-summary`)
      setAiData(res)
      setEditableDraft(res.summary_text || '')
    } catch (err) {
      setAiData({ available: false, message: 'AI summaries unavailable' })
    } finally {
      setLoadingAi(false)
    }
  }

  const handleApproveAiSummary = async () => {
    if (!editableDraft.trim()) return
    setApprovingAi(true)
    try {
      await apiPost(`/api/students/${studentId}/ai-summary/approve`, {
        approved_text: editableDraft.trim(),
      })
      notify.success('AI Summary approved by staff and committed to official case record.', 'Summary Approved')
      setShowAiModal(false)
      // Refresh cases & timeline
      const updatedCases = await apiGet(`/api/cases?student_id=${studentId}`)
      setCases(updatedCases.items || [])
    } catch (err) {
      notify.parseError(err, 'Failed to Approve Summary')
    } finally {
      setApprovingAi(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
      </div>
    )
  }

  if (error || !student) {
    return (
      <div className="py-10 text-center font-body-sm text-body-sm text-error">
        {error || 'Student not found.'}
        <div className="mt-4">
          <Link to="/students" className="font-label-md text-label-md text-secondary hover:underline">
            ← Back to Student Directory
          </Link>
        </div>
      </div>
    )
  }

  const latestAtt = student.attendance_history?.length > 0
    ? student.attendance_history[student.attendance_history.length - 1]
    : null

  return (
    <div className="flex flex-col w-full">
      {/* Top back navigation */}
      <div className="flex items-center justify-between mb-3">
        <Link
          to="/students"
          className="inline-flex items-center gap-1 text-on-surface-variant hover:text-secondary font-label-md text-label-md transition-colors"
        >
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          <span>Back to Student Directory</span>
        </Link>
        <span className="font-label-sm text-label-sm text-on-surface-variant">
          EMIS: <strong className="font-numeric-table text-on-surface">{student.emis_id}</strong>
        </span>
      </div>

      {caseSuccess && (
        <div className="mb-4 px-3 py-2 rounded bg-secondary/10 text-secondary font-body-sm text-body-sm">
          {caseSuccess}
        </div>
      )}

      {/* Student Master Identity Card */}
      <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm mb-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <StudentAvatar student={student} size={64} className="rounded-xl flex-shrink-0 shadow-sm" />
            <div className="flex flex-col">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
                  {student.full_name}
                </h1>
                <span className="px-2 py-0.5 rounded bg-surface-container font-label-sm text-label-sm text-on-surface font-semibold uppercase">
                  {student.class_section ? `Grade ${student.class_section.grade}-${student.class_section.section}` : '—'}
                </span>
                {indicators.length > 0 && (
                  <Badge variant="needs_review">Needs Review ({indicators.length} indicators)</Badge>
                )}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-1 pt-2 font-body-sm text-body-sm text-on-surface-variant">
                <div>EMIS: <span className="font-semibold text-on-surface">{student.emis_id}</span></div>
                <div>Gender: <span className="text-on-surface">{student.gender || '—'}</span></div>
                <div>Guardian: <span className="text-on-surface">{student.guardian_name || '—'}</span></div>
                <div>Contact: <span className="text-on-surface">{student.guardian_phone || '—'}</span></div>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 justify-end">
            <button
              onClick={handleOpenAiModal}
              className="h-9 px-3 bg-surface-container-high text-on-surface hover:bg-surface-tint hover:text-on-primary font-label-md text-label-md rounded flex items-center gap-1.5 transition-colors"
            >
              <span className="material-symbols-outlined text-[16px] text-secondary">auto_awesome</span>
              <span>AI Record Summary</span>
            </button>
            <button
              onClick={() => setShowCaseModal(true)}
              className="h-9 px-3 bg-secondary text-on-secondary hover:bg-on-secondary-container font-label-md text-label-md rounded flex items-center gap-1 transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">add_circle</span>
              <span>Create Support Case</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
        {/* Attendance */}
        <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm flex flex-col justify-between">
          <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">Latest Attendance</span>
          <div className="my-2">
            <span className={`font-numeric-metric text-numeric-metric ${latestAtt && latestAtt.attendance_percentage < 75 ? 'text-error' : 'text-on-surface'}`}>
              {latestAtt ? `${latestAtt.attendance_percentage.toFixed(1)}%` : '—'}
            </span>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
              {latestAtt ? `${latestAtt.period_name} (${latestAtt.days_present}/${latestAtt.total_instructional_days} days)` : 'No records logged'}
            </p>
          </div>
        </div>

        {/* Indicators */}
        <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm flex flex-col justify-between">
          <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">Active Indicators</span>
          <div className="my-2">
            <span className={`font-numeric-metric text-numeric-metric ${indicators.length > 0 ? 'text-error' : 'text-on-surface'}`}>
              {indicators.length}
            </span>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
              {indicators.length > 0 ? 'Awaiting human review' : 'All clear'}
            </p>
          </div>
        </div>

        {/* Cases */}
        <div className="bg-surface-container-lowest rounded-xl p-4 shadow-sm flex flex-col justify-between">
          <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">Support Cases</span>
          <div className="my-2">
            <span className="font-numeric-metric text-numeric-metric text-on-surface">{cases.length}</span>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
              {cases.filter(c => c.status !== 'Closed').length} active cases
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-surface-container-lowest rounded-xl px-4 pt-2 shadow-sm mb-4">
        <div className="flex items-center gap-4 border-b border-outline-variant">
          {[
            { id: 'overview', label: 'Indicators & Evidence', icon: 'fact_check' },
            { id: 'attendance', label: 'Attendance History', icon: 'calendar_month' },
            { id: 'academic', label: 'Academic Scores', icon: 'school' },
            { id: 'cases', label: `Support Cases (${cases.length})`, icon: 'support_agent' },
            { id: 'timeline', label: 'Support History & Timeline', icon: 'timeline' },
            { id: 'trends', label: 'Longitudinal Trends', icon: 'trending_up' },
          ].map(tTab => (
            <button
              key={tTab.id}
              onClick={() => setActiveTab(tTab.id)}
              className={`py-3 px-2 font-label-md text-label-md flex items-center gap-1 transition-colors ${activeTab === tTab.id
                ? 'text-secondary border-b-2 border-secondary font-semibold'
                : 'text-on-surface-variant hover:text-on-surface'
                }`}
            >
              <span className="material-symbols-outlined text-[18px]">{tTab.icon}</span>
              <span>{tTab.label}</span>
            </button>
          ))}
        </div>

        <div className="py-4">
          {/* TAB 1: Indicators */}
          {activeTab === 'overview' && (
            <div>
              {indicators.length === 0 ? (
                <p className="font-body-sm text-body-sm text-on-surface-variant py-4 text-center">No active early indicators for this student.</p>
              ) : (
                <div className="space-y-3">
                  {indicators.map(ind => (
                    <div key={ind.id} className="p-4 rounded-xl bg-surface-container-low border border-outline-variant">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-headline-sm text-headline-sm text-on-surface">{ind.rule_code}</span>
                          <Badge variant={ind.priority?.toLowerCase()}>{ind.priority}</Badge>
                          <Badge variant="needs_review">{ind.status}</Badge>
                        </div>
                        <span className="font-body-sm text-body-sm text-on-surface-variant">
                          {new Date(ind.detected_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="font-body-md text-body-md text-on-surface mb-2">{ind.plain_explanation}</p>
                      {ind.supporting_evidence && (
                        <div className="p-3 bg-surface-container-lowest rounded font-mono text-body-sm text-on-surface-variant overflow-x-auto">
                          <pre>{JSON.stringify(ind.supporting_evidence, null, 2)}</pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Attendance */}
          {activeTab === 'attendance' && (
            <div>
              {student.attendance_history.length === 0 ? (
                <p className="font-body-sm text-body-sm text-on-surface-variant py-4 text-center">No attendance periods recorded.</p>
              ) : (
                <table className="w-full">
                  <thead>
                    <tr className="bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                      <th className="px-4 py-2 text-left">Period</th>
                      <th className="px-4 py-2 text-right">Days Present</th>
                      <th className="px-4 py-2 text-right">Total Days</th>
                      <th className="px-4 py-2 text-right">Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {student.attendance_history.map((att, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'}>
                        <td className="px-4 py-2 font-label-md text-label-md text-on-surface">{att.period_name}</td>
                        <td className="px-4 py-2 text-right">{att.days_present}</td>
                        <td className="px-4 py-2 text-right">{att.total_instructional_days}</td>
                        <td className="px-4 py-2 text-right font-numeric-table font-semibold">
                          <span className={att.attendance_percentage < 75 ? 'text-error' : 'text-on-surface'}>
                            {att.attendance_percentage?.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* TAB 3: Academic */}
          {activeTab === 'academic' && (
            <div>
              {student.assessment_history.length === 0 ? (
                <p className="font-body-sm text-body-sm text-on-surface-variant py-4 text-center">No assessments recorded.</p>
              ) : (
                <table className="w-full">
                  <thead>
                    <tr className="bg-surface-container text-on-surface-variant font-label-sm text-label-sm">
                      <th className="px-4 py-2 text-left">Assessment</th>
                      <th className="px-4 py-2 text-left">Subject</th>
                      <th className="px-4 py-2 text-left">Date</th>
                      <th className="px-4 py-2 text-right">Marks</th>
                      <th className="px-4 py-2 text-right">Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {student.assessment_history.map((asm, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'}>
                        <td className="px-4 py-2 font-label-md text-label-md text-on-surface">{asm.assessment_name}</td>
                        <td className="px-4 py-2">{asm.subject}</td>
                        <td className="px-4 py-2">{asm.assessment_date}</td>
                        <td className="px-4 py-2 text-right">{asm.marks_obtained} / {asm.max_marks}</td>
                        <td className="px-4 py-2 text-right font-numeric-table font-semibold">
                          <span className={asm.percentage < 35 ? 'text-error' : 'text-on-surface'}>
                            {asm.percentage?.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* TAB 4: Cases */}
          {activeTab === 'cases' && (
            <div>
              {cases.length === 0 ? (
                <p className="font-body-sm text-body-sm text-on-surface-variant py-4 text-center">No support cases logged for this student.</p>
              ) : (
                <div className="space-y-2">
                  {cases.map(c => (
                    <div key={c.id} className="p-3 bg-surface-container-low rounded-xl flex items-center justify-between">
                      <div>
                        <span className="font-label-md text-label-md font-semibold text-secondary">{c.case_number}</span>
                        <p className="font-body-sm text-body-sm text-on-surface">{c.reason}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={c.priority?.toLowerCase()}>{c.priority}</Badge>
                        <Badge variant="in_progress">{c.status}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 5: Unified Event Timeline (Feature 5) */}
          {activeTab === 'timeline' && (
            <div>
              <EventTimeline studentId={studentId} />
            </div>
          )}

          {/* TAB 6: Longitudinal Trends & Trajectories (Feature 8) */}
          {activeTab === 'trends' && (
            <div className="space-y-6">
              {/* Civic Trust Banner */}
              <div className="px-4 py-3 bg-surface-container-low rounded-xl border-l-4 border-secondary flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-secondary text-[20px]">timeline</span>
                  <strong className="text-on-surface font-label-md text-label-md">Data Integrity & Honest Gaps Mandate</strong>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  THULIR strictly forbids interpolating, smoothing, or fabricating missing historical attendance or assessment records. Trajectories reflect concrete logged data; unsubmitted or missing reporting periods are explicitly flagged as gaps.
                </p>
              </div>

              {loadingTrends ? (
                <div className="flex items-center justify-center py-16">
                  <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
                </div>
              ) : !trendsData ? (
                <p className="font-body-sm text-body-sm text-on-surface-variant py-4 text-center">No trend data available.</p>
              ) : (
                <div className="space-y-6">
                  {/* Attendance Trajectory Card */}
                  <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-headline-sm text-headline-sm text-on-surface">Attendance Longitudinal Trajectory</h3>
                        <p className="font-body-sm text-body-sm text-on-surface-variant">Cumulative Attendance: <strong className="text-secondary">{trendsData.cumulative_attendance_percentage ? `${trendsData.cumulative_attendance_percentage}%` : '—'}</strong></p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                      {trendsData.attendance_trajectory?.map((point, pIdx) => (
                        <div key={pIdx} className={`p-3 rounded-lg border flex flex-col justify-between ${point.has_data ? 'bg-surface-container-lowest border-outline-variant' : 'bg-amber-500/10 border-amber-500/30'}`}>
                          <div>
                            <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline block">{point.period_name}</span>
                            <span className="font-label-xs text-[11px] text-on-surface-variant block">{point.academic_year}</span>
                          </div>
                          <div className="mt-2">
                            {point.has_data ? (
                              <>
                                <span className={`font-numeric-metric text-headline-sm font-bold ${point.attendance_percentage < 75 ? 'text-error' : 'text-on-surface'}`}>
                                  {point.attendance_percentage}%
                                </span>
                                <span className="font-label-xs text-[11px] text-on-surface-variant block mt-0.5">
                                  {point.days_present} / {point.total_days} days
                                </span>
                              </>
                            ) : (
                              <div className="flex items-center gap-1 text-amber-700 py-1">
                                <span className="material-symbols-outlined text-[16px]">warning</span>
                                <span className="font-label-xs text-[11px] font-semibold">{point.gap_reason || 'Data Gap (Not Logged)'}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Academic Subject Trajectories */}
                  <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant">
                    <h3 className="font-headline-sm text-headline-sm text-on-surface mb-3">Academic Assessment Trajectories by Subject</h3>
                    <div className="space-y-4">
                      {Object.entries(trendsData.academic_trajectory || {}).map(([subject, points]) => (
                        <div key={subject} className="bg-surface-container-lowest rounded-lg p-3 border border-outline-variant">
                          <span className="font-label-md text-label-md font-semibold text-secondary block mb-2">{subject}</span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
                            {points.map((pt, idx) => (
                              <div key={idx} className={`p-2 rounded border ${pt.has_data ? 'bg-surface-container-low border-outline-variant/60' : 'bg-surface-container border-dashed border-outline-variant'}`}>
                                <span className="font-label-xs text-[11px] text-outline block">{pt.period_name}</span>
                                {pt.has_data ? (
                                  <div className="flex items-baseline justify-between mt-1">
                                    <span className={`font-numeric-table font-bold ${pt.average_percentage < 35 ? 'text-error' : 'text-on-surface'}`}>
                                      {pt.average_percentage}%
                                    </span>
                                    <span className="font-label-xs text-[10px] text-outline">
                                      {pt.assessments_count} exam{pt.assessments_count > 1 ? 's' : ''}
                                    </span>
                                  </div>
                                ) : (
                                  <span className="font-label-xs text-[10px] text-outline italic block mt-1">
                                    {pt.gap_reason || 'No Exam Logged'}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Assignment Trajectory */}
                  <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant">
                    <h3 className="font-headline-sm text-headline-sm text-on-surface mb-3">Assignment Completion Longitudinal Trajectory</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                      {trendsData.assignment_trajectory?.map((asg, aIdx) => (
                        <div key={aIdx} className={`p-3 rounded-lg border ${asg.has_data ? 'bg-surface-container-lowest border-outline-variant' : 'bg-surface-container border-dashed border-outline-variant'}`}>
                          <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline block">{asg.period_name}</span>
                          {asg.has_data ? (
                            <div className="mt-1">
                              <span className={`font-numeric-metric text-headline-sm font-bold ${asg.completion_rate < 60 ? 'text-error' : 'text-on-surface'}`}>
                                {asg.completion_rate}%
                              </span>
                              <span className="font-label-xs text-[11px] text-on-surface-variant block mt-0.5">
                                {asg.submitted_count} of {asg.total_assignments} assignments
                              </span>
                            </div>
                          ) : (
                            <span className="font-label-xs text-[11px] text-outline italic block mt-2">
                              {asg.gap_reason || 'No Assignments'}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create Case Modal */}
      {showCaseModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-lg w-full p-6 shadow-xl">
            <h2 className="font-headline-sm text-headline-sm text-on-surface mb-4">
              Create Support Case for {student.full_name}
            </h2>
            <form onSubmit={handleCreateCase} className="space-y-4">
              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">Category</label>
                <select
                  value={caseCategory}
                  onChange={e => setCaseCategory(e.target.value)}
                  className="w-full h-9 px-3 bg-surface-container-low text-on-surface rounded border border-outline-variant"
                >
                  <option value="attendance">Attendance Support</option>
                  <option value="academic">Academic & Remedial</option>
                  <option value="socio_welfare">Socio-Welfare</option>
                  <option value="behavioral">Behavioral Support</option>
                </select>
              </div>
              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">Priority</label>
                <select
                  value={casePriority}
                  onChange={e => setCasePriority(e.target.value)}
                  className="w-full h-9 px-3 bg-surface-container-low text-on-surface rounded border border-outline-variant"
                >
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">Primary Reason</label>
                <textarea
                  required
                  rows={2}
                  value={caseReason}
                  onChange={e => setCaseReason(e.target.value)}
                  placeholder="State the observed concern and context..."
                  className="w-full p-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                />
              </div>
              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">Staff Observations</label>
                <textarea
                  rows={2}
                  value={caseObservations}
                  onChange={e => setCaseObservations(e.target.value)}
                  placeholder="Optional background notes..."
                  className="w-full p-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCaseModal(false)}
                  className="px-4 py-2 bg-surface-container text-on-surface font-label-md text-label-md rounded hover:bg-surface-container-high transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCase}
                  className="px-4 py-2 bg-secondary text-on-secondary font-label-md text-label-md rounded hover:bg-on-secondary-container transition-colors disabled:opacity-60"
                >
                  {submittingCase ? 'Creating...' : 'Create Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* AI RECORD SUMMARY MODAL (FEATURE 10) */}
      {showAiModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-2xl w-full p-6 shadow-xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-outline-variant pb-3 mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-[24px]">auto_awesome</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">AI Record Summary & Draft</span>
              </div>
              <button onClick={() => setShowAiModal(false)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            {loadingAi ? (
              <div className="flex items-center justify-center py-16">
                <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
              </div>
            ) : !aiData || !aiData.available ? (
              <div className="py-8 text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-surface-container mx-auto flex items-center justify-center text-outline">
                  <span className="material-symbols-outlined text-[24px]">cloud_off</span>
                </div>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">
                  {aiData?.message || 'AI summaries unavailable'}
                </h3>
                <p className="font-body-sm text-body-sm text-on-surface-variant max-w-md mx-auto">
                  AI-assisted summarization is disabled by system policy (`AI_ENABLED=false`) or unconfigured. Every other core feature, indicator, and support case tool in THULIR functions completely normally.
                </p>
                <div className="pt-2">
                  <button
                    onClick={() => setShowAiModal(false)}
                    className="px-4 py-2 bg-surface-container text-on-surface rounded font-label-md hover:bg-surface-container-high transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Draft Mandate Alert */}
                <div className="p-3 bg-amber-500/10 border-l-4 border-amber-600 rounded-r-lg">
                  <div className="flex items-center gap-1.5 font-label-md text-amber-900 font-semibold">
                    <span className="material-symbols-outlined text-[18px]">verified</span>
                    <span>STAFF REVIEW MANDATE — DRAFT ONLY</span>
                  </div>
                  <p className="font-body-sm text-body-sm text-amber-800 mt-0.5">
                    This summary is a grounded draft synthesized from verified school records. It has not been committed to student history. A human staff member must review and explicitly approve before saving.
                  </p>
                </div>

                {/* Anonymized Metadata & Citations */}
                <div className="p-3 bg-surface-container-low rounded-lg font-body-sm text-body-sm space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-outline-variant/60 pb-2">
                    <div>
                      <span className="text-outline text-label-xs">Anonymized Reference ID: </span>
                      <strong className="text-on-surface font-mono">{aiData.anonymized_reference_id}</strong>
                    </div>
                    <div>
                      <span className="text-outline text-label-xs">Target Class: </span>
                      <strong className="text-on-surface">{aiData.class_label}</strong>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-surface-container text-label-xs font-semibold text-secondary uppercase">
                      {aiData.status}
                    </span>
                  </div>

                  <div>
                    <span className="text-outline text-label-xs block mb-1">Grounded Record Sources Cited:</span>
                    <div className="flex flex-wrap gap-1">
                      {aiData.sources_cited?.map((src, sIdx) => (
                        <span key={sIdx} className="px-2 py-0.5 rounded bg-surface-container font-mono text-[11px] text-on-surface">
                          {src}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Editable Text Area */}
                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-1">
                    Editable Record Summary Draft
                  </label>
                  <textarea
                    rows={6}
                    value={editableDraft}
                    onChange={e => setEditableDraft(e.target.value)}
                    className="w-full p-3 bg-surface-container-low text-on-surface rounded-lg border border-outline-variant font-body-sm text-body-sm focus:border-secondary focus:outline-none"
                    placeholder="Staff may refine or augment this summary before approving..."
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-2 border-t border-outline-variant">
                  <span className="font-label-xs text-[11px] text-on-surface-variant max-w-sm">
                    No PII (EMIS, name, contact) was shared with external providers.
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setShowAiModal(false)}
                      className="px-4 py-2 bg-surface-container text-on-surface font-label-md text-label-md rounded hover:bg-surface-container-high transition-colors"
                    >
                      Discard Draft
                    </button>
                    <button
                      type="button"
                      disabled={approvingAi || !editableDraft.trim()}
                      onClick={handleApproveAiSummary}
                      className="px-4 py-2 bg-secondary text-on-secondary font-label-md text-label-md rounded hover:bg-on-secondary-container transition-colors disabled:opacity-60 flex items-center gap-1.5"
                    >
                      <span className="material-symbols-outlined text-[16px]">check_circle</span>
                      <span>{approvingAi ? 'Approving...' : 'Approve & Save to Record'}</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

