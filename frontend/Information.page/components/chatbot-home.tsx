import { DecisionChat } from '@/components/decision-chat'
import { FinanceShell } from '@/components/finance-shell'

export function ChatbotHome() {
  return (
    <FinanceShell>
      <DecisionChat />
    </FinanceShell>
  )
}
