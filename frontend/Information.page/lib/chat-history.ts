import type { DecisionAnalysis } from '@/services/analysisService'

export type ChatMessage = { role: 'user' | 'assistant'; text: string; graph?: { savings: number; expenses: number } }

export type ChatConversation = {
  id: string
  title: string
  updatedAt: string
  messages: ChatMessage[]
  analysis: DecisionAnalysis | null
}

export const chatHistoryStorageKey = 'futurefunds.chat-history.v1'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function parseMessages(value: unknown): ChatMessage[] | null {
  if (!Array.isArray(value)) return null
  const messages: ChatMessage[] = []
  for (const item of value) {
    if (!isRecord(item) || (item.role !== 'user' && item.role !== 'assistant') || typeof item.text !== 'string') {
      return null
    }
    messages.push({ role: item.role, text: item.text, graph: item.graph as any })
  }
  return messages
}

function hasStringFields(value: unknown, fields: string[]): value is Record<string, unknown> {
  return isRecord(value) && fields.every((field) => typeof value[field] === 'string')
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function isDecisionAnalysis(value: unknown): value is DecisionAnalysis {
  if (
    !hasStringFields(value, ['id', 'question', 'summary', 'answer', 'createdAt']) ||
    !isStringArray(value.availableAnalyses) ||
    !isRecord(value.stressTest) ||
    !hasStringFields(value.stressTest, [
      'incomeDrop', 'emergencyExpense', 'expenseIncrease', 'cashFlowImpact', 'savingsImpact', 'risk',
    ]) ||
    (value.stressTest.risk !== 'Moderate' && value.stressTest.risk !== 'High') ||
    !isStringArray(value.stressTest.assumptions) ||
    !Array.isArray(value.futures) ||
    !value.futures.every((item) => hasStringFields(item, [
      'name', 'monthlyEmi', 'savings', 'netWorth', 'cashFlow', 'debtRemaining', 'tradeoff',
    ])) ||
    !Array.isArray(value.pivots) ||
    !value.pivots.every((item) => hasStringFields(item, [
      'name', 'monthlyEmi', 'totalInterest', 'savings', 'netWorth', 'risk',
    ])) ||
    !isRecord(value.secondOpinion) ||
    !hasStringFields(value.secondOpinion, ['summary', 'resilience']) ||
    !isStringArray(value.secondOpinion.risks) ||
    !isStringArray(value.secondOpinion.assumptions) ||
    !isStringArray(value.secondOpinion.tradeoffs)
  ) return false
  return true
}

function parseAnalysis(value: unknown): DecisionAnalysis | null | undefined {
  if (value === null) return null
  return isDecisionAnalysis(value) ? value : undefined
}

export function parseChatHistory(value: unknown): ChatConversation[] | null {
  if (!Array.isArray(value)) return null
  const conversations: ChatConversation[] = []
  const ids = new Set<string>()

  for (const item of value) {
    if (
      !isRecord(item) ||
      typeof item.id !== 'string' ||
      !item.id ||
      ids.has(item.id) ||
      typeof item.title !== 'string' ||
      typeof item.updatedAt !== 'string'
    ) return null

    const messages = parseMessages(item.messages)
    const analysis = parseAnalysis(item.analysis)
    if (!messages || analysis === undefined) return null
    ids.add(item.id)
    conversations.push({ id: item.id, title: item.title, updatedAt: item.updatedAt, messages, analysis })
  }

  return conversations
}

export function formatConversationForSharing(conversation: ChatConversation): string {
  const transcript = conversation.messages
    .map(({ role, text }) => `${role === 'user' ? 'You' : 'FutureFund'}:\n${text}`)
    .join('\n\n')
  return `FutureFund conversation: ${conversation.title}\n${new Date(conversation.updatedAt).toLocaleString()}\n\n${transcript}`
}
