/**
 * Thin API client. All requests go through the Vite dev proxy to http://localhost:8000.
 * Cookies (HttpOnly session) are sent automatically via credentials: 'include'.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

async function request(method, path, body) {
  const opts = {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) {
    opts.body = JSON.stringify(body)
  }

  const res = await fetch(`${BASE_URL}${path}`, opts)

  if (res.status === 204) return null

  let data
  try {
    data = await res.json()
  } catch {
    const fallbackMessage = res.status === 404
      ? 'Backend service or requested endpoint not found (HTTP 404). Please ensure the backend is running at http://127.0.0.1:8000.'
      : (res.statusText || `HTTP ${res.status}`)
    data = { detail: fallbackMessage }
  }

  if (!res.ok) {
    const message = data?.detail || (res.status === 404 ? 'Endpoint not found (HTTP 404)' : `HTTP ${res.status}`)
    const err = new Error(typeof message === 'string' ? message : JSON.stringify(message))
    err.status = res.status
    err.data = data
    throw err
  }

  return data
}

export const apiGet    = (path)         => request('GET',    path)
export const apiPost   = (path, body)   => request('POST',   path, body)
export const apiPut    = (path, body)   => request('PUT',    path, body)
export const apiDelete = (path)         => request('DELETE', path)

/**
 * Upload a file (multipart/form-data).
 */
export async function apiUpload(path, formData) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    credentials: 'include',
    body: formData, // do NOT set Content-Type — browser sets it with boundary
  })
  let data
  try {
    data = await res.json()
  } catch {
    const fallbackMessage = res.status === 404
      ? 'Backend service or requested endpoint not found (HTTP 404). Please ensure the backend is running at http://127.0.0.1:8000.'
      : (res.statusText || `HTTP ${res.status}`)
    data = { detail: fallbackMessage }
  }
  if (!res.ok) {
    const message = data?.detail || (res.status === 404 ? 'Endpoint not found (HTTP 404)' : `HTTP ${res.status}`)
    const err = new Error(typeof message === 'string' ? message : JSON.stringify(message))
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

