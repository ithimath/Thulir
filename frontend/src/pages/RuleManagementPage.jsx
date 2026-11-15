
import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { apiGet, apiPost } from '../api/client.js'
import { useAuth } from '../context/AuthContext.jsx'
import { useNotification } from '../context/NotificationContext.jsx'
import Badge from '../components/Badge.jsx'

export default function RuleManagementPage() {
  const { t } = useTranslation()
  const { role } = useAuth()
  const { notify } = useNotification()
  const isAdmin = role?.role_name === 'admin'

  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Edit / Version modal state
  const [selectedRule, setSelectedRule] = useState(null)
  const [newThreshold, setNewThreshold] = useState('')
  const [changeReason, setChangeReason] = useState('')
  const [simulation, setSimulation] = useState(null)
  const [simulating, setSimulating] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [activeVersionHistory, setActiveVersionHistory] = useState(null)

  const fetchRules = () => {
    setLoading(true)
    apiGet('/api/rules')
      .then(res => setRules(res.items || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchRules()
  }, [])

  const handleOpenEdit = (rule) => {
    setSelectedRule(rule)
    setNewThreshold(rule.threshold_value)
    setChangeReason('')
    setSimulation(null)
  }

  const handleSimulate = async () => {
    if (!selectedRule || !newThreshold) return
    setSimulating(true)
    try {
      const res = await apiGet(`/api/rules/preview-change?rule_code=${selectedRule.rule_code}&proposed_threshold=${newThreshold}`)
      setSimulation(res)
      notify.info('Rule simulation completed. Impact analysis updated below.', 'Simulation Complete')
    } catch (err) {
      notify.parseError(err, 'Simulation Failed')
    } finally {
      setSimulating(false)
    }
  }

  const handleSaveThreshold = async (e) => {
    e.preventDefault()
    if (!selectedRule || !newThreshold || !changeReason.trim()) {
      notify.warning('Please enter a valid threshold and justification reason.', 'Incomplete Form')
      return
    }
    setSubmitting(true)
    try {
      await apiPost(`/api/rules/${selectedRule.rule_code}/threshold`, {
        new_threshold: parseFloat(newThreshold),
        change_reason: changeReason.trim(),
      })
      notify.success(`Rule ${selectedRule.rule_code} updated successfully. A new version has been recorded.`, 'Rule Updated')
      setSelectedRule(null)
      fetchRules()
    } catch (err) {
      notify.parseError(err, 'Failed to Update Rule')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col w-full">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <div>
          <span className="font-headline-lg text-headline-lg text-on-surface tracking-tight">
            Early Warning Rule Configuration
          </span>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Deterministic detection rules, statutory thresholds, and versioned audit history.
          </p>
        </div>
      </div>

      {/* Governance Banner */}
      <div className="mb-4 px-4 py-3 bg-surface-container-low rounded-xl border-l-4 border-secondary">
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          <strong className="text-on-surface">ℹ Rule Integrity Mandate:</strong> Rule thresholds cannot be silently altered. Every modification increments the rule version, records an effective date and justification reason, and leaves historical indicators tied to their inception version.
        </p>
      </div>

      {/* Rules Table */}
      <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
          </div>
        ) : error ? (
          <div className="py-10 text-center font-body-sm text-body-sm text-error">{error}</div>
        ) : (
          <div className="overflow-x-auto w-full">
            <table className="w-full">
              <thead>
                <tr className="bg-surface-container border-b border-outline-variant text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
                  <th className="px-4 py-3 text-left">Rule Code & Version</th>
                  <th className="px-4 py-3 text-left">Category</th>
                  <th className="px-4 py-3 text-left">Active Threshold</th>
                  <th className="px-4 py-3 text-left">Detection Description</th>
                  <th className="px-4 py-3 text-center">Version History</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r, idx) => (
                  <tr key={r.id} className={`${idx % 2 === 0 ? 'bg-surface-container-lowest' : 'bg-surface-container-low'} hover:bg-surface-container transition-colors`}>
                    <td className="px-4 py-3 font-label-md text-label-md text-on-surface">
                      <span className="font-bold">{r.rule_code}</span>
                      <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-surface-container font-mono text-secondary">
                        v{r.current_version}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-body-sm text-body-sm text-on-surface capitalize">
                      {r.category}
                    </td>
                    <td className="px-4 py-3 font-mono text-sm font-semibold text-on-surface">
                      {r.threshold_value} {r.category === 'attendance' || r.category === 'assignment' ? '%' : ''}
                    </td>
                    <td className="px-4 py-3 font-body-sm text-body-sm text-on-surface-variant max-w-md">
                      {r.description}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => setActiveVersionHistory(r)}
                        className="text-secondary font-label-sm text-label-sm hover:underline"
                      >
                        {r.version_history.length} versions
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {isAdmin ? (
                        <button
                          onClick={() => handleOpenEdit(r)}
                          className="px-3 py-1 bg-surface-container text-secondary hover:bg-surface-container-high rounded font-label-md text-label-md transition-colors"
                        >
                          Edit Threshold
                        </button>
                      ) : (
                        <span className="font-label-sm text-label-sm text-outline">Read Only</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Threshold & Simulate Modal */}
      {selectedRule && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-lg w-full p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-outline-variant pb-3 mb-4">
              <span className="font-headline-sm text-headline-sm text-on-surface">
                Configure Rule: {selectedRule.rule_code}
              </span>
              <button onClick={() => setSelectedRule(null)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <form onSubmit={handleSaveThreshold} className="space-y-4 font-body-sm text-body-sm">
              <div className="p-3 bg-surface-container-low rounded">
                <div>Current Threshold: <strong>{selectedRule.threshold_value}</strong> (Version {selectedRule.current_version})</div>
                <div className="text-xs text-on-surface-variant mt-1">
                  Updating creates Version {selectedRule.current_version + 1}. Existing indicators remain on Version {selectedRule.current_version}.
                </div>
              </div>

              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">
                  Proposed Threshold Value
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    step="0.5"
                    required
                    value={newThreshold}
                    onChange={e => setNewThreshold(e.target.value)}
                    className="flex-1 h-9 px-3 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                  />
                  <button
                    type="button"
                    onClick={handleSimulate}
                    disabled={simulating}
                    className="px-3 py-1 bg-surface-container text-secondary hover:bg-surface-container-high rounded font-label-sm text-label-sm transition-colors flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-[16px]">query_stats</span>
                    <span>{simulating ? 'Simulating...' : 'Simulate'}</span>
                  </button>
                </div>
              </div>

              {/* Simulation Results */}
              {simulation && (
                <div className="p-3 bg-primary-container/10 border border-primary-container rounded font-body-sm text-body-sm">
                  <span className="font-label-sm text-label-sm font-semibold uppercase text-secondary block mb-1">
                    Historical Impact Simulation
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>Current Active Indicators: <strong>{simulation.current_indicators_count}</strong></div>
                    <div>Simulated Indicators: <strong>{simulation.simulated_indicators_count}</strong></div>
                    <div className="col-span-2 text-outline italic">{simulation.disclaimer}</div>
                  </div>
                </div>
              )}

              <div>
                <label className="block font-label-md text-label-md text-on-surface mb-1">
                  Justification Reason (Mandatory Audit Trail)
                </label>
                <textarea
                  required
                  rows={3}
                  value={changeReason}
                  onChange={e => setChangeReason(e.target.value)}
                  placeholder="State the administrative reason for altering this threshold..."
                  className="w-full p-2 bg-surface-container-low text-on-surface rounded border border-outline-variant font-body-sm text-body-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedRule(null)}
                  className="px-3 py-1.5 bg-surface-container text-on-surface font-label-md text-label-md rounded hover:bg-surface-container-high transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !changeReason.trim()}
                  className="px-4 py-1.5 bg-secondary text-on-secondary font-label-md text-label-md rounded hover:bg-on-secondary-container transition-colors disabled:opacity-60"
                >
                  {submitting ? 'Applying...' : 'Apply Version Increment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Version History Modal */}
      {activeVersionHistory && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest rounded-xl max-w-lg w-full p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-outline-variant pb-3 mb-4">
              <span className="font-headline-sm text-headline-sm text-on-surface">
                Version History: {activeVersionHistory.rule_code}
              </span>
              <button onClick={() => setActiveVersionHistory(null)} className="text-on-surface-variant hover:text-on-surface">
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="space-y-3 font-body-sm text-body-sm max-h-80 overflow-y-auto">
              {activeVersionHistory.version_history.map(vh => (
                <div key={vh.id} className="p-3 bg-surface-container-low rounded border border-outline-variant">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-secondary">Version {vh.version} {vh.is_active ? '(Active)' : '(Superseded)'}</span>
                    <span className="text-xs text-on-surface-variant">
                      Effective: {vh.effective_from || 'Initial Baseline'}
                    </span>
                  </div>
                  <div className="font-mono text-xs">Threshold: {vh.threshold_value}</div>
                  {vh.change_reason && (
                    <div className="text-xs text-on-surface-variant mt-1 italic">
                      Reason: {vh.change_reason}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-4">
              <button
                onClick={() => setActiveVersionHistory(null)}
                className="px-4 py-1.5 bg-surface-container text-on-surface font-label-md text-label-md rounded hover:bg-surface-container-high transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
