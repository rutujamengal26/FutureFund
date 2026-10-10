'use client'

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { useAnalysis } from '@/components/analysis-context'
import type { UserProfile } from '@/lib/user-profile'

type ProfileDialogProps = {
  mode: 'view' | 'edit'
  onClose: () => void
  onEdit: () => void
}

type TextProfileField = Exclude<keyof UserProfile, 'noLiabilities'>

const fields: { name: TextProfileField; label: string; type?: string; suffix?: string }[] = [
  { name: 'name', label: 'Full name' },
  { name: 'email', label: 'Email address', type: 'email' },
  { name: 'phone', label: 'Phone number', type: 'tel' },
  { name: 'occupation', label: 'Occupation' },
  { name: 'age', label: 'Age', suffix: 'years' },
  { name: 'income', label: 'Monthly income', suffix: '₹' },
  { name: 'expenses', label: 'Monthly expenses', suffix: '₹' },
  { name: 'assets', label: 'Total assets', suffix: '₹' },
  { name: 'savings', label: 'Bank savings', suffix: '₹' },
  { name: 'emergency', label: 'Emergency fund', suffix: '₹' },
  { name: 'loans', label: 'Outstanding loans', suffix: '₹' },
  { name: 'emi', label: 'Monthly EMI', suffix: '₹' },
  { name: 'liabilities', label: 'Other liabilities', suffix: '₹' },
  { name: 'salaryGrowth', label: 'Expected annual salary growth', suffix: '%' },
]

function validateProfile(profile: UserProfile): Record<string, string> {
  const errors: Record<string, string> = {}
  if (!profile.name.trim()) errors.name = 'Full name is required.'
  if (profile.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)) {
    errors.email = 'Enter a valid email address.'
  }
  if (profile.phone && !/^\+?[\d\s()-]{7,20}$/.test(profile.phone)) {
    errors.phone = 'Enter a valid phone number.'
  }
  if (profile.age && (!/^\d+$/.test(profile.age) || Number(profile.age) < 1 || Number(profile.age) > 120)) {
    errors.age = 'Age must be a number between 1 and 120.'
  }
  for (const name of ['income', 'expenses', 'assets', 'savings', 'emergency', 'loans', 'emi', 'liabilities'] as const) {
    const value = profile[name]
    if (value && (!/^\d+(\.\d+)?$/.test(value) || Number(value) < 0)) {
      errors[name] = 'Enter a valid, non-negative amount.'
    }
  }
  if (profile.salaryGrowth && (!/^\d+(\.\d+)?$/.test(profile.salaryGrowth) || Number(profile.salaryGrowth) < 0)) {
    errors.salaryGrowth = 'Enter a valid, non-negative percentage.'
  }
  if (profile.duration && !['12', '24', '36'].includes(profile.duration)) {
    errors.duration = 'Choose a projection duration.'
  }
  return errors
}

function displayValue(profile: UserProfile, name: keyof UserProfile) {
  if (name === 'noLiabilities') {
    if (profile.noLiabilities) return 'Yes'
    return [profile.loans, profile.emi, profile.liabilities].some(Boolean) ? 'No' : 'Not provided'
  }
  if (name === 'duration') return profile.duration ? `${profile.duration} months` : 'Not provided'
  const value = profile[name]
  if (typeof value !== 'string' || !value.trim()) return 'Not provided'
  if (['income', 'expenses', 'assets', 'savings', 'emergency', 'loans', 'emi', 'liabilities'].includes(name)) return `₹${value}`
  if (name === 'age') return `${value} years`
  if (name === 'salaryGrowth') return `${value}%`
  return value
}

export function ProfileDialog({ mode, onClose, onEdit }: ProfileDialogProps) {
  const { userProfile, profileError, updateUserProfile } = useAnalysis()
  const [draft, setDraft] = useState(userProfile)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState(false)
  const dialogRef = useRef<HTMLElement>(null)
  const titleRef = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    titleRef.current?.focus()
    function handleEscape(event: globalThis.KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  function handleKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key !== 'Tab') return
    const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex="0"]',
    )
    if (!focusable?.length) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  function updateField(name: keyof UserProfile, value: string | boolean) {
    setDraft((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: '' }))
    setSaved(false)
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = validateProfile(draft)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return
    if (await updateUserProfile(draft)) setSaved(true)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#172a2a]/35 p-4 backdrop-blur-sm"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <section
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="profile-dialog-title"
        onKeyDown={handleKeyDown}
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[26px] border border-[#e4dbcf] bg-[#fffdf9] p-6 shadow-2xl sm:p-8"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#a17a35]">
              Your account
            </p>
            <h2
              ref={titleRef}
              id="profile-dialog-title"
              tabIndex={0}
              className="mt-2 text-2xl font-semibold tracking-tight text-[#263d39]"
            >
              {mode === 'view' ? 'View Profile' : 'Edit Profile'}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close profile"
            className="rounded-xl px-3 py-2 text-sm text-[#68756e] hover:bg-[#f7f3ec] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#a17a35]"
          >
            Close
          </button>
        </div>

        {profileError && (
          <p role="alert" className="mt-5 rounded-xl bg-[#f8eee4] p-3 text-sm text-[#8e4e3b]">
            {profileError}
          </p>
        )}

        {mode === 'view' ? (
          <>
            <dl className="mt-6 grid gap-3 sm:grid-cols-2">
              {fields.map(({ name, label }) => (
                <div key={name} className="rounded-2xl border border-[#eee6db] bg-white/70 p-4">
                  <dt className="text-xs font-semibold uppercase tracking-wide text-[#89928c]">{label}</dt>
                  <dd className="mt-2 break-words text-sm font-medium text-[#34443e]">
                    {displayValue(userProfile, name)}
                  </dd>
                </div>
              ))}
              <div className="rounded-2xl border border-[#eee6db] bg-white/70 p-4">
                <dt className="text-xs font-semibold uppercase tracking-wide text-[#89928c]">No existing liabilities</dt>
                <dd className="mt-2 text-sm font-medium text-[#34443e]">
                  {displayValue(userProfile, 'noLiabilities')}
                </dd>
              </div>
              <div className="rounded-2xl border border-[#eee6db] bg-white/70 p-4">
                <dt className="text-xs font-semibold uppercase tracking-wide text-[#89928c]">Projection duration</dt>
                <dd className="mt-2 text-sm font-medium text-[#34443e]">
                  {displayValue(userProfile, 'duration')}
                </dd>
              </div>
            </dl>
            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={onEdit}
                className="rounded-xl bg-[#17352f] px-5 py-3 text-sm font-semibold text-[#f5d282] transition hover:bg-[#285248] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#a17a35]"
              >
                Edit Profile
              </button>
            </div>
          </>
        ) : (
          <form onSubmit={save} noValidate>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {fields.map(({ name, label, type = 'text', suffix }) => (
                <div key={name}>
                  <label htmlFor={`profile-${name}`} className="mb-1.5 block text-sm font-medium text-[#48574f]">
                    {label}
                  </label>
                  <div className="flex items-center rounded-xl border border-[#ded8ce] bg-white focus-within:border-[#bd9b58] focus-within:ring-2 focus-within:ring-[#e9d9b4]/50">
                    <input
                      id={`profile-${name}`}
                      type={type}
                      inputMode={type === 'text' && suffix ? 'decimal' : undefined}
                      value={draft[name]}
                      onChange={(event) => updateField(name, event.target.value)}
                      aria-invalid={Boolean(errors[name])}
                      aria-describedby={errors[name] ? `profile-${name}-error` : undefined}
                      className="min-w-0 flex-1 rounded-xl bg-transparent px-3 py-2.5 text-sm text-[#34443e] outline-none"
                    />
                    {suffix && <span className="px-3 text-xs text-[#89928c]">{suffix}</span>}
                  </div>
                  {errors[name] && (
                    <p id={`profile-${name}-error`} role="alert" className="mt-1 text-xs text-[#a34b3b]">
                      {errors[name]}
                    </p>
                  )}
                </div>
              ))}
              <div>
                <label htmlFor="profile-duration" className="mb-1.5 block text-sm font-medium text-[#48574f]">
                  Projection duration
                </label>
                <select
                  id="profile-duration"
                  value={draft.duration}
                  onChange={(event) => updateField('duration', event.target.value)}
                  aria-invalid={Boolean(errors.duration)}
                  aria-describedby={errors.duration ? 'profile-duration-error' : undefined}
                  className="w-full rounded-xl border border-[#ded8ce] bg-white px-3 py-2.5 text-sm text-[#34443e] outline-none focus:border-[#bd9b58] focus:ring-2 focus:ring-[#e9d9b4]/50"
                >
                  <option value="">Not provided</option>
                  <option value="12">12 months</option>
                  <option value="24">24 months</option>
                  <option value="36">36 months</option>
                </select>
                {errors.duration && (
                  <p id="profile-duration-error" role="alert" className="mt-1 text-xs text-[#a34b3b]">
                    {errors.duration}
                  </p>
                )}
              </div>
              <label className="flex items-center gap-3 rounded-xl border border-[#e4dbcf] bg-white/70 p-3 text-sm text-[#48574f] sm:col-span-2">
                <input
                  type="checkbox"
                  checked={draft.noLiabilities}
                  onChange={(event) => updateField('noLiabilities', event.target.checked)}
                  className="h-4 w-4 accent-[#35624f]"
                />
                I have no existing loans or liabilities
              </label>
            </div>
            {saved && (
              <p role="status" className="mt-4 rounded-xl bg-[#e8f0e7] p-3 text-sm text-[#35624f]">
                Profile changes saved in this browser.
              </p>
            )}
            <div className="mt-6 flex flex-wrap justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-[#ded8ce] px-5 py-3 text-sm font-semibold text-[#64716b] transition hover:bg-[#f8f3eb] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#a17a35]"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="rounded-xl bg-[#17352f] px-5 py-3 text-sm font-semibold text-[#f5d282] transition hover:bg-[#285248] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#a17a35]"
              >
                Save Changes
              </button>
            </div>
          </form>
        )}
      </section>
    </div>
  )
}
