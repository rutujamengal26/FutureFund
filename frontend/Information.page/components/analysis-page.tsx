'use client'

import { EmptyAnalysis, AnalysisHeader, BarChart, MetricCard, PageFrame, SectionCard } from '@/components/finance-shell'
import { useAnalysis } from '@/components/analysis-context'

const config = { '/stress-test': { eyebrow: 'Stress Test & Risk', title: 'How resilient is your plan?', description: 'See how the current decision responds when income falls, an emergency arrives, or everyday costs rise.' }, '/multiple-futures': { eyebrow: 'Multiple Futures', title: 'Three paths. One clearer decision.', description: 'Compare the cost of acting now, waiting, or choosing a lower-risk alternative.' }, '/auto-pivot': { eyebrow: 'Auto-Pivot', title: 'Small changes, stronger outcomes.', description: 'Explore calculated alternatives that keep the original goal in view while reducing pressure.' }, '/ai-opinion': { eyebrow: 'AI Second Opinion', title: 'A calm read of the trade-offs.', description: 'Turn the numbers into a clear, professional explanation you can use alongside your own judgement.' } } as const

export function AnalysisPage({ kind }: { kind: keyof typeof config }) {
  const { analysis } = useAnalysis(); const copy = config[kind]
  if (!analysis) return <><AnalysisHeader {...copy} /><PageFrame><EmptyAnalysis title="Your analysis is waiting" detail="Submit a financial question in the chatbot first. Once your snapshot is ready, this section will show the relevant calculations." /></PageFrame></>
  return <><AnalysisHeader {...copy} /><PageFrame>{kind === '/stress-test' && <Stress analysis={analysis} />}{kind === '/multiple-futures' && <Futures analysis={analysis} />}{kind === '/auto-pivot' && <Pivots analysis={analysis} />}{kind === '/ai-opinion' && <Opinion analysis={analysis} />}</PageFrame></>
}
function Stress({ analysis }: { analysis: any }) {
  const result = analysis.stressTest;
  return (
    <div className="mx-auto w-full max-w-[1000px]">
      <SectionCard title="Stress scenarios">
        <div className="mt-5 grid gap-5 sm:grid-cols-3">
          <MetricCard label="Income" value={result.incomeDrop} detail="Downside case" tone="rose" />
          <MetricCard label="Emergency" value={result.emergencyExpense} detail="One-time cost" tone="gold" />
          <MetricCard label="Expenses" value={result.expenseIncrease} detail="Upside pressure" tone="sage" />
        </div>
        
        <div className="mt-8 grid gap-5 sm:grid-cols-1 md:grid-cols-3">
          <div className="flex flex-col justify-between rounded-2xl border border-[#e7dfd3] bg-[#fffaf5] p-5">
            <div>
              <h3 className="text-base font-semibold text-[#8e4e3b]">Income Drop</h3>
              <p className="mt-3 text-[16px] leading-6 text-[#7a6b60]">
                A {result.incomeDrop} loss in earnings tests your ongoing monthly commitments.
              </p>
            </div>
            <div className="mt-5 border-t border-[#f0e3d6] pt-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#a8533e]">Specific Risk</span>
              <p className="mt-1 text-[16px] font-medium leading-6 text-[#8e4e3b]">
                Severe cash flow strain; directly risks defaulting on your EMI if no emergency fund exists.
              </p>
            </div>
          </div>
          
          <div className="flex flex-col justify-between rounded-2xl border border-[#e7dfd3] bg-[#fffaf0] p-5">
            <div>
              <h3 className="text-base font-semibold text-[#a17a35]">Emergency Expense</h3>
              <p className="mt-3 text-[16px] leading-6 text-[#7a6b60]">
                A sudden {result.emergencyExpense} unplanned expense draws directly from liquid savings.
              </p>
            </div>
            <div className="mt-5 border-t border-[#f0e8d6] pt-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#a17a35]">Specific Risk</span>
              <p className="mt-1 text-[16px] font-medium leading-6 text-[#916b27]">
                Depletes your safety runway; forces you into more debt just to cover the original loan EMI.
              </p>
            </div>
          </div>

          <div className="flex flex-col justify-between rounded-2xl border border-[#e7dfd3] bg-[#f2f7f4] p-5">
            <div>
              <h3 className="text-base font-semibold text-[#35624f]">Expense Inflation</h3>
              <p className="mt-3 text-[16px] leading-6 text-[#7a6b60]">
                A {result.expenseIncrease} spike in basic costs steadily erodes your monthly surplus.
              </p>
            </div>
            <div className="mt-5 border-t border-[#d8e6de] pt-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#35624f]">Specific Risk</span>
              <p className="mt-1 text-[16px] font-medium leading-6 text-[#2d5443]">
                Long-term lifestyle squeeze; your fixed EMI becomes a heavier burden over the years.
              </p>
            </div>
          </div>
        </div>
      </SectionCard>
    </div>
  )
}
function Futures({ analysis }: { analysis: any }) { return <SectionCard title="Universe comparison"><div className="mt-5 grid gap-4 lg:grid-cols-3">{analysis.futures.map((item: any, index: number) => <article key={item.name} className={`rounded-2xl border p-5 ${index === 1 ? 'border-[#c8a75f] bg-[#fffaf0]' : 'border-[#e7dfd3] bg-white/60'}`}><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#a17a35]">{item.name}</p><p className="mt-5 text-2xl font-semibold text-[#263d39]">{item.monthlyEmi}</p><p className="mt-1 text-xs text-[#89928c]">monthly EMI</p><dl className="mt-6 space-y-3 text-sm">{[['Savings', item.savings], ['Net worth', item.netWorth], ['Cash flow', item.cashFlow], ['Debt remaining', item.debtRemaining]].map(([label, value]) => <div key={label} className="flex justify-between gap-3 border-b border-[#eee6db] pb-2"><dt className="text-[#87908c]">{label}</dt><dd className="font-semibold text-[#40524b]">{value}</dd></div>)}</dl><p className="mt-5 text-xs leading-5 text-[#78827d]">{item.tradeoff}</p></article>)}</div><div className="mt-7 rounded-2xl bg-[#f7f3ec] p-5"><p className="text-sm font-semibold text-[#34443e]">Savings across projection paths</p><BarChart values={[48, 82, 69]} labels={['Now', 'Wait', 'Alternative']} /></div></SectionCard> }
function Pivots({ analysis }: { analysis: any }) { return <SectionCard title="Calculated alternatives"><div className="mt-5 grid gap-4 lg:grid-cols-3">{analysis.pivots.map((item: any) => <article key={item.name} className="rounded-2xl border border-[#e7dfd3] bg-white/60 p-5"><p className="font-semibold text-[#34443e]">{item.name}</p><p className="mt-5 text-2xl font-semibold text-[#263d39]">{item.monthlyEmi}</p><p className="mt-1 text-xs text-[#89928c]">projected EMI</p><div className="mt-6 space-y-3 text-sm">{[['Total interest', item.totalInterest], ['Savings', item.savings], ['Net worth', item.netWorth], ['Risk', item.risk]].map(([label, value]) => <div key={label} className="flex justify-between border-b border-[#eee6db] pb-2"><span className="text-[#87908c]">{label}</span><strong className="text-[#40524b]">{value}</strong></div>)}</div></article>)}</div></SectionCard> }
function Opinion({ analysis }: { analysis: any }) { const opinion = analysis.secondOpinion; return <div className="grid gap-6 lg:grid-cols-[1.1fr_.9fr]"><SectionCard title="The second opinion"><p className="mt-5 text-lg leading-8 text-[#40524b]">{opinion.summary}</p><div className="mt-7 rounded-2xl bg-[#e8f0e7] p-5"><p className="text-sm font-semibold text-[#35624f]">What could make it more resilient</p><p className="mt-2 text-sm leading-6 text-[#577366]">{opinion.resilience}</p></div><div className="mt-7"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#89928c]">Trade-offs to keep in view</p><ul className="mt-4 space-y-3 text-sm leading-6 text-[#68756e]">{opinion.tradeoffs.map((item: string) => <li key={item}>• {item}</li>)}</ul></div></SectionCard><div className="space-y-6"><SectionCard title="Main financial risks"><ul className="mt-4 space-y-3 text-sm leading-6 text-[#68756e]">{opinion.risks.map((item: string) => <li key={item} className="rounded-xl bg-[#f8eee4] p-3">{item}</li>)}</ul></SectionCard><SectionCard title="Important assumptions"><ul className="mt-4 space-y-3 text-sm leading-6 text-[#68756e]">{opinion.assumptions.map((item: string) => <li key={item} className="border-b border-[#eee6db] pb-3 last:border-0">{item}</li>)}</ul></SectionCard></div></div> }
