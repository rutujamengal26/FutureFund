import type { Metadata } from 'next'
import { FinancialOnboarding } from '@/components/financial-onboarding'

export const metadata: Metadata = {
  title: 'Future Fund — Your Financial Profile',
  description: 'Share a few details to explore your financial future with Future Fund.',
}

export default function InformationPage() {
  return <FinancialOnboarding />
}
