/** Authentication state shared by the whole application. */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import api, { setUnauthorizedHandler, tokenStore, userStore } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => userStore.get())
  const [checking, setChecking] = useState(() => Boolean(tokenStore.get()))

  const logout = useCallback(
    async ({ silent = false } = {}) => {
      if (!silent) {
        try {
          await api.logout()
        } catch {
          // Signing out locally must succeed even if the backend is unreachable.
        }
      }
      tokenStore.clear()
      setUser(null)
    },
    [],
  )

  // A 401 from any endpoint drops the stale session immediately.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      tokenStore.clear()
      setUser(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  // Re-validate a stored token on a hard page refresh.
  useEffect(() => {
    let cancelled = false
    const token = tokenStore.get()
    if (!token) {
      setChecking(false)
      return undefined
    }
    api
      .me()
      .then((profile) => {
        if (cancelled) return
        setUser(profile)
        userStore.set(profile, Boolean(localStorage.getItem('cyberguard.token')))
      })
      .catch((error) => {
        if (cancelled) return
        // Keep the cached session if the backend is merely offline; only a real
        // rejection (401) should sign the analyst out.
        if (error?.isAuth) {
          tokenStore.clear()
          setUser(null)
        }
      })
      .finally(() => !cancelled && setChecking(false))
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email, password, remember = true) => {
    const result = await api.login(email, password)
    tokenStore.set(result.token, remember)
    userStore.set(result.user, remember)
    setUser(result.user)
    return result.user
  }, [])

  const updateUser = useCallback((updated) => {
    setUser(updated)
    userStore.set(updated, Boolean(localStorage.getItem('cyberguard.token')))
  }, [])

  const value = useMemo(
    () => ({
      user,
      checking,
      isAuthenticated: Boolean(user),
      login,
      logout,
      updateUser,
    }),
    [user, checking, login, logout, updateUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside an AuthProvider')
  return context
}
