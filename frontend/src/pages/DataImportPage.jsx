import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { apiGet, apiPost, apiUpload } from '../api/client.js'
import Badge from '../components/Badge.jsx'

export default function DataImportPage() {
  const { t } = useTranslation()

  const [file, setFile] = useState(null)
  const [importType, setImportType] = useState('students')
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState(null)
  const [confirming, setConfirming] = useState(false)
  const [commitResult, setCommitResult] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)

  useEffect(() => {
    apiGet('/api/import/history')
      .then(res => setHistory(res || []))
      .catch(() => setHistory([]))
      .finally(() => setLoadingHistory(false))
  }, [commitResult])

  const handleFileChange = (e) => {
    if (e.target.files?.length > 0) {
      setFile(e.target.files[0])
      setPreview(null)
      setCommitResult(null)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    setCommitResult(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('import_type', importType)

    try {
      const res = await apiUpload('/api/import/upload', formData)
      setPreview(res)
    } catch (err) {
      alert('Upload failed: ' + err.message)
    } finally {
      setUploading(false)
    }
  }

  const handleConfirm = async () => {
    if (!preview) return
    setConfirming(true)
    try {
      const res = await apiPost(`/api/import/${preview.batch_id}/confirm`, {})
      setCommitResult(res)
      setPreview(null)
      setFile(null)
    } catch (err) {
      alert('Commit failed: ' + err.message)
    } finally {
      setConfirming(false)
    }
  }

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <div>
          <span className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            {t('nav.data_import')} & Quality Guardrails
          </span>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Upload student records, periodic attendance registers, or assessment scorecards. Previews and duplicate detection run before any database commit.
          </p>
        </div>
      </div>

      {commitResult && (
        <div className="mb-4 p-4 rounded-xl bg-secondary/10 border border-secondary text-on-surface">
          <div className="flex items-center gap-2 font-headline-sm text-headline-sm text-secondary mb-1">
            <span className="material-symbols-outlined text-[20px]">check_circle</span>
            <span>Import Completed</span>
          </div>
          <p className="font-body-sm text-body-sm">{commitResult.message}</p>
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
                onChange={e => setImportType(e.target.value)}
                className="w-full h-10 px-3 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
              >
                <option value="students">Student Cohort Master Directory (CSV/XLSX)</option>
              </select>
            </div>
            <div>
              <label className="block font-label-md text-label-md text-on-surface mb-1">Select File</label>
              <input
                type="file"
                accept=".csv, .xlsx, .xls"
                onChange={handleFileChange}
                className="w-full h-10 px-2 py-1 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="submit"
              disabled={!file || uploading}
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
        )}
      </div>
    </div>
  )
}

