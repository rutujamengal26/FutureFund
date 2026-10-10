export type UserProfile = {
  name: string
  email: string
  phone: string
  occupation: string
  age: string
  income: string
  expenses: string
  assets: string
  savings: string
  emergency: string
  loans: string
  emi: string
  liabilities: string
  noLiabilities: boolean
  salaryGrowth: string
  duration: string
}

export const emptyUserProfile: UserProfile = {
  name: '',
  email: '',
  phone: '',
  occupation: '',
  age: '',
  income: '',
  expenses: '',
  assets: '',
  savings: '',
  emergency: '',
  loans: '',
  emi: '',
  liabilities: '',
  noLiabilities: false,
  salaryGrowth: '0',
  duration: '36',
}

export function parseUserProfile(value: unknown): UserProfile | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null

  const record = value as Record<string, unknown>
  const textFields: Exclude<keyof UserProfile, 'noLiabilities'>[] = [
    'name', 'email', 'phone', 'occupation', 'age', 'income', 'expenses',
    'assets', 'savings', 'emergency', 'loans', 'emi', 'liabilities',
    'salaryGrowth', 'duration',
  ]
  const profile = { ...emptyUserProfile }

  for (const field of textFields) {
    const fieldValue = record[field]
    if (fieldValue === undefined) continue
    if (typeof fieldValue !== 'string') return null
    profile[field] = fieldValue
  }

  if (record.noLiabilities !== undefined) {
    if (typeof record.noLiabilities !== 'boolean') return null
    profile.noLiabilities = record.noLiabilities
  }

  return profile
}
