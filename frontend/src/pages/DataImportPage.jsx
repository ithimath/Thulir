import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiGet, apiPost, apiUpload } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useNotification } from '../context/NotificationContext.jsx'
import Badge from '../components/Badge.jsx'

export default function DataImportPage() {
  const { t } = useTranslation()
  const { role } = useAuth()
  const { notify, confirm } = useNotification()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = searchParams.get('tab') === 'quality' ? 'quality' : 'import'
  const [activeTab, setActiveTab] = useState(initialTab)

  // Import State
  const [file, setFile] = useState(null)
  const [importType, setImportType] = useState('students')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [preview, setPreview] = useState(null)
  const [confirming, setConfirming] = useState(false)
  const [commitResult, setCommitResult] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)

  // Data Quality State
  const [qualitySummary, setQualitySummary] = useState(null)
  const [qualityIssues, setQualityIssues] = useState([])
  const [loadingQuality, setLoadingQuality] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [classFilter, setClassFilter] = useState('')

  // Correction Proposal Modal state
  const [showCorrectionModal, setShowCorrectionModal] = useState(false)
  const [correctionTarget, setCorrectionTarget] = useState(null)
  const [correctionRecordType, setCorrectionRecordType] = useState('attendance')
  const [correctionRecordId, setCorrectionRecordId] = useState('')
  const [correctionField, setCorrectionField] = useState('days_present')
  const [correctionValue, setCorrectionValue] = useState('')
  const [correctionReason, setCorrectionReason] = useState('')
  const [submittingCorrection, setSubmittingCorrection] = useState(false)

  // Fetch Import History
  const fetchHistory = useCallback(() => {
    setLoadingHistory(true)
    apiGet('/api/import/history')
      .then(res => setHistory(res || []))
      .catch(err => {
        console.error('Failed to load import history:', err)
        setHistory([])
      })
      .finally(() => setLoadingHistory(false))
  }, [])

  useEffect(() => {
    if (activeTab === 'import') {
      fetchHistory()
    }
  }, [activeTab, fetchHistory])

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setPreview(null)
      setCommitResult(null)
      setUploadError(null)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) {
      notify.warning('Please select a valid CSV or XLSX file to upload.', 'No File Selected')
      return
    }
    setUploading(true)
    setCommitResult(null)
    setUploadError(null)
    const formData = new FormData()
    formData.append('file', file)
    formData.append('import_type', importType)

    try {
      const res = await apiUpload('/api/import/upload', formData)
      setPreview(res)
      notify.info(
        `File validated successfully. ${res.total_rows} records analyzed (${res.valid_count} valid, ${res.warnings_count} updates, ${res.rejected_count} rejected).`,
        'File Validation Complete'
      )
    } catch (err) {
      setUploadError(err.message || 'File validation failed.')
      notify.parseError(err, 'Student File Validation Failed')
    } finally {
      setUploading(false)
    }
  }

  const handleConfirm = async () => {
    if (!preview?.batch_id) return
    const isConfirmed = await confirm({
      title: 'Confirm Data Import',
      message: `Are you sure you want to commit this import batch? ${preview.valid_count} valid records will be stored in the database and early-warning indicators will be updated.`,
      confirmText: 'Commit Import',
      cancelText: 'Cancel',
      type: 'primary',
    })
    if (!isConfirmed) return

    setConfirming(true)
    try {
      const res = await apiPost(`/api/import/${preview.batch_id}/confirm`)
      setCommitResult(res)
      setPreview(null)
      setFile(null)
      notify.success(
        `Import committed successfully! ${res.imported} new records saved, ${res.duplicates} existing updated, ${res.rejected} rejected.`,
        'Import Succeeded'
      )
      fetchHistory()
    } catch (err) {
      notify.parseError(err, 'Failed to Commit Import')
    } finally {
      setConfirming(false)
    }
  }

  const fetchQualityData = useCallback(() => {
    setLoadingQuality(true)
    const params = new URLSearchParams()
    if (categoryFilter) params.set('category', categoryFilter)
    if (classFilter) {
      const parts = classFilter.split('-')
      if (parts[0]) params.set('grade', parts[0])
      if (parts[1]) params.set('section', parts[1])
    }

    Promise.all([
      apiGet('/api/data-quality/summary'),
      apiGet(`/api/data-quality/issues?${params}`),
    ])
      .then(([summaryRes, issuesRes]) => {
        setQualitySummary(summaryRes)
        setQualityIssues(issuesRes.items || [])
      })
      .catch(err => console.error(err))
      .finally(() => setLoadingQuality(false))
  }, [categoryFilter, classFilter])

  useEffect(() => {
    if (activeTab === 'quality') {
      fetchQualityData()
    }
  }, [activeTab, fetchQualityData])

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    setSearchParams(tab === 'quality' ? { tab: 'quality' } : {})
  }

  const handleOpenCorrection = (issue = null) => {
    setCorrectionTarget(issue)
    if (issue) {
      if (issue.category.includes('attendance')) {
        setCorrectionRecordType('attendance')
        setCorrectionField('days_present')
      } else if (issue.category.includes('marks')) {
        setCorrectionRecordType('assessment')
        setCorrectionField('score')
      } else if (issue.category.includes('assignment')) {
        setCorrectionRecordType('assignment')
        setCorrectionField('score')
      }
      setCorrectionRecordId(issue.record_id || '')
      setCorrectionReason(`Correction proposed from data quality alert: ${issue.title}`)
    } else {
      setCorrectionRecordId('')
      setCorrectionReason('')
    }
    setCorrectionValue('')
    setShowCorrectionModal(true)
  }

  const handleSubmitCorrection = async (e) => {
    e.preventDefault()
    if (!correctionRecordId || !correctionValue || !correctionReason.trim()) {
      notify.warning('Please fill in all required fields before submitting.', 'Incomplete Form')
      return
    }
    setSubmittingCorrection(true)
    try {
      let val = correctionValue
      if (correctionField === 'score' || correctionField === 'days_present') {
        const num = parseFloat(correctionValue)
        if (!isNaN(num)) val = num
      }

      await apiPost('/api/corrections', {
        record_type: correctionRecordType,
        record_id: parseInt(correctionRecordId, 10),
        proposed_changes: { [correctionField]: val },
        reason: correctionReason.trim(),
      })
      notify.success('Correction proposed successfully. Awaiting administrator review.', 'Correction Submitted')
      setShowCorrectionModal(false)
      if (activeTab === 'quality') fetchQualityData()
    } catch (err) {
      notify.parseError(err, 'Failed to Propose Correction')
    } finally {
      setSubmittingCorrection(false)
    }
  }

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <div>
          <span className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            {activeTab === 'quality' ? t('data_quality.title') : t('nav.data_import')}
          </span>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            {activeTab === 'quality'
              ? t('data_quality.subtitle')
              : 'Upload student records, periodic registers, or assessment scorecards with verification previews.'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center bg-surface-container-low p-1 rounded-lg border border-outline-variant">
          <button
            onClick={() => handleTabChange('import')}
            className={`px-4 py-1.5 rounded-md font-label-md text-label-md transition-all flex items-center gap-1.5 ${activeTab === 'import'
              ? 'bg-surface-container-lowest text-secondary shadow-sm font-semibold'
              : 'text-on-surface-variant hover:text-on-surface'
              }`}
          >
            <span className="material-symbols-outlined text-[18px]">upload_file</span>
            <span>{t('nav.data_import')}</span>
          </button>
          <button
            onClick={() => handleTabChange('quality')}
            className={`px-4 py-1.5 rounded-md font-label-md text-label-md transition-all flex items-center gap-1.5 ${activeTab === 'quality'
              ? 'bg-surface-container-lowest text-secondary shadow-sm font-semibold'
              : 'text-on-surface-variant hover:text-on-surface'
              }`}
          >
            <span className="material-symbols-outlined text-[18px]">verified_user</span>
            <span>{t('data_quality.title')}</span>
          </button>
        </div>
      </div>

      {/* TAB 1: DATA IMPORT */}
      {activeTab === 'import' && (
        <>
          {commitResult && (
            <div className="mb-4 p-4 rounded-xl bg-secondary/10 border border-secondary text-on-surface">
              <div className="flex items-center gap-2 font-headline-sm text-headline-sm text-secondary mb-1">
                <span className="material-symbols-outlined text-[20px]">check_circle</span>
                <span>Import Completed</span>
              </div>
              <p className="font-body-sm text-body-sm">{commitResult.message}</p>
            </div>
          )}

          {role && role.role_name !== 'admin' && (
            <div className="mb-4 px-4 py-3 rounded-xl bg-surface-container-low border border-outline-variant/30 flex items-center gap-2.5 text-on-surface-variant font-body-sm text-body-sm">
              <span className="material-symbols-outlined text-[20px] text-secondary">info</span>
              <span>
                <strong>Notice:</strong> File upload and record commitment require <strong>School Administrator</strong> privileges. Staff members may view import history and inspect data quality alerts below.
              </span>
            </div>
          )}

          {/* Upload Box */}
          <div className="bg-surface-container-lowest rounded-xl p-6 shadow-sm mb-4">
            <form onSubmit={handleUpload} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-1">Import Data Domain</label>
                  <select
                    value={importType}
                    disabled={role?.role_name !== 'admin'}
                    onChange={e => setImportType(e.target.value)}
                    className="w-full h-10 px-3 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm disabled:opacity-60"
                  >
                    <option value="students">Student Cohort Master Directory (CSV/XLSX)</option>
                    <option value="attendance">Periodic Attendance Registers (CSV/XLSX)</option>
                    <option value="marks">Assessment & Exam Scorecards (CSV/XLSX)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-1">Select File</label>
                  <input
                    type="file"
                    accept=".csv, .xlsx, .xls"
                    disabled={role?.role_name !== 'admin'}
                    onChange={handleFileChange}
                    className={`w-full h-10 px-2 py-1 bg-surface-container-low text-on-surface rounded border ${
                      uploadError ? 'border-rose-500 ring-1 ring-rose-500/30' : 'border-outline-variant'
                    } font-body-sm text-body-sm disabled:opacity-60 transition-colors`}
                  />
                  {uploadError && (
                    <div className="mt-3 p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-800 rounded-lg flex items-start gap-2.5 text-rose-900 dark:text-rose-200">
                      <span className="material-symbols-outlined text-[20px] text-rose-600 dark:text-rose-400 flex-shrink-0 mt-0.5">
                        error
                      </span>
                      <div className="flex-1 text-xs">
                        <span className="font-bold block mb-0.5">Validation Alert:</span>
                        <span>{uploadError}</span>
                        <p className="mt-1 opacity-80 italic">
                          Tip: Ensure column headers match statutory specifications (e.g., student files require: <code>emis_id, full_name, grade, section</code>).
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  type="submit"
                  disabled={!file || uploading || role?.role_name !== 'admin'}
                  className="h-10 px-4 bg-secondary text-on-secondary hover:bg-on-secondary-container font-label-md text-label-md rounded flex items-center gap-2 transition-colors disabled:opacity-60"
                >
                  {uploading ? (
                    <span className="material-symbols-outlined text-[16px] animate-spin">progress_activity</span>
                  ) : (
                    <span className="material-symbols-outlined text-[16px]">upload</span>
                  )}
                  <span>{uploading ? 'Validating File...' : 'Upload & Validate'}</span>
                </button>
              </div>
            </form>
          </div>

          {/* Preview Section */}
          {preview && (
            <div className="bg-surface-container-lowest rounded-xl p-6 shadow-sm mb-4">
              <div className="flex items-center justify-between border-b border-outline-variant pb-3 mb-4">
                <div>
                  <span className="font-headline-sm text-headline-sm text-on-surface">Import Validation Preview</span>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">
                    File: <strong>{preview.file_name}</strong> • Total Rows: <strong>{preview.total_rows}</strong>
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPreview(null)}
                    className="px-3 py-1.5 bg-surface-container text-on-surface rounded font-label-md text-label-md hover:bg-surface-container-high transition-colors"
                  >
                    Discard
                  </button>
                  <button
                    onClick={handleConfirm}
                    disabled={confirming}
                    className="px-4 py-1.5 bg-secondary text-on-secondary rounded font-label-md text-label-md hover:bg-on-secondary-container transition-colors disabled:opacity-60 flex items-center gap-1"
                  >
                    {confirming ? 'Committing...' : 'Confirm & Commit to Database'}
                  </button>
                </div>
              </div>

              {/* Counts */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 font-body-sm text-body-sm">
                <div className="p-3 bg-surface-container-low rounded">
                  <span className="text-on-surface-variant">Valid Records:</span>
                  <div className="font-numeric-metric text-on-surface text-emerald-600">{preview.valid_count}</div>
                </div>
                <div className="p-3 bg-surface-container-low rounded">
                  <span className="text-on-surface-variant">Existing to Update:</span>
                  <div className="font-numeric-metric text-on-surface text-amber-600">{preview.warnings_count}</div>
                </div>
                <div className="p-3 bg-surface-container-low rounded">
                  <span className="text-on-surface-variant">Duplicate Rows (Skipped):</span>
                  <div className="font-numeric-metric text-on-surface text-outline">{preview.duplicates_count}</div>
                </div>
                <div className="p-3 bg-surface-container-low rounded">
                  <span className="text-on-surface-variant">Rejected / Invalid:</span>
                  <div className="font-numeric-metric text-on-surface text-error">{preview.rejected_count}</div>
                </div>
              </div>

              {/* Issues list if any */}
              {preview.row_issues.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-label-md text-label-md font-semibold text-on-surface mb-2">Validation Alerts</h3>
                  <div className="space-y-1">
                    {preview.row_issues.map((iss, i) => (
                      <div key={i} className="p-2 bg-surface-container-low rounded font-body-sm text-body-sm flex items-center justify-between">
                        <span>Row {iss.row_number}: {iss.message}</span>
                        <Badge variant={iss.category === 'rejected' ? 'critical' : 'moderate'}>{iss.category}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* History Table */}
          <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b border-outline-variant">
              <span className="font-headline-sm text-headline-sm text-on-surface">Recent Import History</span>
            </div>
            {loadingHistory ? (
              <div className="flex items-center justify-center py-8">
                <span className="material-symbols-outlined text-[24px] text-secondary animate-spin">progress_activity</span>
              </div>
            ) : history.length === 0 ? (
              <div className="py-8 text-center font-body-sm text-body-sm text-on-surface-variant">
                No previous imports recorded.
              </div>
            ) : (
              <div className="overflow-x-auto w-full">
                <table className="w-full">
                  <thead>
                    <tr className="bg-surface-container text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
                      <th className="px-4 py-2 text-left">File Name</th>
                      <th className="px-4 py-2 text-left">Domain</th>
                      <th className="px-4 py-2 text-right">Rows</th>
                      <th className="px-4 py-2 text-right">Imported</th>
                      <th className="px-4 py-2 text-center">Status</th>
                      <th className="px-4 py-2 text-right">Committed At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((b, idx) => (
                      <tr key={b.id} className={idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'}>
                        <td className="px-4 py-2 font-label-md text-label-md text-on-surface">{b.file_name}</td>
                        <td className="px-4 py-2 uppercase font-label-sm text-label-sm text-on-surface-variant">{b.import_type}</td>
                        <td className="px-4 py-2 text-right font-numeric-table">{b.total_rows}</td>
                        <td className="px-4 py-2 text-right font-numeric-table text-emerald-600 font-semibold">{b.imported_count}</td>
                        <td className="px-4 py-2 text-center">
                          <Badge variant={b.status === 'committed' ? 'stable' : 'critical'}>{b.status}</Badge>
                        </td>
                        <td className="px-4 py-2 text-right font-body-sm text-body-sm text-on-surface-variant">
                          {b.committed_at ? new Date(b.committed_at).toLocaleDateString() : '—'}
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

      {/* TAB 2: DATA QUALITY MONITOR (FEATURE 3) */}
      {activeTab === 'quality' && (
        <>
          {/* Quality Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm border-l-4 border-secondary">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">
                {t('data_quality.completeness_score')}
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="font-numeric-metric text-numeric-metric text-on-surface">
                  {qualitySummary ? `${qualitySummary.profile_completeness_pct}%` : '—'}
                </span>
                <span className="font-body-sm text-body-sm text-on-surface-variant">
                  ({qualitySummary?.complete_profiles_count}/{qualitySummary?.total_students} profiles)
                </span>
              </div>
            </div>

            <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm border-l-4 border-emerald-600">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">
                {t('data_quality.attendance_completeness')}
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="font-numeric-metric text-numeric-metric text-on-surface">
                  {qualitySummary ? `${qualitySummary.attendance_completeness_pct}%` : '—'}
                </span>
                <span className="font-body-sm text-body-sm text-on-surface-variant">expected terms logged</span>
              </div>
            </div>

            <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm border-l-4 border-amber-500">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">
                Total Quality Alerts
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="font-numeric-metric text-numeric-metric text-amber-700">
                  {qualitySummary?.total_issues_count ?? 0}
                </span>
                <span className="font-body-sm text-body-sm text-on-surface-variant">actionable issues</span>
              </div>
            </div>

            <div className="bg-surface-container-lowest p-4 rounded-xl shadow-sm border-l-4 border-primary">
              <span className="font-label-sm text-label-sm uppercase tracking-wider text-outline">
                Active Cohort Size
              </span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="font-numeric-metric text-numeric-metric text-on-surface">
                  {qualitySummary?.total_students ?? 0}
                </span>
                <span className="font-body-sm text-body-sm text-on-surface-variant">students registered</span>
              </div>
            </div>
          </div>

          {/* Civic Trust Banner */}
          <div className="mb-4 px-4 py-3 bg-surface-container-low rounded-xl border-l-4 border-outline flex items-center justify-between">
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              <strong className="text-on-surface">ℹ Data Trust Principle:</strong>{' '}
              {t('data_quality.disclaimer')} Completeness and error counts reflect concrete database records, never an opaque model score.
            </p>
            <button
              onClick={() => handleOpenCorrection()}
              className="px-3 py-1.5 bg-secondary text-on-secondary rounded font-label-md text-label-md hover:bg-on-secondary-container transition-colors flex items-center gap-1 shrink-0"
            >
              <span className="material-symbols-outlined text-[16px]">edit_note</span>
              <span>{t('corrections.propose')}</span>
            </button>
          </div>

          {/* Quality Filters */}
          <div className="flex flex-wrap gap-2 mb-4">
            <select
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
              className="h-9 px-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant"
            >
              <option value="">All Issue Categories</option>
              <option value="missing_attendance">Missing Attendance</option>
              <option value="duplicate_student_id">Duplicate Student EMIS</option>
              <option value="invalid_marks">Invalid Marks</option>
              <option value="invalid_attendance">Invalid Attendance Values</option>
              <option value="conflicting_period">Conflicting Periods</option>
              <option value="incomplete_profile">Incomplete Student Profile</option>
              <option value="invalid_assignment">Corrupted Assignment</option>
              <option value="import_error">Import Validation Rejections</option>
            </select>

            <select
              value={classFilter}
              onChange={e => setClassFilter(e.target.value)}
              className="h-9 px-3 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded border border-outline-variant"
            >
              <option value="">All Classes</option>
              <option value="9-A">Grade 9 - Section A</option>
              <option value="9-B">Grade 9 - Section B</option>
              <option value="10-A">Grade 10 - Section A</option>
              <option value="10-B">Grade 10 - Section B</option>
            </select>
          </div>

          {/* Quality Issues List */}
          <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
            <div className="p-4 border-b border-outline-variant flex items-center justify-between">
              <span className="font-headline-sm text-headline-sm text-on-surface">
                Audit Findings ({qualityIssues.length})
              </span>
              <button
                onClick={fetchQualityData}
                className="text-secondary font-label-sm text-label-sm hover:underline flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-[16px]">refresh</span>
                <span>Refresh Audit</span>
              </button>
            </div>

            {loadingQuality ? (
              <div className="flex items-center justify-center py-12">
                <span className="material-symbols-outlined text-[28px] text-secondary animate-spin">progress_activity</span>
              </div>
            ) : qualityIssues.length === 0 ? (
              <div className="py-12 text-center font-body-sm text-body-sm text-on-surface-variant">
                <span className="material-symbols-outlined text-[36px] text-emerald-600 block mb-2">check_circle</span>
                {t('data_quality.no_issues')}
              </div>
            ) : (
              <div className="overflow-x-auto w-full">
                <table className="w-full">
                  <thead>
                    <tr className="bg-surface-container text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
                      <th className="px-4 py-2 text-left">Category</th>
                      <th className="px-4 py-2 text-left">Issue Description</th>
                      <th className="px-4 py-2 text-left">Affected Student</th>
                      <th className="px-4 py-2 text-center">Severity</th>
                      <th className="px-4 py-2 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {qualityIssues.map((iss, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'}>
                        <td className="px-4 py-2 font-label-md text-label-md text-on-surface capitalize">
                          {iss.category.replace(/_/g, ' ')}
                        </td>
                        <td className="px-4 py-2">
                          <div className="font-label-md text-label-md text-on-surface font-semibold">{iss.title}</div>
                          <div className="font-body-sm text-body-sm text-on-surface-variant">{iss.detail}</div>
                        </td>
                        <td className="px-4 py-2 font-body-sm text-body-sm text-on-surface">
                          {iss.student_name ? (
                            <div>
                              <span className="font-semibold">{iss.student_name}</span>
                              <span className="text-on-surface-variant block text-label-sm">{iss.class_section || ''} {iss.emis_id ? `(EMIS: ${iss.emis_id})` : ''}</span>
                            </div>
                          ) : 'Cohorts / Multiple'}
                        </td>
                        <td className="px-4 py-2 text-center">
                          <Badge variant={iss.severity === 'high' ? 'critical' : iss.severity === 'medium' ? 'moderate' : 'low'}>
                            {iss.severity}
                          </Badge>
                        </td>
                        <td className="px-4 py-2 text-right">
                          {iss.record_id ? (
                            <button
                              onClick={() => handleOpenCorrection(iss)}
                              className="px-2.5 py-1 bg-surface-container text-secondary hover:bg-surface-container-high rounded font-label-sm text-label-sm transition-colors"
                            >
                              Propose Correction
                            </button>
                          ) : (
                            <span className="font-label-sm text-label-sm text-outline">Master Record</span>
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

      {/* PROPOSE CORRECTION MODAL (FEATURE 2) */}
      {showCorrectionModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-lg w-full p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-outline-variant pb-3 mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-[24px]">edit_note</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">{t('corrections.propose')}</span>
              </div>
              <button onClick={() => setShowCorrectionModal(false)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <p className="font-body-sm text-body-sm text-on-surface-variant mb-4 bg-surface-container-low p-2.5 rounded">
              {t('corrections.superseded_notice')}
            </p>

            <form onSubmit={handleSubmitCorrection} className="space-y-3 font-body-sm text-body-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-1">Record Domain</label>
                  <select
                    value={correctionRecordType}
                    onChange={e => setCorrectionRecordType(e.target.value)}
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
                    value={correctionRecordId}
                    onChange={e => setCorrectionRecordId(e.target.value)}
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
                    value={correctionField}
                    onChange={e => setCorrectionField(e.target.value)}
                    placeholder="e.g. days_present or score"
                    className="w-full h-9 px-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                  />
                </div>

                <div>
                  <label className="block font-label-md text-label-md text-on-surface mb-1">Corrected Value</label>
                  <input
                    type="text"
                    required
                    value={correctionValue}
                    onChange={e => setCorrectionValue(e.target.value)}
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
                  value={correctionReason}
                  onChange={e => setCorrectionReason(e.target.value)}
                  placeholder="Explain why this record is being amended (e.g. verified with physical attendance register)..."
                  className="w-full p-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCorrectionModal(false)}
                  className="px-3 py-1.5 bg-surface-container text-on-surface font-label-md text-label-md rounded hover:bg-surface-container-high transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingCorrection}
                  className="px-4 py-1.5 bg-secondary text-on-secondary font-label-md text-label-md rounded hover:bg-on-secondary-container transition-colors disabled:opacity-60"
                >
                  {submittingCorrection ? 'Submitting...' : 'Submit Proposal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

