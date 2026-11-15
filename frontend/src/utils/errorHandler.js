/**
 * Centralized Error Parser and Formatter for THULIR.
 *
 * Translates raw backend errors, HTTP status codes, network errors, and file validation
 * exceptions into clear, actionable, user-friendly notification payloads.
 *
 * Preserves developer diagnostics in console.error while shielding end-users from raw stack traces.
 */

export function parseError(err, fallbackTitle = 'Action Failed') {
  if (process.env.NODE_ENV !== 'production') {
    console.error('[THULIR Error]', err)
  }

  // 1. String error
  if (typeof err === 'string') {
    return parseMessageString(err, fallbackTitle)
  }

  // 2. Network / Offline error
  if (err?.name === 'TypeError' && err?.message?.includes('fetch')) {
    return {
      title: 'Connection Error',
      message: 'Unable to reach the THULIR server. Please verify your network connection.',
      type: 'error',
    }
  }

  // 3. HTTP status-specific handling
  const status = err?.status || err?.response?.status
  const detail = err?.data?.detail || err?.message || ''

  if (status === 401) {
    return {
      title: 'Session Expired',
      message: 'Your sign-in session has expired or is invalid. Please sign in again.',
      type: 'warning',
    }
  }

  if (status === 403) {
    return {
      title: 'Access Restricted',
      message: typeof detail === 'string' && detail && !detail.startsWith('HTTP')
        ? detail
        : 'You do not have administrative permission to perform this action.',
      type: 'warning',
    }
  }

  if (status === 404) {
    return {
      title: 'Not Found',
      message: typeof detail === 'string' && detail && !detail.startsWith('HTTP')
        ? detail
        : 'The requested record or resource was not found.',
      type: 'error',
    }
  }

  if (status === 413) {
    return {
      title: 'File Size Exceeded',
      message: 'The uploaded file exceeds the maximum allowed size limit of 5 MB. Please reduce the file size and try again.',
      type: 'error',
    }
  }

  if (status === 422 || status === 400) {
    return parseValidationDetail(detail, fallbackTitle)
  }

  if (status >= 500) {
    return {
      title: 'Server Error',
      message: 'An unexpected server error occurred. The technical details have been logged.',
      type: 'error',
    }
  }

  // 4. General error message parsing
  return parseMessageString(detail || err?.message || 'An unexpected error occurred.', fallbackTitle)
}

/**
 * Parses validation error messages, detecting missing columns or structured row errors.
 */
function parseValidationDetail(detail, fallbackTitle) {
  if (Array.isArray(detail)) {
    // FastAPI / Pydantic validation error array
    const fieldErrors = detail.map(d => {
      const field = d.loc ? d.loc.filter(l => l !== 'body').join('.') : 'field'
      return `${field}: ${d.msg}`
    })
    return {
      title: 'Validation Error',
      message: 'Please correct the highlighted inputs:',
      listItems: fieldErrors,
      type: 'error',
    }
  }

  const str = String(detail || '')

  // Missing required columns pattern: "Missing required columns in student file: emis_id, grade, full_name"
  const missingColMatch = str.match(/Missing required columns in ([^:]+) file:\s*(.+)/i)
  if (missingColMatch) {
    const fileType = missingColMatch[1].trim()
    const columns = missingColMatch[2].split(',').map(c => c.trim()).filter(Boolean)
    return {
      title: `${capitalize(fileType)} File Validation Failed`,
      message: `The uploaded file is missing ${columns.length} required column${columns.length > 1 ? 's' : ''}:`,
      listItems: columns,
      suggestion: 'Please verify the header row in your CSV/Excel file matches the required template and upload again.',
      type: 'error',
    }
  }

  // Duplicate EMIS
  if (str.toLowerCase().includes('duplicate emis')) {
    return {
      title: 'Duplicate Record Detected',
      message: str,
      suggestion: 'Check your file for repeated student IDs before submitting.',
      type: 'warning',
    }
  }

  // General CSV parsing error
  if (str.toLowerCase().includes('failed to parse')) {
    return {
      title: 'Unreadable File Format',
      message: str,
      suggestion: 'Ensure the file is a standard UTF-8 CSV or valid Microsoft Excel (.xlsx) file.',
      type: 'error',
    }
  }

  return {
    title: fallbackTitle || 'Validation Failed',
    message: str || 'The submitted data could not be validated.',
    type: 'error',
  }
}

function parseMessageString(str, fallbackTitle) {
  const text = String(str || '')
  if (text.startsWith('Missing required columns')) {
    return parseValidationDetail(text, fallbackTitle)
  }
  return {
    title: fallbackTitle,
    message: text,
    type: 'error',
  }
}

function capitalize(s) {
  if (!s) return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
}

