import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiGet, apiPost } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import Badge from '../components/Badge.jsx'

export default function StudentProfilePage() {
  const { studentId } = useParams()
  const { t } = useTranslation()
  const { user, role } = useAuth()

  const [student, setStudent] = useState(null)
  const [indicators, setIndicators] = useState([])
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Active tab state: 'overview' | 'attendance' | 'academic' | 'cases'
  const [activeTab, setActiveTab] = useState('overview')

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
      setCaseSuccess('Support case created successfully.')
      setShowCaseModal(false)
      // Refresh cases
      const updatedCases = await apiGet(`/api/cases?student_id=${studentId}`)
      setCases(updatedCases.items || [])
    } catch (err) {
      alert('Error: ' + err.message)
    } finally {
      setSubmittingCase(false)
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
            <div className="w-16 h-16 rounded-xl bg-primary-container flex items-center justify-center flex-shrink-0 text-on-primary">
              <span className="material-symbols-outlined text-[32px]">person</span>
            </div>
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
          ].map(tTab => (
            <button
              key={tTab.id}
              onClick={() => setActiveTab(tTab.id)}
              className={`py-3 px-2 font-label-md text-label-md flex items-center gap-1 transition-colors ${
                activeTab === tTab.id
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
    </div>
  )
}

