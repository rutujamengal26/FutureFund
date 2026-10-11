'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { analyzeDecision, type DecisionAnalysis } from '@/services/analysisService'

type Message = { role: 'user' | 'assistant'; text: string; graph?: { savings: number[]; expenses: number[] } }
type AnalysisContextValue = {
  analysis: DecisionAnalysis | null
  messages: Message[]
  loading: boolean
  error: string
  submit: (question: string) => Promise<void>
  setAnalysis: (analysis: DecisionAnalysis | null) => void
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null)

const STORAGE_KEY_ANALYSIS = 'futurefund_decision_analysis'
const STORAGE_KEY_MESSAGES = 'futurefund_decision_messages'

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const [analysis, setAnalysisState] = useState<DecisionAnalysis | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Restore persisted analysis on initial client mount
  useEffect(() => {
    try {
      const savedAnalysis = localStorage.getItem(STORAGE_KEY_ANALYSIS)
      if (savedAnalysis) {
        setAnalysisState(JSON.parse(savedAnalysis))
      }
      const savedMessages = localStorage.getItem(STORAGE_KEY_MESSAGES)
      if (savedMessages) {
        setMessages(JSON.parse(savedMessages))
      }
    } catch (e) {
      console.warn('Failed to restore saved analysis from storage:', e)
    }
  }, [])

  function setAnalysis(newAnalysis: DecisionAnalysis | null) {
    setAnalysisState(newAnalysis)
    try {
      if (newAnalysis) {
        localStorage.setItem(STORAGE_KEY_ANALYSIS, JSON.stringify(newAnalysis))
      } else {
        localStorage.removeItem(STORAGE_KEY_ANALYSIS)
      }
    } catch (e) {
      console.warn('Failed to persist analysis to storage:', e)
    }
  }

  async function submit(question: string) {
    const trimmed = question.trim()
    if (!trimmed || loading) return

    let transcript = messages.map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.text}`).join('\n')
    transcript += (transcript ? '\n' : '') + `User: ${trimmed}`

    setError('')
    const nextMessages = [...messages, { role: 'user' as const, text: trimmed }]
    setMessages(nextMessages)
    setLoading(true)

    try {
      const result = await analyzeDecision({ question: trimmed, transcript })
      setAnalysis(result)
      const updatedMessages = [...nextMessages, { role: 'assistant' as const, text: result.answer, graph: result.graph }]
      setMessages(updatedMessages)
      try {
        localStorage.setItem(STORAGE_KEY_MESSAGES, JSON.stringify(updatedMessages))
      } catch (e) {
        console.warn('Failed to persist messages:', e)
      }
    } catch (err: any) {
      setError(err?.message || 'We could not process that question. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const value = useMemo(
    () => ({ analysis, messages, loading, error, submit, setAnalysis }),
    [analysis, messages, loading, error]
  )

  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>
}

export function useAnalysis() {
  const context = useContext(AnalysisContext)
  if (!context) throw new Error('useAnalysis must be used inside AnalysisProvider')
  return context
}
