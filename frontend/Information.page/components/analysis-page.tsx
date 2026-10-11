'use client'

import { useState, useMemo } from 'react'
import { EmptyAnalysis, AnalysisHeader, BarChart, MetricCard, PageFrame, SectionCard, LineChart } from '@/components/finance-shell'
import { useAnalysis } from '@/components/analysis-context'
import { generateThreeAutoPivots, generateComprehensiveSecondOpinion, fetchLiveAISecondOpinion } from '@/services/analysisService'
import { ArrowRight, CheckCircle2, AlertTriangle, ShieldCheck, Sparkles, RotateCw, Award, Scale } from 'lucide-react'

const config = { '/stress-test': { eyebrow: 'Stress Test & Risk', title: 'How resilient is your plan?', description: 'See how the current decision responds when income falls, an emergency arrives, or everyday costs rise.' }, '/multiple-futures': { eyebrow: 'Multiple Futures', title: 'Three paths. One clearer decision.', description: 'Compare the cost of acting now, waiting, or choosing a lower-risk alternative.' }, '/auto-pivot': { eyebrow: 'Auto-Pivot', title: 'Small changes, stronger outcomes.', description: 'Explore calculated alternatives that keep the original goal in view while reducing pressure.' }, '/ai-opinion': { eyebrow: 'AI Second Opinion', title: 'A calm read of the trade-offs.', description: 'Turn the numbers into a clear, professional explanation you can use alongside your own judgement.' } } as const

export function AnalysisPage({ kind }: { kind: keyof typeof config }) {
  const { analysis, submit, loading } = useAnalysis(); const copy = config[kind]
  if (!analysis) {
    return (
      <>
        <AnalysisHeader {...copy} />
        <PageFrame>
          <EmptyAnalysis
            title="Your analysis is waiting"
            detail="Submit a financial question in the chatbot first, or explore how Auto-Pivot optimizes outcomes by loading a sample ₹5L loan analysis."
            samplePrompt="Explore Sample ₹5L Loan Analysis"
            onRunSample={() => void submit("Can I afford a ₹5 lakh personal loan over 3 years?")}
            loading={loading}
          />
        </PageFrame>
      </>
    )
  }
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
function Pivots({ analysis }: { analysis: any }) {
  const pivots = useMemo(() => {
    if (
      Array.isArray(analysis?.pivots) &&
      analysis.pivots.length === 3 &&
      analysis.pivots[0]?.id === 'smaller_loan' &&
      analysis.pivots[0]?.whyChooseThis
    ) {
      return analysis.pivots
    }
    return generateThreeAutoPivots(analysis)
  }, [analysis])

  return (
    <div className="mx-auto w-full max-w-[1140px] space-y-8">
      {/* Overview Banner */}
      <div className="relative overflow-hidden rounded-[24px] border border-[#e2d5bf] bg-gradient-to-r from-[#fbf6ec] via-[#f8eedb] to-[#faedd2] p-6 sm:p-7 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-1.5 rounded-full bg-[#ecdcba] px-3.5 py-1 text-sm font-semibold text-[#7c5517]">
              <Sparkles size={14} />
              <span>3 Strategic Alternatives</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-[#223933]">
              Auto-Pivot Conditions for &ldquo;{analysis.question || 'Your Decision'}&rdquo;
            </h2>
            <p className="max-w-[720px] text-base leading-relaxed text-[#5a6863]">
              Compare the 3 calculated conditions below: <strong>Smaller loan</strong>, <strong>Longer tenure</strong>, and <strong>Wait before purchasing</strong>. Each box details the exact financial reasoning and risks.
            </p>
          </div>
          <div className="rounded-2xl border border-[#ded1ba] bg-white/80 px-5 py-3.5 text-center shadow-xs shrink-0">
            <span className="block text-xs font-semibold uppercase tracking-wider text-[#91795a]">Strategies</span>
            <span className="text-2xl font-bold text-[#1f3832]">3 Conditions</span>
          </div>
        </div>
      </div>

      {/* The EXACT 3 Condition Boxes */}
      <div className="grid gap-6 md:grid-cols-3">
        {pivots.map((item: any, idx: number) => {
          return (
            <div
              key={item.id || `pivot-condition-${idx}`}
              className={`relative flex flex-col justify-between rounded-[26px] border p-6 transition-all duration-200 shadow-sm ${
                item.isRecommended
                  ? 'border-2 border-[#b89345] bg-[#fffcf5] ring-2 ring-[#b89345]/15'
                  : 'border-[#e4dcce] bg-white/90 hover:border-[#c5a359]'
              }`}
            >
              <div>
                {/* Badge & Risk Rating */}
                <div className="flex items-center justify-between gap-2">
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1 text-sm font-bold ${
                      item.isRecommended
                        ? 'bg-[#faecd0] text-[#8a5d1b]'
                        : 'bg-[#e7f1eb] text-[#245846]'
                    }`}
                  >
                    {item.isRecommended ? <Sparkles size={14} /> : <CheckCircle2 size={14} />}
                    {item.badge || item.name}
                  </span>
                  <span
                    className={`rounded-full px-3 py-1 text-sm font-bold ${
                      item.riskTone === 'gold'
                        ? 'bg-[#fbf3df] text-[#9b722e]'
                        : 'bg-[#e4efe5] text-[#295e4b]'
                    }`}
                  >
                    {item.risk}
                  </span>
                </div>

                {/* Title */}
                <h3 className="mt-4 text-2xl font-extrabold tracking-tight text-[#1c3933]">
                  {item.name}
                </h3>
                <p className="mt-1.5 text-base font-semibold leading-normal text-[#44554e]">
                  {item.subtitle}
                </p>

                {/* Projected Monthly EMI Callout */}
                <div className="mt-5 rounded-2xl border border-[#ece4d6] bg-white p-4 shadow-2xs">
                  <span className="text-sm font-bold uppercase tracking-wider text-[#697a72]">
                    Projected Monthly EMI
                  </span>
                  <div className="mt-1.5 flex items-baseline justify-between">
                    <span className="text-3xl font-extrabold tracking-tight text-[#18362f]">
                      {item.monthlyEmi}
                    </span>
                    <span className="text-sm font-bold text-[#55675f]">Per Month</span>
                  </div>
                </div>

                {/* Financial Summary */}
                <div className="mt-4 space-y-3 rounded-xl border border-[#ede5d8] bg-[#fdfbf7] p-4 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-[#4e5f58]">Total Financing Interest</span>
                    <span className="font-bold text-[#203a32] text-sm sm:text-base">{item.totalInterest}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-[#4e5f58]">Ending Cash Reserves</span>
                    <span className="font-bold text-[#203a32] text-sm sm:text-base">{item.savings}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-[#4e5f58]">Ending Net Worth</span>
                    <span className="font-bold text-[#203a32] text-sm sm:text-base">{item.netWorth}</span>
                  </div>
                </div>
              </div>

              {/* Key Changes vs Baseline */}
              {item.keyChanges && item.keyChanges.length > 0 && (
                <div className="mt-5 border-t border-[#eee5d8] pt-3.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#8b6e36]">
                    Key Changes:
                  </span>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {item.keyChanges.map((ch: any, cIdx: number) => (
                      <span
                        key={cIdx}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[#e5d9c2] bg-white px-3 py-1.5 text-xs sm:text-sm font-bold text-[#26443c]"
                      >
                        {ch.metric}: <span className="line-through text-[#8e9893] text-xs font-medium">{ch.from}</span> → <span className="text-[#a17a35] font-extrabold">{ch.to}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function Opinion({ analysis }: { analysis: any }) {
  const [liveLoading, setLiveLoading] = useState(false)
  const [liveOpinion, setLiveOpinion] = useState<any>(null)
  const [liveError, setLiveError] = useState<string | null>(null)

  const baseOpinion = useMemo(() => {
    if (
      analysis?.secondOpinion?.bestPlan &&
      analysis.secondOpinion.summary &&
      analysis.secondOpinion.summary !== 'Second opinion not available.'
    ) {
      return analysis.secondOpinion
    }
    return generateComprehensiveSecondOpinion(analysis)
  }, [analysis])

  const opinion = liveOpinion || baseOpinion

  const handleLiveRefresh = async () => {
    setLiveLoading(true)
    setLiveError(null)
    try {
      const res = await fetchLiveAISecondOpinion(analysis)
      if (res && res.bestPlan) {
        setLiveOpinion(res)
      }
    } catch (err: any) {
      setLiveError(err?.message || 'Could not reach AI service.')
    } finally {
      setLiveLoading(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1140px] space-y-8">
      {/* AI Recommendation Champion Banner */}
      <div className="relative overflow-hidden rounded-[24px] border border-[#2b4c40] bg-gradient-to-br from-[#1b362e] via-[#142d25] to-[#0f221c] p-6 sm:p-8 text-white shadow-md">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3.5 max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#e2c17c]/40 bg-[#e2c17c]/15 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-[#fae9c3]">
              <Sparkles className="h-3.5 w-3.5 text-[#e2c17c]" />
              AI Synthesized Second Opinion • Live API Key
            </div>

            <div className="space-y-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#a3b8af]">
                Top Recommended Choice Across All Plans:
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex flex-wrap items-center gap-2.5">
                <span>{opinion.bestPlan || 'Smaller Loan'}</span>
                <span className="inline-flex items-center rounded-lg border border-[#e2c17c]/30 bg-[#e2c17c]/20 px-2.5 py-0.5 text-xs font-bold text-[#f7e4be]">
                  {opinion.bestCategory || 'Auto-Pivot Strategy'}
                </span>
              </h2>
            </div>

            <p className="text-sm sm:text-base leading-relaxed text-[#d7e4de] pt-1">
              {opinion.whyBestPlan || opinion.summary}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row md:flex-col items-start md:items-end gap-2.5 shrink-0">
            <button
              onClick={handleLiveRefresh}
              disabled={liveLoading}
              className="inline-flex items-center gap-2 rounded-xl border border-[#e2c17c]/40 bg-[#e2c17c]/20 hover:bg-[#e2c17c]/30 px-4 py-2.5 text-xs sm:text-sm font-bold text-[#fae9c3] transition-all shadow-xs disabled:opacity-60 cursor-pointer"
            >
              <RotateCw className={`h-4 w-4 ${liveLoading ? 'animate-spin text-[#fae9c3]' : 'text-[#e2c17c]'}`} />
              {liveLoading ? 'Generating via Groq API...' : 'Live AI Re-Evaluate'}
            </button>
            <span className="text-[11px] text-[#93a79f]">
              Powered by Groq High-Speed API Key
            </span>
            {liveError && (
              <span className="text-[11px] text-[#fca5a5] max-w-[200px] text-right">
                {liveError}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 6 Plans Side-by-Side Comparison Matrix */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2 border-b border-[#ebdcca] pb-3">
          <div>
            <h3 className="text-xl font-bold tracking-tight text-[#1a342d]">
              All 6 Proposed Plans Evaluated by AI
            </h3>
            <p className="text-xs sm:text-sm text-[#667770] mt-0.5">
              Comparing 3 Multiple Futures paths & 3 Auto-Pivot alternatives to determine cash resilience.
            </p>
          </div>
          <span className="text-xs font-bold text-[#8d6c34] uppercase tracking-wider bg-[#f8eedb] px-3 py-1 rounded-full border border-[#e2d5bf]">
            6 Plans Assessed
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {Array.isArray(opinion.allPlansComparison) && opinion.allPlansComparison.length > 0 ? (
            opinion.allPlansComparison.map((plan: any, idx: number) => {
              const isTopPick = plan.verdict === 'Top Pick'
              const isHighRisk = plan.verdict === 'High Risk'

              let verdictClass = 'border-[#badfc7] bg-[#e3f4e9] text-[#1c643b]'
              if (isTopPick) verdictClass = 'border-[#2d734c] bg-[#1c643b] text-white shadow-2xs'
              else if (isHighRisk) verdictClass = 'border-[#fecaca] bg-[#fef2f2] text-[#991b1b]'
              else verdictClass = 'border-[#fed7aa] bg-[#fff7ed] text-[#c2410c]'

              return (
                <div
                  key={idx}
                  className={`flex flex-col justify-between rounded-2xl border p-5 transition-all ${
                    isTopPick
                      ? 'border-[#c49a46] bg-[#fdf9f0] shadow-sm ring-1 ring-[#c49a46]/40'
                      : 'border-[#e8ded0] bg-white hover:border-[#dbcbb4]'
                  }`}
                >
                  <div className="space-y-3.5">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-base font-bold text-[#1a342d]">
                            {plan.planName}
                          </h4>
                          {isTopPick && (
                            <Award className="h-4 w-4 text-[#c49a46]" />
                          )}
                        </div>
                        <span className="text-xs font-medium text-[#7a8882]">
                          {plan.category}
                        </span>
                      </div>
                      <span className={`rounded-full border px-2.5 py-0.5 text-xs font-bold shrink-0 ${verdictClass}`}>
                        {plan.verdict}
                      </span>
                    </div>

                    <div className="rounded-xl border border-[#eee4d6] bg-[#fcfaf6] p-3 text-xs sm:text-sm space-y-1.5">
                      <span className="font-bold text-[#354841] block">
                        Trade-Off:
                      </span>
                      <p className="text-[#556760] leading-relaxed">
                        {plan.keyTradeOff}
                      </p>
                    </div>

                    <div className="text-xs sm:text-sm text-[#4d5e57]">
                      <span className="font-bold text-[#2d4039]">Best For: </span>
                      <span>{plan.suitability}</span>
                    </div>
                  </div>
                </div>
              )
            })
          ) : (
            <div className="col-span-full py-8 text-center text-sm text-[#73827b]">
              Loading all plans evaluation...
            </div>
          )}
        </div>
      </div>

      {/* Resilience, Trade-offs, Risks, and Assumptions Deep-Dive */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Column: Resilience & Trade-offs */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-[#cbe1d3] bg-[#f0f7f3] p-6 shadow-xs">
            <div className="flex items-center gap-2.5 text-[#1b5e39] font-bold text-base">
              <ShieldCheck className="h-5 w-5 text-[#247c4b]" />
              <h4>What Could Make Your Plan More Resilient</h4>
            </div>
            <p className="mt-3 text-sm sm:text-base leading-relaxed text-[#2f4d3d]">
              {opinion.resilience || 'Maintain a liquid buffer covering at least 6 months of expenses before initiating major loan commitments.'}
            </p>
          </div>

          <div className="rounded-2xl border border-[#ebdcca] bg-[#fdfbf7] p-6 shadow-xs">
            <div className="flex items-center gap-2.5 text-[#865d1d] font-bold text-base">
              <Scale className="h-5 w-5 text-[#b08b3e]" />
              <h4>Trade-Offs to Keep in View</h4>
            </div>
            <ul className="mt-4 space-y-3 text-sm sm:text-base text-[#4d5f57]">
              {opinion.tradeoffs && opinion.tradeoffs.length > 0 ? (
                opinion.tradeoffs.map((item: string, i: number) => (
                  <li key={i} className="flex items-start gap-2.5">
                    <span className="mt-1.5 h-2 w-2 rounded-full bg-[#c49a46] shrink-0" />
                    <span>{item}</span>
                  </li>
                ))
              ) : (
                <li className="text-xs text-[#7d8b84]">• Smaller loans reduce asset scale while preserving liquid safety.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Right Column: Risks & Assumptions */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-[#f2ded1] bg-[#fdf6f0] p-6 shadow-xs">
            <div className="flex items-center gap-2.5 text-[#9c422b] font-bold text-base">
              <AlertTriangle className="h-5 w-5 text-[#c25336]" />
              <h4>Main Financial Risks</h4>
            </div>
            <ul className="mt-4 space-y-3 text-sm sm:text-base text-[#573932]">
              {opinion.risks && opinion.risks.length > 0 ? (
                opinion.risks.map((item: string, i: number) => (
                  <li key={i} className="rounded-xl border border-[#f5dfd3] bg-white/70 p-3 leading-relaxed">
                    {item}
                  </li>
                ))
              ) : (
                <li className="text-xs text-[#7d8b84]">• High monthly EMI deductions without buffer reserves increase stress.</li>
              )}
            </ul>
          </div>

          <div className="rounded-2xl border border-[#ebdcca] bg-[#fcfaf6] p-6 shadow-xs">
            <div className="flex items-center gap-2.5 text-[#3b4c45] font-bold text-base">
              <CheckCircle2 className="h-5 w-5 text-[#4e6a5e]" />
              <h4>Important Assumptions</h4>
            </div>
            <ul className="mt-4 space-y-3 text-sm sm:text-base text-[#586a63]">
              {opinion.assumptions && opinion.assumptions.length > 0 ? (
                opinion.assumptions.map((item: string, i: number) => (
                  <li key={i} className="border-b border-[#eee4d6] pb-2.5 last:border-0 last:pb-0">
                    • {item}
                  </li>
                ))
              ) : (
                <li className="text-xs text-[#7d8b84]">• Assumes steady employment and standard inflation trajectories.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
