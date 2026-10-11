'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Brain, ChevronDown, GitBranch, MessageCircle, RefreshCw, ShieldCheck, Sparkles, UserRound } from 'lucide-react'
import { FinancePattern } from '@/components/finance-pattern'
import { useState } from 'react'

const sections = [
  { href: '/decision', label: 'Chatbot', icon: MessageCircle },
  { href: '/stress-test', label: 'Stress Test & Risk', icon: ShieldCheck },
  { href: '/multiple-futures', label: 'Multiple Futures', icon: GitBranch },
  { href: '/auto-pivot', label: 'Auto-Pivot', icon: RefreshCw },
  { href: '/ai-opinion', label: 'AI Second Opinion', icon: Brain },
]

export function FinanceShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [profileOpen, setProfileOpen] = useState(false)
  return (
    <main className="finance-canvas min-h-screen overflow-x-hidden text-[#17212b]"><FinancePattern />
      <header className="sticky top-0 z-20 border-b border-[#e7dfd2]/80 bg-[#fbf6ee]/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1240px] items-center gap-6 px-4 py-3.5 lg:gap-8 lg:px-8">
          <Link href="/decision" className="flex shrink-0 items-center gap-3" aria-label="FutureFunds home">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#17352f] text-[#b4c99c] shadow-sm"><svg viewBox="0 0 64 64" role="img" aria-label="Future Fund mark" className="h-5 w-5"><circle cx="32" cy="32" r="30" fill="none" stroke="currentColor" strokeWidth="1.5" /><path d="M40 19H27a8 8 0 0 0-8 8v19m0-14h17" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" /><circle cx="45" cy="44" r="3" fill="currentColor" /></svg></span>
            <span className="hidden text-[17px] font-semibold tracking-[-0.02em] sm:inline">FutureFunds</span>
          </Link>
          <nav aria-label="Analysis sections" className="min-w-0 flex-1 overflow-x-auto py-0.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            <div className="flex min-w-max items-center gap-2">
              {sections.map(({ href, label, icon: Icon }) => {
                const active = pathname === href
                return <Link key={href} href={href} aria-current={active ? 'page' : undefined} className={`flex items-center gap-2 rounded-xl border px-3.5 py-2.5 text-[14px] font-semibold transition-all duration-200 ${active ? 'border-[#c8a256] bg-[#f7eaca] text-[#304d42] shadow-[0_3px_12px_rgba(163,123,44,0.12)]' : 'border-[#e5ddd1] bg-[#fffdf9]/75 text-[#66736d] hover:border-[#d3bd8b] hover:bg-white hover:text-[#34554b]'}`}><Icon size={16} strokeWidth={2} /><span>{label}</span></Link>
              })}
            </div>
          </nav>
          <div className="relative shrink-0">
            <button aria-label="Open profile menu" onClick={() => setProfileOpen((open) => !open)} className="flex items-center gap-2 rounded-full border border-[#ded8ce] bg-white/70 py-1.5 pl-1.5 pr-2.5 text-sm transition hover:bg-white">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#dfebdf] text-[#275447]"><UserRound size={15} /></span><ChevronDown size={14} className="text-[#63706b]" />
            </button>
            {profileOpen && <div className="absolute right-0 top-12 z-30 w-56 rounded-2xl border border-[#e3ddd3] bg-white p-2 shadow-xl"><p className="px-3 pb-2 pt-1 text-xs text-[#87908c]">Your account</p><button onClick={() => setProfileOpen(false)} className="block w-full rounded-xl px-3 py-2.5 text-left text-sm hover:bg-[#f8f3eb]">View Financial Profile</button><button onClick={() => setProfileOpen(false)} className="block w-full rounded-xl px-3 py-2.5 text-left text-sm hover:bg-[#f8f3eb]">Edit Financial Information</button></div>}
          </div>
        </div>
      </header>
      {children}
    </main>
  )
}

export { sections }

export function EmptyAnalysis({ title, detail }: { title: string; detail: string }) {
  return <div className="mx-auto mt-14 max-w-[560px] rounded-[28px] border border-[#e2d9ca] bg-white/80 p-8 text-center shadow-[0_14px_40px_rgba(79,61,34,0.06)]"><div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f5ead0] text-[#a57627]"><Sparkles size={20} /></div><h2 className="mt-5 text-xl font-semibold text-[#263d39]">{title}</h2><p className="mt-3 text-sm leading-6 text-[#78827d]">{detail}</p><Link href="/decision" className="mt-6 inline-flex rounded-xl bg-[#17352f] px-4 py-3 text-sm font-semibold text-[#f5d282] transition hover:bg-[#285248]">Ask Your First Question</Link></div>
}

export function MetricCard({ label, value, detail, tone = 'gold' }: { label: string; value: string; detail: string; tone?: 'gold' | 'sage' | 'rose' }) {
  const tones = { gold: 'bg-[#fbf3df] text-[#9b722e]', sage: 'bg-[#e4efe5] text-[#346452]', rose: 'bg-[#f8e7df] text-[#a34b3b]' }
  return <div className="rounded-2xl border border-[#e6ded3] bg-white/80 p-5"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#89928c]">{label}</p><p className="mt-3 text-2xl font-semibold tracking-tight text-[#263d39]">{value}</p><p className={`mt-2 inline-flex rounded-full px-2 py-1 text-[11px] font-semibold ${tones[tone]}`}>{detail}</p></div>
}

export function AnalysisHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <div className="mx-auto max-w-[1240px] px-5 pb-10 pt-14 lg:px-8"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#a17a35]">{eyebrow}</p><h1 className="mt-3 max-w-[760px] text-4xl font-semibold tracking-[-0.055em] text-[#172a2a] sm:text-[52px] sm:leading-[1.04]">{title}</h1><p className="mt-5 max-w-[600px] text-[15px] leading-7 text-[#6c7771]">{description}</p></div>
}

export function PageFrame({ children }: { children: React.ReactNode }) { return <div className="mx-auto max-w-[1240px] px-5 pb-20 lg:px-8">{children}</div> }

export function SectionCard({ title, children }: { title: string; children: React.ReactNode }) { return <section className="rounded-[26px] border border-[#e4dbcf] bg-white/75 p-6 shadow-[0_10px_32px_rgba(79,61,34,0.045)]"><h2 className="text-sm font-semibold text-[#34443e]">{title}</h2>{children}</section> }

export function BarChart({ values, labels }: { values: number[]; labels: string[] }) { return <div className="flex h-44 items-end gap-3 pt-5">{values.map((value, index) => <div key={labels[index]} className="flex flex-1 flex-col items-center gap-2"><div className="w-full rounded-t-xl bg-[#d7b76c] transition-all" style={{ height: `${Math.max(value, 10)}%` }} /><span className="text-[11px] text-[#87908c]">{labels[index]}</span></div>)}</div> }

export function LineChart({
  savings,
  expenses,
  loanAmount
}: {
  savings: number[] | number;
  expenses: number[] | number;
  loanAmount?: number | string;
}) {
  const savingsArr = Array.isArray(savings) ? savings : [savings, savings];
  const expensesArr = Array.isArray(expenses) ? expenses : [expenses, expenses];

  const parseLoan = (l: any) => {
    if (typeof l === 'number') return l;
    if (typeof l === 'string') {
      const cleaned = l.replace(/[^0-9.-]+/g, '');
      const num = parseFloat(cleaned);
      return isNaN(num) ? 0 : num;
    }
    return 0;
  };
  const parsedLoan = parseLoan(loanAmount);
  const rawMax = Math.max(...savingsArr, ...expensesArr, parsedLoan, 5000);

  const niceSteps = [
    5000, 10000, 20000, 25000, 50000,
    100000, 200000, 250000, 500000,
    1000000, 2000000, 2500000, 5000000, 10000000
  ];

  let chosenStep = niceSteps[niceSteps.length - 1];
  for (const step of niceSteps) {
    const intervals = Math.ceil(rawMax / step);
    if (intervals >= 3 && intervals <= 7) {
      chosenStep = step;
      break;
    }
  }
  if (!chosenStep || Math.ceil(rawMax / chosenStep) > 7) {
    for (const step of niceSteps) {
      if (Math.ceil(rawMax / step) <= 7) {
        chosenStep = step;
        break;
      }
    }
  }

  const numIntervals = Math.max(1, Math.ceil(rawMax / chosenStep));
  const maxTick = numIntervals * chosenStep;
  const activeTicks: number[] = [];
  for (let i = 0; i <= numIntervals; i++) {
    activeTicks.push(i * chosenStep);
  }

  const getYPercent = (val: number) => {
    if (val <= 0) return 0;
    if (val >= maxTick) return 100;
    return (val / maxTick) * 100;
  };

  const monthsCount = Math.max(savingsArr.length - 1, 1);
  const numYears = Math.floor(monthsCount / 12);

  const pts = (arr: number[]) =>
    arr.map((v, i) => `${(i / monthsCount) * 100},${100 - getYPercent(v)}`).join(' ');

  const formatYLabel = (val: number) => {
    if (val === 0) return '0';
    if (val >= 10000000) return `${(val / 10000000).toFixed(val % 10000000 === 0 ? 0 : 1)}Cr`;
    if (val >= 100000) return `${(val / 100000).toFixed(val % 100000 === 0 ? 0 : 1)}L`;
    if (val >= 1000) return `${(val / 1000).toFixed(0)}k`;
    return val.toString();
  };

  return (
    <div className="relative mt-2 h-[350px] sm:h-[450px] w-full pb-14 pl-14 pr-4 pt-4 font-sans text-[11px] text-[#87908c]">
      {/* Y Axis Labels */}
      <div className="absolute bottom-14 left-0 top-4 w-12">
        {activeTicks.map((tick, i) => (
          <span
            key={i}
            className="absolute right-2 -translate-y-1/2 text-right text-[12px] font-medium text-[#6c7771]"
            style={{ bottom: `${(tick / maxTick) * 100}%` }}
          >
            {formatYLabel(tick)}
          </span>
        ))}
      </div>

      {/* Chart Canvas */}
      <div className="relative h-full w-full border-b-[1.5px] border-l-[1.5px] border-[#34443e]">
        {/* Horizontal Grid Lines */}
        {activeTicks.slice(1).map((tick, i) => (
          <div
            key={i}
            className="absolute w-full border-t border-[#e6dfd5]"
            style={{ bottom: `${(tick / maxTick) * 100}%` }}
          />
        ))}

        {/* Lines */}
        <svg className="absolute inset-0 h-full w-full overflow-visible" preserveAspectRatio="none" viewBox="0 0 100 100">
          <polyline fill="none" stroke="#d7b76c" strokeWidth="2.5" points={pts(savingsArr)} vectorEffect="non-scaling-stroke" />
          <polyline fill="none" stroke="#a34b3b" strokeWidth="2.5" points={pts(expensesArr)} vectorEffect="non-scaling-stroke" />
        </svg>

        {/* Start Data Dots */}
        <div
          className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-[#d7b76c] shadow-sm pointer-events-none"
          style={{ left: '0%', bottom: `${getYPercent(savingsArr[0])}%` }}
        />
        <div
          className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-[#a34b3b] shadow-sm pointer-events-none"
          style={{ left: '0%', bottom: `${getYPercent(expensesArr[0])}%` }}
        />

        {/* End Data Dots */}
        <div
          className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-[#d7b76c] shadow-sm pointer-events-none"
          style={{ left: '100%', bottom: `${getYPercent(savingsArr[savingsArr.length - 1])}%` }}
        />
        <div
          className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-[#a34b3b] shadow-sm pointer-events-none"
          style={{ left: '100%', bottom: `${getYPercent(expensesArr[expensesArr.length - 1])}%` }}
        />
      </div>

      {/* X Axis Labels */}
      <div className="absolute bottom-8 left-14 right-4 h-5">
        {Array.from({ length: numYears + 1 }).map((_, i) => (
          <div
            key={i}
            className="absolute top-0 flex -translate-x-1/2 flex-col items-center"
            style={{ left: `${(i / Math.max(1, numYears)) * 100}%` }}
          >
            <div className="h-1.5 w-[1.5px] bg-[#34443e]" />
            <span className="mt-1 font-medium text-[#6c7771]">{i === 0 ? '0' : `${i} year`}</span>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="absolute bottom-0 left-0 flex w-full justify-center gap-6 text-[12px] font-medium text-[#6c7771]">
        <span className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded-full bg-[#d7b76c]"></div> Saving
        </span>
        <span className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded-full bg-[#a34b3b]"></div> Expenses
        </span>
      </div>
    </div>
  );
}
