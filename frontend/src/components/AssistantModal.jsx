import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { apiPost } from '../api/client.js'

export default function AssistantModal() {
  const { t, i18n } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const quickPrompts = [
    { labelEn: '75% Attendance Norms', labelTa: '75% வருகை விதி', q: 'What is the minimum attendance requirement for exam eligibility?' },
    { labelEn: '3-Day Absence SOP', labelTa: '3 நாள் விடுப்பு SOP', q: 'What is the procedure for 3 consecutive unexcused absences?' },
    { labelEn: '35% Pass Criteria', labelTa: '35% தேர்ச்சி மதிப்பெண்', q: 'What are the pass mark criteria for continuous assessments?' },
    { labelEn: '7 Rules Catalog', labelTa: '7 விதிகள் விவரம்', q: 'List all 7 THULIR early-warning rules and thresholds' },
    { labelEn: 'Case Note Privacy', labelTa: 'ரகசிய ஆவண பாதுகாப்பு', q: 'How does the confidential case notes privacy model work?' },
  ]

  const handleAsk = async (textToAsk) => {
    const q = textToAsk || query
    if (!q.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await apiPost('/api/assistant/query', {
        query: q.trim(),
        language: i18n.language === 'ta' ? 'ta' : 'en',
      })
      setResult(res)
    } catch (err) {
      setError(err.message || 'Failed to query assistant.')
    } finally {
      setLoading(false)
    }
  }

  const handleQuickPrompt = (promptText) => {
    setQuery(promptText)
    handleAsk(promptText)
  }

  return (
    <>
      {/* Floating Action Button */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-3 bg-secondary text-on-secondary rounded-full shadow-lg hover:bg-on-secondary-container hover:shadow-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-secondary/50 font-label-md text-label-md"
          title="Institutional Policy & Early-Warning Rules Guide"
        >
          <span className="material-symbols-outlined text-[20px]">menu_book</span>
          <span className="hidden sm:inline font-medium">Policy & Rules Guide</span>
        </button>
      </div>

      {/* Modal Backdrop & Drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-fade-in">
          <div className="bg-surface-container-lowest w-full max-w-2xl rounded-2xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden border border-outline-variant">
            {/* Header */}
            <div className="px-6 py-4 bg-surface-container border-b border-outline-variant flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-[24px]">school</span>
                <div>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface">
                    THULIR Policy & SOP Guide
                  </h3>
                  <p className="font-label-sm text-label-sm text-on-surface-variant">
                    Statutory Tamil Nadu School Regulations & Early-Warning Formulas
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-outline hover:text-on-surface hover:bg-surface-container-high transition-colors"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            {/* Content Body */}
            <div className="p-6 overflow-y-auto space-y-4">
              {/* Institutional Non-Predictive Ethics Notice */}
              <div className="p-3 bg-surface-container-low rounded-xl border-l-4 border-secondary text-body-sm text-on-surface-variant flex items-start gap-2">
                <span className="material-symbols-outlined text-secondary text-[18px] shrink-0 mt-0.5">verified_user</span>
                <div>
                  <strong className="text-on-surface">Non-Predictive System: </strong>
                  THULIR does not predict dropouts, calculate psychological ratings, or infer emotions. Every rule is a deterministic prompt for educator review.
                </div>
              </div>

              {/* Quick Prompts */}
              <div>
                <span className="font-label-sm text-label-sm uppercase text-outline tracking-wider block mb-2">
                  Frequently Queried Guidelines
                </span>
                <div className="flex flex-wrap gap-2">
                  {quickPrompts.map((p, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleQuickPrompt(p.q)}
                      className="px-3 py-1.5 bg-surface-container text-on-surface hover:bg-secondary hover:text-on-secondary rounded-lg text-label-sm font-label-sm transition-colors text-left"
                    >
                      {i18n.language === 'ta' ? p.labelTa : p.labelEn}
                    </button>
                  ))}
                </div>
              </div>

              {/* Form Input */}
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleAsk()
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask about attendance codes, pass cutoffs, or warning indicators..."
                  className="flex-1 h-11 px-4 rounded-xl border border-outline-variant bg-surface-container-low text-on-surface font-body-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-secondary/40 focus:bg-surface-container-lowest"
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="h-11 px-5 bg-secondary text-on-secondary rounded-xl font-label-md text-label-md flex items-center gap-2 hover:bg-on-secondary-container transition-colors disabled:opacity-50 shadow-sm"
                >
                  {loading ? (
                    <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                  ) : (
                    <span className="material-symbols-outlined text-[18px]">send</span>
                  )}
                  <span>Ask</span>
                </button>
              </form>

              {/* Error Output */}
              {error && (
                <div className="p-3 bg-error-container/20 border border-error/20 rounded-xl text-error text-body-sm">
                  {error}
                </div>
              )}

              {/* Assistant Response Card */}
              {result && (
                <div className={`p-4 rounded-xl border ${result.is_refusal ? 'bg-error-container/10 border-error/30' : 'bg-surface-container-low border-outline-variant'} space-y-3`}>
                  {result.title && (
                    <div className="font-headline-sm text-headline-sm text-on-surface font-semibold flex items-center gap-2">
                      <span className="material-symbols-outlined text-secondary text-[20px]">
                        {result.is_refusal ? 'gavel' : 'menu_book'}
                      </span>
                      <span>{result.title}</span>
                    </div>
                  )}

                  <p className="font-body-md text-body-md text-on-surface whitespace-pre-line leading-relaxed">
                    {result.response}
                  </p>

                  {result.grounded_sources && result.grounded_sources.length > 0 && (
                    <div className="pt-2 border-t border-outline-variant/60 flex flex-wrap items-center gap-1 text-label-sm text-on-surface-variant">
                      <span className="font-medium text-outline">Authoritative Sources:</span>
                      {result.grounded_sources.map((s, i) => (
                        <span key={i} className="inline-block px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-mono text-[11px]">
                          {s}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="text-[11px] text-outline italic">
                    ℹ {result.disclaimer}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 bg-surface-container border-t border-outline-variant flex items-center justify-between text-label-sm text-on-surface-variant">
              <span>Bilingual: English & தமிழ்</span>
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-1.5 rounded-lg bg-surface-container-highest hover:bg-surface-container-high text-on-surface font-label-md text-label-md transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

