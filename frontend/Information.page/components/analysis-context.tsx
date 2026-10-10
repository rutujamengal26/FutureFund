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
    async function loadHistory() {
      let loadedFromBackend = false;
      if (typeof window !== 'undefined' && localStorage.getItem('token')) {
        try {
          const { fetchAPI } = await import('@/lib/api');
          const { mapBackendResponseToDecisionAnalysis } = await import('@/services/analysisService');
          const summaries = await fetchAPI('/api/v1/analyses');
          
          if (summaries && summaries.length > 0) {
             const fullHistory: ChatConversation[] = [];
             for (const summary of summaries) {
                const detail = await fetchAPI(`/api/v1/analyses/${summary.id}`);
                const q = detail.request_snapshot?.text || 'Historical Analysis';
                
                const analysisObj = mapBackendResponseToDecisionAnalysis(q, detail.response_snapshot || { status: summary.status });
                
                const msg: ChatMessage = { role: 'user', text: q };
                const resp: ChatMessage = { role: 'assistant', text: analysisObj.answer, graph: analysisObj.graph };
                
                fullHistory.push({
                   id: summary.id,
                   title: q.length > 72 ? `${q.slice(0, 69)}...` : q,
                   updatedAt: summary.created_at,
                   messages: [msg, resp],
                   analysis: analysisObj
                });
             }
             setHistory(fullHistory);
             if (fullHistory.length > 0) {
               setCurrentConversationId(fullHistory[0].id);
               setMessages(fullHistory[0].messages);
               setAnalysis(fullHistory[0].analysis);
             }
             loadedFromBackend = true;
          }
        } catch (e) {
          console.error("Failed to fetch history from backend", e);
        }
      }

      if (!loadedFromBackend) {
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
        }
      }
      setHistoryLoaded(true);
    }
    loadHistory();
  }, [])

  useEffect(() => {
    async function loadProfile() {
      let loadedFromBackend = false;
      if (typeof window !== 'undefined' && localStorage.getItem('token')) {
        try {
          const { fetchAPI } = await import('@/lib/api');
          const profiles = await fetchAPI('/api/v1/profiles');
          if (profiles && profiles.length > 0) {
            const profileData = profiles[0].profile_data;
            const validProfile = {
              ...emptyUserProfile,
              name: profiles[0].profile_name || '',
              income: profileData.monthly_income_inr?.toString() || '',
              expenses: (profileData.monthly_rent_inr + profileData.essential_expenses_excluding_rent_inr + profileData.variable_expenses_inr)?.toString() || '',
              savings: profileData.current_savings_inr?.toString() || '',
              emi: profileData.existing_monthly_emi_inr?.toString() || ''
            };
            setUserProfile(validProfile);
            window.localStorage.setItem(profileStorageKey, JSON.stringify(validProfile));
            loadedFromBackend = true;
          }
        } catch (e) {
          console.error("Failed to fetch profile from backend", e);
        }
      }

      if (!loadedFromBackend) {
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
        }
      }
      setProfileLoaded(true);
    }
    loadProfile();
  }, [])

  const updateUserProfile = useCallback(async (updates: Partial<UserProfile>) => {
    const nextProfile = { ...userProfile, ...updates }
    try {
      window.localStorage.setItem(profileStorageKey, JSON.stringify(nextProfile))
      setUserProfile(nextProfile)
      setProfileError('')
      
      // Attempt to save to backend if authenticated
      if (typeof window !== 'undefined' && localStorage.getItem('token')) {
        const { fetchAPI } = await import('@/lib/api');
        
        // Map frontend UserProfile to backend ProfileSchema
        const profileData = {
          monthly_income_inr: nextProfile.income ? parseFloat(nextProfile.income) : 0,
          other_income_inr: 0,
          monthly_rent_inr: nextProfile.expenses ? parseFloat(nextProfile.expenses) * 0.4 : 0,
          essential_expenses_excluding_rent_inr: nextProfile.expenses ? parseFloat(nextProfile.expenses) * 0.4 : 0,
          variable_expenses_inr: nextProfile.expenses ? parseFloat(nextProfile.expenses) * 0.2 : 0,
          current_savings_inr: nextProfile.savings ? parseFloat(nextProfile.savings) : 0,
          existing_monthly_emi_inr: nextProfile.emi ? parseFloat(nextProfile.emi) : 0
        };

        await fetchAPI('/api/v1/profiles', {
          method: 'POST',
          body: JSON.stringify({
            profile_name: nextProfile.name || 'Default Profile',
            profile_data: profileData,
            is_default: true
          })
        });
      }
      return true
    } catch (e: any) {
      // Don't show error if it's just an auth error, we still saved locally
      if (e.message !== 'Not authenticated' && e.message !== 'Could not validate credentials') {
        console.error("Failed to save profile to backend:", e);
      }
      return true // returning true because local save succeeded
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
      let transcript = messages.map(m => `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.text}`).join('\n')
      transcript += (transcript ? '\n' : '') + `User: ${trimmed}`
      
      const result = await analyzeDecision({ question: trimmed, transcript, profile: userProfile })
      const nextMessages = [...questionMessages, { role: 'assistant' as const, text: result.answer, graph: result.graph }]
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
