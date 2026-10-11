'use client'

import { useState } from 'react'
import { EmptyAnalysis, AnalysisHeader, BarChart, MetricCard, PageFrame, SectionCard, LineChart } from '@/components/finance-shell'
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
function Futures({ analysis }: { analysis: any }) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const futures = analysis?.futures || []
  const selectedItem = futures[selectedIndex] || futures[0]

  const getUniverseGraph = (universe: any, idx: number) => {
    if (universe?.graph && Array.isArray(universe.graph.savings) && universe.graph.savings.length > 0) {
      return universe.graph
    }
    const baseExpenses = analysis?.graph?.expenses
    const baseSavings = analysis?.graph?.savings
    const parseNum = (val: any) => {
      if (typeof val === 'number') return val
      if (typeof val === 'string') {
        const cleaned = val.replace(/[^0-9.-]+/g, '')
        const parsed = parseFloat(cleaned)
        return isNaN(parsed) ? 0 : parsed
      }
      return 0
    }
    const emi = parseNum(universe?.monthlyEmi)
    const targetEndSavings = parseNum(universe?.savings)

    if (baseExpenses && baseExpenses.length > 1) {
      const horizon = baseExpenses.length - 1
      const startSavings = baseSavings && baseSavings.length > 0 ? baseSavings[0] : (targetEndSavings > 0 ? targetEndSavings * 0.5 : 500000)
      const isWait = idx === 1 || universe?.name?.toLowerCase().includes('wait')
      const delay = isWait ? 6 : 0
      let currSavings = startSavings
      const savingsArr = [currSavings]
      const totalExpensesSum = baseExpenses.reduce((a: number, b: number) => a + b, 0)
      const monthsWithEmi = Math.max(1, horizon - delay)
      const totalEmiSum = emi * monthsWithEmi
      const requiredIncomeSum = (targetEndSavings - startSavings) + totalExpensesSum + totalEmiSum
      const monthlyIncome = Math.max(requiredIncomeSum / horizon, baseExpenses[0] + emi)

      for (let m = 1; m <= horizon; m++) {
        const exp = baseExpenses[m] ?? baseExpenses[baseExpenses.length - 1]
        const monthlyEmiVal = m > delay ? emi : 0
        currSavings += (monthlyIncome - exp - monthlyEmiVal)
        savingsArr.push(Math.round(currSavings))
      }
      return { savings: savingsArr, expenses: baseExpenses }
    }

    const months = 36
    const startExp = 45000
    const startSav = targetEndSavings > 0 ? Math.round(targetEndSavings * 0.6) : 300000
    const expArr = [startExp]
    const savArr = [startSav]
    let cExp = startExp
    let cSav = startSav
    const isWait = idx === 1 || universe?.name?.toLowerCase().includes('wait')
    const delay = isWait ? 6 : 0
    const estIncome = 100000
    for (let m = 1; m <= months; m++) {
      cExp = Math.round(cExp * Math.pow(1.05, 1 / 12))
      const mEmi = m > delay ? emi : 0
      cSav += (estIncome - cExp - mEmi)
      expArr.push(cExp)
      savArr.push(Math.round(cSav))
    }
    return { savings: savArr, expenses: expArr }
  }

  const activeGraph = selectedItem ? getUniverseGraph(selectedItem, selectedIndex) : null

  return (
    <SectionCard title="Universe comparison">
      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        {futures.map((item: any, index: number) => {
          const isSelected = selectedIndex === index
          return (
            <article
              key={item.name}
              onClick={() => setSelectedIndex(index)}
              className={`group cursor-pointer rounded-2xl border p-5 transition-all duration-200 ${
                isSelected
                  ? 'border-2 border-[#b89345] bg-[#fffaf0] shadow-md ring-2 ring-[#b89345]/20'
                  : 'border-[#e7dfd3] bg-white/60 hover:border-[#c8a75f] hover:bg-[#fffdf8]'
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#a17a35]">
                  {item.name}
                </p>
                {isSelected ? (
                  <span className="rounded-full bg-[#faecd0] px-2.5 py-0.5 text-[11px] font-semibold text-[#8a5d1b]">
                    Active View
                  </span>
                ) : (
                  <span className="text-[11px] font-medium text-[#89928c] opacity-0 transition group-hover:opacity-100">
                    Click to view graph
                  </span>
                )}
              </div>

              <p className="mt-4 text-2xl font-semibold text-[#263d39]">{item.monthlyEmi}</p>
              <p className="mt-1 text-xs text-[#89928c]">monthly EMI</p>

              <dl className="mt-6 space-y-2.5">
                {[
                  ['Savings', item.savings],
                  ['Net worth', item.netWorth],
                  ['Cash flow', item.cashFlow],
                  ['Debt remaining', item.debtRemaining],
                ].map(([label, value]) => (
                  <div key={label} className="flex justify-between items-center gap-3 border-b border-[#eee6db] pb-2 last:border-b-0">
                    <dt className="text-[16px] font-semibold text-[#1e342f]">{label}</dt>
                    <dd className="text-[16px] font-semibold text-[#1e342f]">{value}</dd>
                  </div>
                ))}
              </dl>
              {item.tradeoff && <p className="mt-5 text-xs leading-5 text-[#78827d]">{item.tradeoff}</p>}
            </article>
          )
        })}
      </div>

      <div className="mt-7 rounded-2xl border border-[#e6dfd5] bg-[#f7f3ec] p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#e5ded4] pb-3 mb-4">
          <div>
            <p className="text-base font-semibold text-[#34443e]">
              Savings & Expenses Projection — {selectedItem?.name}
            </p>
            <p className="text-xs text-[#78827d] mt-0.5">
              Monthly evolution of projected savings vs living expenses under {selectedItem?.name} (5% annual inflation)
            </p>
          </div>
          {selectedItem && (
            <span className="self-start sm:self-auto rounded-full border border-[#d8cbb8] bg-white px-3 py-1 text-xs font-semibold text-[#7d561a]">
              Scheduled EMI: {selectedItem.monthlyEmi}
            </span>
          )}
        </div>
        {activeGraph ? (
          <LineChart
            savings={activeGraph.savings}
            expenses={activeGraph.expenses}
            loanAmount={selectedItem?.debtRemaining || selectedItem?.monthlyEmi}
          />
        ) : (
          <div className="py-12 text-center text-sm text-[#87908c]">
            Select a universe above to see its projected savings timeline.
          </div>
        )}
      </div>
    </SectionCard>
  )
}
function Pivots({ analysis }: { analysis: any }) { return <SectionCard title="Calculated alternatives"><div className="mt-5 grid gap-4 lg:grid-cols-3">{analysis.pivots.map((item: any) => <article key={item.name} className="rounded-2xl border border-[#e7dfd3] bg-white/60 p-5"><p className="font-semibold text-[#34443e]">{item.name}</p><p className="mt-5 text-2xl font-semibold text-[#263d39]">{item.monthlyEmi}</p><p className="mt-1 text-xs text-[#89928c]">projected EMI</p><div className="mt-6 space-y-3 text-sm">{[['Total interest', item.totalInterest], ['Savings', item.savings], ['Net worth', item.netWorth], ['Risk', item.risk]].map(([label, value]) => <div key={label} className="flex justify-between border-b border-[#eee6db] pb-2"><span className="text-[#87908c]">{label}</span><strong className="text-[#40524b]">{value}</strong></div>)}</div></article>)}</div></SectionCard> }
function Opinion({ analysis }: { analysis: any }) { const opinion = analysis.secondOpinion; return <div className="grid gap-6 lg:grid-cols-[1.1fr_.9fr]"><SectionCard title="The second opinion"><p className="mt-5 text-lg leading-8 text-[#40524b]">{opinion.summary}</p><div className="mt-7 rounded-2xl bg-[#e8f0e7] p-5"><p className="text-sm font-semibold text-[#35624f]">What could make it more resilient</p><p className="mt-2 text-sm leading-6 text-[#577366]">{opinion.resilience}</p></div><div className="mt-7"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#89928c]">Trade-offs to keep in view</p><ul className="mt-4 space-y-3 text-sm leading-6 text-[#68756e]">{opinion.tradeoffs.map((item: string) => <li key={item}>• {item}</li>)}</ul></div></SectionCard><div className="space-y-6"><SectionCard title="Main financial risks"><ul className="mt-4 space-y-3 text-sm leading-6 text-[#68756e]">{opinion.risks.map((item: string) => <li key={item} className="rounded-xl bg-[#f8eee4] p-3">{item}</li>)}</ul></SectionCard><SectionCard title="Important assumptions"><ul className="mt-4 space-y-3 text-sm leading-6 text-[#68756e]">{opinion.assumptions.map((item: string) => <li key={item} className="border-b border-[#eee6db] pb-3 last:border-0">{item}</li>)}</ul></SectionCard></div></div> }
