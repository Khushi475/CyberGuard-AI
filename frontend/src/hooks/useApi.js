/** Data-fetching hooks shared by every page. */
import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Runs an async request and tracks loading / error / data, with a manual
 * `refresh()` and optional polling. Guards against setting state after unmount
 * and against out-of-order responses.
 */
export function useApi(request, dependencies = [], { immediate = true, pollMs = 0 } = {}) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(immediate)
  const mounted = useRef(true)
  const requestId = useRef(0)
  const requestRef = useRef(request)
  requestRef.current = request

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  const execute = useCallback(async ({ quiet = false } = {}) => {
    const id = requestId.current + 1
    requestId.current = id
    if (!quiet) setLoading(true)
    try {
      const result = await requestRef.current()
      if (!mounted.current || id !== requestId.current) return null
      setData(result)
      setError(null)
      return result
    } catch (caught) {
      if (!mounted.current || id !== requestId.current) return null
      setError(caught)
      return null
    } finally {
      if (mounted.current && id === requestId.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (immediate) execute()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies)

  useEffect(() => {
    if (!pollMs) return undefined
    const timer = window.setInterval(() => execute({ quiet: true }), pollMs)
    return () => window.clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pollMs, ...dependencies])

  return { data, error, loading, refresh: execute, setData }
}

/** Debounces a rapidly changing value (used by every search box). */
export function useDebounced(value, delay = 400) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(timer)
  }, [value, delay])
  return debounced
}

/** Local-storage backed state for small UI preferences. */
export function usePersistentState(key, initialValue) {
  const [value, setValue] = useState(() => {
    try {
      const stored = localStorage.getItem(key)
      return stored === null ? initialValue : JSON.parse(stored)
    } catch {
      return initialValue
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch {
      // Storage may be unavailable (private mode); the app still works.
    }
  }, [key, value])

  return [value, setValue]
}
