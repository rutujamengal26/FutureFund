'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAnalysis } from '@/components/analysis-context'
import { emptyUserProfile, type UserProfile } from '@/lib/user-profile'
import { FinancePattern } from '@/components/finance-pattern'
import {
  ArrowLeft,
  ArrowRight,
  Banknote,
  Check,
  CircleHelp,
  Coins,
  Landmark,
  LockKeyhole,
  ShieldCheck,
  TrendingUp,
  UserRound,
  WalletCards,
} from 'lucide-react'

type Profile = UserProfile
const initialProfile: Profile = { ...emptyUserProfile }

const steps = ['About you', 'Assets & savings', 'Loans & liabilities', 'Future assumptions']

function money(value: string) {
  if (!value) return ''
  const digits = value.replace(/[^0-9]/g, '')
  return digits ? Number(digits).toLocaleString('en-IN') : ''
}

function Field({ label, name, value, onChange, placeholder, icon: Icon, hint, error, disabled = false, suffix }: any) {
  return (
    <div className="field-wrap">
      <label htmlFor={name}>{label}</label>
      <div className={`input-shell ${error ? 'input-error' : ''} ${disabled ? 'input-disabled' : ''}`}>
        <Icon size={18} strokeWidth={1.7} aria-hidden="true" />
        {suffix && <span className="input-prefix">{suffix}</span>}
        <input id={name} name={name} value={value} onChange={onChange} placeholder={placeholder} disabled={disabled} inputMode={suffix ? 'numeric' : undefined} aria-invalid={Boolean(error)} />
      </div>
      {hint && <p className="field-hint">{hint}</p>}
      {error && <p className="field-error" role="alert">{error}</p>}
    </div>
  )
}

export function FinancialOnboarding() {
  const router = useRouter()
  const { userProfile, profileLoaded, updateUserProfile } = useAnalysis()
  const [step, setStep] = useState(0)
  const [profile, setProfile] = useState<Profile>(initialProfile)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    if (profileLoaded) setProfile(userProfile)
  }, [profileLoaded, userProfile])

  const update = (name: keyof Profile, value: string | boolean) => {
    setProfile((current) => ({ ...current, [name]: value }))
    if (profileLoaded) updateUserProfile({ [name]: value })
    setErrors((current) => ({ ...current, [name]: '' }))
  }

  const setMoney = (name: keyof Profile) => (event: React.ChangeEvent<HTMLInputElement>) => update(name, event.target.value.replace(/[^0-9]/g, ''))
  const setText = (name: keyof Profile) => (event: React.ChangeEvent<HTMLInputElement>) => update(name, event.target.value)

  const validate = (currentStep: number) => {
    const next: Record<string, string> = {}
    const nonNegative = (key: keyof Profile, label: string) => {
      const value = profile[key] as string
      if (value && (!/^\d+(\.\d+)?$/.test(value) || Number(value) < 0)) next[key] = `${label} must be a valid, non-negative amount.`
    }
    if (currentStep === 0) {
      if (!profile.name.trim()) next.name = 'Please enter your full name.'
      if (!profile.age || !/^\d+$/.test(profile.age) || Number(profile.age) <= 0) next.age = 'Please enter a valid age.'
      if (!profile.income) next.income = 'Please enter your monthly income.'
      else nonNegative('income', 'Monthly income')
      if (!profile.expenses) next.expenses = 'Please enter your monthly expenses.'
      else nonNegative('expenses', 'Monthly expenses')
    }
    if (currentStep === 1) {
      if (!profile.assets) next.assets = 'Please enter your total assets value.'
      else nonNegative('assets', 'Total assets')
      if (!profile.savings) next.savings = 'Please enter your bank savings.'
      else nonNegative('savings', 'Bank savings')
      if (profile.emergency) nonNegative('emergency', 'Emergency fund')
    }
    if (currentStep === 2 && !profile.noLiabilities) ['loans', 'emi', 'liabilities'].forEach((key) => nonNegative(key as keyof Profile, key))
    if (currentStep === 3) {
      if (!profile.salaryGrowth || !/^\d+(\.\d+)?$/.test(profile.salaryGrowth) || Number(profile.salaryGrowth) < 0) next.salaryGrowth = 'Enter a valid percentage.'
      if (!['12', '24', '36'].includes(profile.duration)) next.duration = 'Choose a projection duration.'
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const nextStep = () => {
    if (!validate(step)) return
    if (step < 3) setStep((current) => current + 1)
    else {
      updateUserProfile(profile)
      router.push('/chatbot')
    }
  }

  const progress = useMemo(() => `${((step + 1) / steps.length) * 100}%`, [step])

  return (
    <main className="onboarding-shell finance-canvas">
      <FinancePattern />
      <header className="topbar">
        <div className="brand"><span className="brand-mark"><img src="/images/futurefunds-logo.jpeg" alt="" /></span><span>Future<span className="brand-accent">Funds</span></span></div>
        <div className="privacy-note"><LockKeyhole size={14} /> Your information stays private</div>
      </header>

      <section className="intro">
        <div className="eyebrow"><span className="eyebrow-line" /> FINANCIAL PROFILE <span className="eyebrow-line" /></div>
        <h1>Let&apos;s understand your <em>financial world.</em></h1>
        <p>A few details today will help us simulate the financial future of your decisions.</p>
      </section>

      <div className="progress-area" aria-label={`Step ${step + 1} of 4`}>
        <div className="progress-track"><div className="progress-fill" style={{ width: progress }} /></div>
        <div className="step-labels">{steps.map((label, index) => <div className={`step-label ${index === step ? 'active' : ''} ${index < step ? 'complete' : ''}`} key={label}><span className="step-dot">{index < step ? <Check size={12} /> : index + 1}</span><span>{label}</span></div>)}</div>
      </div>

      <section className="form-card" key={step}>
        <div className="card-heading">
          <span className="step-kicker">0{step + 1} / 04</span>
          <h2>{["First, let's get to know you.", 'What do you own today?', 'Any existing financial commitments?', "Now, let's look ahead."][step]}</h2>
          <p>{['Your financial journey starts with a few basics.', "Let's understand your current financial foundation.", "We'll account for your current obligations before simulating new decisions.", 'Every future projection depends on a few assumptions. You can change these later.'][step]}</p>
        </div>

        {step === 0 && <div className="fields-grid"><Field label="Full name" name="name" value={profile.name} onChange={setText('name')} placeholder="e.g. Ananya Sharma" icon={UserRound} error={errors.name} /><Field label="Age" name="age" value={profile.age} onChange={setText('age')} placeholder="e.g. 28" icon={UserRound} error={errors.age} /><Field label="Monthly income" name="income" value={money(profile.income)} onChange={setMoney('income')} placeholder="0" icon={Banknote} suffix="₹" error={errors.income} /><Field label="Monthly expenses" name="expenses" value={money(profile.expenses)} onChange={setMoney('expenses')} placeholder="0" icon={WalletCards} suffix="₹" error={errors.expenses} /></div>}
        {step === 1 && <><div className="helper-banner"><CircleHelp size={17} /><span><strong>What counts where?</strong> Assets include investments, property and gold. Bank savings are the cash balances in your accounts — keep them separate to avoid double-counting.</span></div><div className="fields-grid"><Field label="Total assets value" name="assets" value={money(profile.assets)} onChange={setMoney('assets')} placeholder="0" icon={Coins} suffix="₹" error={errors.assets} /><Field label="Savings in bank accounts" name="savings" value={money(profile.savings)} onChange={setMoney('savings')} placeholder="0" icon={Landmark} suffix="₹" error={errors.savings} /><Field label="Emergency fund" name="emergency" value={money(profile.emergency)} onChange={setMoney('emergency')} placeholder="Optional" icon={ShieldCheck} suffix="₹" hint="Money set aside specifically for unexpected expenses." error={errors.emergency} /></div></>}
        {step === 2 && <><label className="check-card"><input type="checkbox" checked={profile.noLiabilities} onChange={(event) => { const checked = event.target.checked; setProfile((current) => ({ ...current, noLiabilities: checked, loans: checked ? '0' : current.loans, emi: checked ? '0' : current.emi, liabilities: checked ? '0' : current.liabilities })) }} /><span className="custom-check"><Check size={14} /></span><span><strong>I have no existing loans or liabilities</strong><small>We&apos;ll set all commitment values to zero.</small></span></label><div className="fields-grid three"><Field label="Outstanding loans" name="loans" value={money(profile.loans)} onChange={setMoney('loans')} placeholder="0" icon={Landmark} suffix="₹" disabled={profile.noLiabilities} error={errors.loans} /><Field label="Total monthly EMI" name="emi" value={money(profile.emi)} onChange={setMoney('emi')} placeholder="0" icon={Banknote} suffix="₹" disabled={profile.noLiabilities} error={errors.emi} /><Field label="Other liabilities" name="liabilities" value={money(profile.liabilities)} onChange={setMoney('liabilities')} placeholder="0" icon={WalletCards} suffix="₹" disabled={profile.noLiabilities} error={errors.liabilities} /></div></>}
        {step === 3 && <div className="fields-grid future-grid"><Field label="Expected annual salary growth" name="salaryGrowth" value={profile.salaryGrowth} onChange={setText('salaryGrowth')} placeholder="0" icon={TrendingUp} suffix="%" hint="How your income may change over time." error={errors.salaryGrowth} /><div className="field-wrap"><label htmlFor="duration">Projection duration</label><div className={`input-shell ${errors.duration ? 'input-error' : ''}`}><TrendingUp size={18} strokeWidth={1.7} /><select id="duration" value={profile.duration} onChange={(event) => update('duration', event.target.value)} aria-invalid={Boolean(errors.duration)}><option value="12">12 months</option><option value="24">24 months</option><option value="36">36 months</option></select></div>{errors.duration && <p className="field-error" role="alert">{errors.duration}</p>}<p className="field-hint">How far into the future we simulate.</p></div></div>}

        <div className="form-actions">{step > 0 ? <button className="back-button" onClick={() => setStep((current) => current - 1)}><ArrowLeft size={16} /> Back</button> : <span />}{<button className="continue-button" onClick={nextStep}>{step === 3 ? 'Complete financial profile' : 'Continue'} <ArrowRight size={17} /></button>}</div>
      </section>
      <footer className="footer-note"><ShieldCheck size={15} /> Built to help you make clearer, more confident decisions.</footer>
    </main>
  )
}
