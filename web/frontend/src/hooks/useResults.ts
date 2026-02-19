import { useState, useEffect } from 'react'
import { api } from '../api/client'
import type { FrameworkResults } from '../api/types'

export function useAllResults() {
  const [data, setData] = useState<Record<string, FrameworkResults> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = () => {
    setLoading(true)
    api
      .getAllResults()
      .then((d) => {
        setData(d)
        setError(null)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    refresh()
  }, [])

  return { data, loading, error, refresh }
}
