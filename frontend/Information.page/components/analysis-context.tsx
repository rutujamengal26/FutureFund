'use client'

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { analyzeDecision, type DecisionAnalysis } from '@/services/analysisService'
import { emptyUserProfile, parseUserProfile, type UserProfile } from '@/lib/user-profile'
import {
  chatHistoryStorageKey,
  parseChatHistory,
  type ChatConversation,
  type ChatMessage,
} from '@/lib/chat-history'

type AnalysisContextValue = {
  analysis: DecisionAnalysis | null
  messages: ChatMessage[]
  loading: boolean
  error: string
  submit: (question: string) => Promise<void>
  history: ChatConversation[]
  historyLoaded: boolean
  historyError: string
  currentConversationId: string | null
  selectConversation: (id: string) => void
  startNewConversation: () => void
  deleteConversation: (id: string) => boolean
  userProfile: UserProfile
  profileLoaded: boolean
  profileError: string
  updateUserProfile: (updates: Partial<UserProfile>) => boolean
}
const AnalysisContext = createContext<AnalysisContextValue | null>(null)
const profileStorageKey = 'futurefunds.user-profile.v1'

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const [analysis, setAnalysis] = useState<DecisionAnalysis | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [userProfile, setUserProfile] = useState<UserProfile>(emptyUserProfile)
  const [profileLoaded, setProfileLoaded] = useState(false)
  const [profileError, setProfileError] = useState('')
  const [history, setHistory] = useState<ChatConversation[]>([])
  const [historyLoaded, setHistoryLoaded] = useState(false)
  const [historyError, setHistoryError] = useState('')
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)

  useEffect(() => {
    try {
      const storedHistory = window.localStorage.getItem(chatHistoryStorageKey)
      if (storedHistory) {
        const parsedHistory: unknown = JSON.parse(storedHistory)
        const validHistory = parseChatHistory(parsedHistory)
        if (!validHistory) {
          setHistoryError('Saved chat history is invalid and could not be loaded.')
        } else {
          setHistory(validHistory)
          const latest = validHistory[0]
          if (latest) {
            setCurrentConversationId(latest.id)
            setMessages(latest.messages)
            setAnalysis(latest.analysis)
          }
        }
      }
    } catch {
      setHistoryError('We could not read your saved chat history from this browser.')
    } finally {
      setHistoryLoaded(true)
    }
  }, [])

  useEffect(() => {
    try {
      const storedProfile = window.localStorage.getItem(profileStorageKey)
      if (storedProfile) {
        const parsedProfile: unknown = JSON.parse(storedProfile)
        const validProfile = parseUserProfile(parsedProfile)
        if (!validProfile) {
          setProfileError('Saved profile data is invalid. Update your profile to replace it.')
        } else {
          setUserProfile(validProfile)
        }
      }
    } catch {
      setProfileError('We could not read your saved profile from this browser.')
    } finally {
      setProfileLoaded(true)
    }
  }, [])

  const updateUserProfile = useCallback((updates: Partial<UserProfile>) => {
    const nextProfile = { ...userProfile, ...updates }
    try {
      window.localStorage.setItem(profileStorageKey, JSON.stringify(nextProfile))
      setUserProfile(nextProfile)
      setProfileError('')
      return true
    } catch {
      setProfileError('Your profile could not be saved in this browser. Check its storage settings and try again.')
      return false
    }
  }, [userProfile])

  const persistHistory = useCallback((nextHistory: ChatConversation[]) => {
    try {
      window.localStorage.setItem(chatHistoryStorageKey, JSON.stringify(nextHistory))
      setHistory(nextHistory)
      setHistoryError('')
      return true
    } catch {
      setHistoryError('Chat history could not be saved in this browser. Check its storage settings and try again.')
      return false
    }
  }, [])

  const selectConversation = useCallback((id: string) => {
    const selected = history.find((conversation) => conversation.id === id)
    if (!selected) return
    setCurrentConversationId(selected.id)
    setMessages(selected.messages)
    setAnalysis(selected.analysis)
    setError('')
  }, [history])

  const startNewConversation = useCallback(() => {
    setCurrentConversationId(null)
    setMessages([])
    setAnalysis(null)
    setError('')
  }, [])

  const deleteConversation = useCallback((id: string) => {
    if (!history.some((conversation) => conversation.id === id)) return false
    const nextHistory = history.filter((conversation) => conversation.id !== id)
    if (!persistHistory(nextHistory)) return false
    if (currentConversationId === id) startNewConversation()
    return true
  }, [currentConversationId, history, persistHistory, startNewConversation])

  async function submit(question: string) {
    const trimmed = question.trim()
    if (!trimmed || loading || !historyLoaded) return
    const conversationId = currentConversationId ?? crypto.randomUUID()
    const questionMessages = [...messages, { role: 'user' as const, text: trimmed }]
    setCurrentConversationId(conversationId)
    setError('')
    setMessages(questionMessages)
    setLoading(true)

    const saveConversation = (nextMessages: ChatMessage[], nextAnalysis: DecisionAnalysis | null) => {
      const firstQuestion = nextMessages.find((message) => message.role === 'user')?.text ?? 'New conversation'
      const conversation: ChatConversation = {
        id: conversationId,
        title: firstQuestion.length > 72 ? `${firstQuestion.slice(0, 69)}...` : firstQuestion,
        updatedAt: new Date().toISOString(),
        messages: nextMessages,
        analysis: nextAnalysis,
      }
      persistHistory([conversation, ...history.filter((item) => item.id !== conversationId)])
    }

    try {
      const result = await analyzeDecision({ question: trimmed })
      const nextMessages = [...questionMessages, { role: 'assistant' as const, text: result.answer }]
      setAnalysis(result)
      setMessages(nextMessages)
      saveConversation(nextMessages, result)
    }
    catch {
      setError('We could not process that question. Please try again.')
      saveConversation(questionMessages, analysis)
    }
    finally { setLoading(false) }
  }
  const value = useMemo(() => ({
    analysis, messages, loading, error, submit, history, historyLoaded, historyError,
    currentConversationId, selectConversation, startNewConversation, deleteConversation,
    userProfile, profileLoaded, profileError, updateUserProfile,
  }), [
    analysis, messages, loading, error, history, historyLoaded, historyError,
    currentConversationId, selectConversation, startNewConversation, deleteConversation,
    userProfile, profileLoaded, profileError, updateUserProfile,
  ])
  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>
}
export function useAnalysis() { const context = useContext(AnalysisContext); if (!context) throw new Error('useAnalysis must be used inside AnalysisProvider'); return context }
