import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { apiGet, apiPost } from '../api/client.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)       // { id, username, full_name, designation }
  const [role, setRole] = useState(null)       // { role_name, school_id, school_name, assigned_classes }
  const [loading, setLoading] = useState(true) // initial session check
  const [error, setError] = useState(null)

  // On mount, check if we have a valid session via GET /api/auth/me
  // /api/auth/me returns UserProfileOut: { id, username, full_name, ..., current_role }
  useEffect(() => {
    apiGet('/api/auth/me')
      .then(data => {
        // data is UserProfileOut — extract user fields and role from current_role
        const { current_role, ...userFields } = data
        setUser(userFields)
        setRole({
          role_name: current_role.role,
          school_id: current_role.school_id,
          school_name: current_role.school_name,
          assigned_classes: current_role.assigned_classes,
        })
      })
      .catch(() => {
        setUser(null)
        setRole(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (username, password) => {
    setError(null)
    // POST /api/auth/login returns LoginResponse: { message, user (UserProfileOut), token }
    const data = await apiPost('/api/auth/login', { username, password })
    const { current_role, ...userFields } = data.user
    setUser(userFields)
    setRole({
      role_name: current_role.role,
      school_id: current_role.school_id,
      school_name: current_role.school_name,
      assigned_classes: current_role.assigned_classes,
    })
    return data
  }, [])

  const logout = useCallback(async () => {
    try {
      await apiPost('/api/auth/logout', {})
    } catch (_) {
      // ignore errors on logout
    }
    setUser(null)
    setRole(null)
  }, [])

  const isAuthenticated = !!user

  return (
    <AuthContext.Provider value={{ user, role, loading, error, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
