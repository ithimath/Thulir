import React from 'react'

export default function DemoDataBanner({ origin, onClearFilter }) {
  return (
    <div
      role="status"
      data-testid="demo-data-banner"
      className="bg-amber-500/15 border border-amber-500/30 text-amber-900 dark:text-amber-200 px-4 py-2.5 rounded-lg mb-4 flex items-center justify-between text-body-sm shadow-sm"
    >
      <div className="flex items-center gap-2.5">
        <span className="material-symbols-outlined text-amber-600 dark:text-amber-400 text-[20px]">science</span>
        <div>
          <span className="font-semibold text-label-md">Demo Data Active: </span>
          <span>
            Displaying simulated records generated to fill dataset gaps (working-day attendance registers, LMS continuous assessments, and sample support workflows).
          </span>
        </div>
      </div>
      {onClearFilter && (
        <button
          onClick={onClearFilter}
          className="ml-3 px-2.5 py-1 text-label-sm font-medium bg-amber-600/20 hover:bg-amber-600/30 text-amber-950 dark:text-amber-100 rounded transition-colors"
        >
          Show All Records
        </button>
      )}
    </div>
  )
}

