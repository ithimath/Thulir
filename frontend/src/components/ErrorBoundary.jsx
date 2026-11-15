import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo })
    console.error('[THULIR Global ErrorBoundary Caught]', error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.href = '/overview'
  }

  render() {
    if (this.state.hasError) {
      const isDev = process.env.NODE_ENV !== 'production'

      return (
        <div className="min-h-screen bg-surface flex items-center justify-center p-6 text-on-surface">
          <div className="w-full max-w-lg bg-surface-container-lowest border border-outline-variant/40 rounded-2xl shadow-xl p-8 text-center">
            <div className="w-16 h-16 rounded-2xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center justify-center mx-auto mb-4">
              <span className="material-symbols-outlined text-[36px]">error</span>
            </div>

            <h2 className="font-headline-sm text-xl font-bold text-on-surface">
              Something went wrong
            </h2>

            <p className="mt-2 font-body-sm text-sm text-on-surface-variant leading-relaxed">
              An unexpected display error occurred while rendering this view. Your saved records and system data remain completely safe.
            </p>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 rounded-lg font-label-md text-xs font-semibold bg-surface-container hover:bg-surface-container-high border border-outline-variant/40 text-on-surface transition-colors"
              >
                Go to Overview
              </button>
              <button
                onClick={this.handleReload}
                className="px-4 py-2 rounded-lg font-label-md text-xs font-semibold bg-gradient-to-r from-teal-600 to-teal-700 hover:from-teal-500 hover:to-teal-600 text-white shadow-sm transition-all"
              >
                Reload Application
              </button>
            </div>

            {isDev && this.state.error && (
              <details className="mt-6 text-left border-t border-outline-variant/20 pt-4">
                <summary className="font-mono text-xs text-rose-600 dark:text-rose-400 cursor-pointer font-semibold">
                  Technical Diagnostics (Dev Mode)
                </summary>
                <pre className="mt-2 p-3 bg-surface-container text-xs font-mono rounded overflow-x-auto text-on-surface-variant max-h-48">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

