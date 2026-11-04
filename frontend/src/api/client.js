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
    data = { detail: res.statusText }
  }

  if (!res.ok) {
    const err = new Error(data?.detail || `HTTP ${res.status}`)
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
  const data = await res.json().catch(() => ({ detail: res.statusText }))
  if (!res.ok) {
    const err = new Error(data?.detail || `HTTP ${res.status}`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

