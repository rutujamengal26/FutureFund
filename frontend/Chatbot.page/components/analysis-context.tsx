'use client'

import { createContext, useContext, useMemo, useState } from 'react'
import { analyzeDecision, type DecisionAnalysis } from '@/services/analysisService'

type Message = { role: 'user' | 'assistant'; text: string }
type AnalysisContextValue = { analysis: DecisionAnalysis | null; messages: Message[]; loading: boolean; error: string; submit: (question: string) => Promise<void> }
const AnalysisContext = createContext<AnalysisContextValue | null>(null)

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const [analysis, setAnalysis] = useState<DecisionAnalysis | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  async function submit(question: string) {
    const trimmed = question.trim()
    if (!trimmed || loading) return
    setError(''); setMessages((current) => [...current, { role: 'user', text: trimmed }]); setLoading(true)
    try { const result = await analyzeDecision({ question: trimmed }); setAnalysis(result); setMessages((current) => [...current, { role: 'assistant', text: result.answer }]) }
    catch { setError('We could not process that question. Please try again.') }
    finally { setLoading(false) }
  }
  const value = useMemo(() => ({ analysis, messages, loading, error, submit }), [analysis, messages, loading, error])
  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>
}
export function useAnalysis() { const context = useContext(AnalysisContext); if (!context) throw new Error('useAnalysis must be used inside AnalysisProvider'); return context }
