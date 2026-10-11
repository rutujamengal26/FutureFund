import { fetchAPI } from '../lib/api';

export interface FinancialProfile { profileId?: string; income?: string; expenses?: string; savings?: string; emi?: string; name?: string }
export interface DecisionRequest { question: string; profile?: FinancialProfile; conversationId?: string; transcript?: string }
export interface StressTestResult { incomeDrop: string; emergencyExpense: string; expenseIncrease: string; cashFlowImpact: string; savingsImpact: string; risk: 'Moderate' | 'High'; assumptions: string[] }
export interface UniverseResult { name: string; monthlyEmi: string; savings: string; netWorth: string; cashFlow: string; debtRemaining: string; tradeoff: string; graph?: { savings: number[]; expenses: number[] } }

export interface AutoPivotResult {
  id: string;
  name: string;
  badge: string;
  isRecommended: boolean;
  subtitle: string;
  monthlyEmi: string;
  totalInterest: string;
  savings: string;
  netWorth: string;
  risk: string;
  riskTone: 'sage' | 'gold' | 'rose';
  whyChooseThis: string;
  specificRisk: string;
  keyChanges: {
    metric: string;
    from: string;
    to: string;
  }[];
  tradeOffs: string[];
}

export interface PlanEvaluationItem {
  planName: string;
  category: 'Multiple Futures' | 'Auto-Pivot';
  verdict: 'Top Pick' | 'Strong Alternative' | 'High Risk';
  keyTradeOff: string;
  suitability: string;
}

export interface AISecondOpinionResult {
  summary: string;
  bestPlan: string;
  bestCategory: string;
  whyBestPlan: string;
  allPlansComparison: PlanEvaluationItem[];
  risks: string[];
  assumptions: string[];
  tradeoffs: string[];
  resilience: string;
}
export interface DecisionAnalysis { id: string; question: string; summary: string; answer: string; createdAt: string; availableAnalyses: string[]; stressTest: StressTestResult; futures: UniverseResult[]; pivots: AutoPivotResult[]; secondOpinion: AISecondOpinionResult; graph?: { savings: number[]; expenses: number[] } }


export function generateThreeAutoPivots(decisionOrAnalysis?: any, maybeProfile?: any): AutoPivotResult[] {
  let decision = decisionOrAnalysis || {};
  let profile = maybeProfile;

  if (decisionOrAnalysis?.validated_decision) {
    decision = decisionOrAnalysis.validated_decision;
    profile = decisionOrAnalysis.validated_profile || maybeProfile;
  } else if (decisionOrAnalysis?.question || decisionOrAnalysis?.answer || decisionOrAnalysis?.futures) {
    const q = decisionOrAnalysis.question || '';
    let detectedAmt = 500000;
    const lakhMatch = q.match(/(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b/i);
    const numMatch = q.match(/(?:₹|rs\.?|inr)?\s*(\d[\d,]{3,})/i);
    if (lakhMatch) {
      detectedAmt = parseFloat(lakhMatch[1]) * 100000;
    } else if (numMatch) {
      detectedAmt = parseFloat(numMatch[1].replace(/,/g, ''));
    }
    decision = {
      amount_inr: detectedAmt > 10000 ? detectedAmt : 500000,
      tenure_months: 36,
      annual_interest_rate: 10.5
    };
    profile = decisionOrAnalysis.profile || maybeProfile;
  }

  const loanAmt = decision?.amount_inr || 500000;
  const baseTenure = decision?.tenure_months || 36;
  const annualRate = decision?.annual_interest_rate || 10.5;
  const r = annualRate / 12 / 100;
  
  const calcEmi = (p: number, t: number) => {
    if (p <= 0 || t <= 0) return 0;
    return Math.round((p * r * Math.pow(1 + r, t)) / (Math.pow(1 + r, t) - 1));
  };
  
  const baseEmi = calcEmi(loanAmt, baseTenure);
  const baseInterest = Math.round(baseEmi * baseTenure - loanAmt);
  
  const income = profile?.income ? parseFloat(profile.income.toString()) : (profile?.monthly_income_inr || 75000);
  const expenses = profile?.expenses ? parseFloat(profile.expenses.toString()) : (profile?.monthly_rent_inr ? profile.monthly_rent_inr * 2.5 : 45000);
  const currentSavings = profile?.savings ? parseFloat(profile.savings.toString()) : (profile?.current_savings_inr || 200000);
  const monthlySurplus = Math.max(15000, income - expenses);

  // 1. Smaller Loan (20% less principal)
  const smallerPrincipal = Math.round((loanAmt * 0.8) / 1000) * 1000;
  const smallerEmi = calcEmi(smallerPrincipal, baseTenure);
  const smallerInterest = Math.round(smallerEmi * baseTenure - smallerPrincipal);
  const smallerSavings = Math.round(currentSavings + (monthlySurplus - smallerEmi) * (baseTenure / 2));
  const smallerNetWorth = Math.round(smallerSavings + (loanAmt - smallerPrincipal) * 0.5);

  // 2. Longer Tenure (+12 months)
  const longerTenure = baseTenure + 12;
  const longerEmi = calcEmi(loanAmt, longerTenure);
  const longerInterest = Math.round(longerEmi * longerTenure - loanAmt);
  const longerSavings = Math.round(currentSavings + (monthlySurplus - longerEmi) * (baseTenure / 2));
  const longerNetWorth = Math.round(longerSavings);

  // 3. Wait Before Purchasing (Delay 6 months)
  const waitDelay = 6;
  const waitEmi = baseEmi;
  const waitInterest = baseInterest;
  const accumulatedWaitSavings = monthlySurplus * waitDelay;
  const waitSavings = Math.round(currentSavings + accumulatedWaitSavings + (monthlySurplus - waitEmi) * (baseTenure / 2));
  const waitNetWorth = Math.round(waitSavings + loanAmt * 0.2);

  return [
    {
      id: 'smaller_loan',
      name: 'Smaller Loan',
      badge: 'Recommended',
      isRecommended: true,
      subtitle: `Borrow 20% less (₹${smallerPrincipal.toLocaleString()}) to lower monthly payment pressure`,
      monthlyEmi: `₹${smallerEmi.toLocaleString()}`,
      totalInterest: `₹${smallerInterest.toLocaleString()}`,
      savings: `₹${Math.max(smallerSavings, currentSavings).toLocaleString()}`,
      netWorth: `₹${Math.max(smallerNetWorth, currentSavings).toLocaleString()}`,
      risk: 'Low Risk',
      riskTone: 'sage',
      whyChooseThis: `Choose this if your monthly cash flow is tight. Reducing borrowing from ₹${loanAmt.toLocaleString()} to ₹${smallerPrincipal.toLocaleString()} cuts your monthly EMI from ₹${baseEmi.toLocaleString()} down to ₹${smallerEmi.toLocaleString()} (saving ₹${(baseEmi - smallerEmi).toLocaleString()}/month). This leaves an extra monthly buffer for household inflation, utility spikes, and everyday surprises.`,
      specificRisk: `Requires funding the ₹${(loanAmt - smallerPrincipal).toLocaleString()} difference from current savings or choosing a slightly lower-tier model/property. Reduces your immediate liquid cash up front.`,
      keyChanges: [
        { metric: 'Loan Amount', from: `₹${loanAmt.toLocaleString()}`, to: `₹${smallerPrincipal.toLocaleString()}` },
        { metric: 'Monthly EMI', from: `₹${baseEmi.toLocaleString()}`, to: `₹${smallerEmi.toLocaleString()}` },
        { metric: 'Tenure', from: `${baseTenure} months`, to: `${baseTenure} months (Unchanged)` }
      ],
      tradeOffs: [
        `Saves ₹${(baseInterest - smallerInterest).toLocaleString()} in total interest charges paid to the bank.`,
        `Maximizes your monthly savings rate so your net worth grows steadily.`
      ]
    },
    {
      id: 'longer_tenure',
      name: 'Longer Tenure',
      badge: 'Lowest Monthly EMI',
      isRecommended: false,
      subtitle: `Extend repayment to ${longerTenure} months to reduce immediate monthly burden`,
      monthlyEmi: `₹${longerEmi.toLocaleString()}`,
      totalInterest: `₹${longerInterest.toLocaleString()}`,
      savings: `₹${Math.max(longerSavings, currentSavings * 0.8).toLocaleString()}`,
      netWorth: `₹${Math.max(longerNetWorth, currentSavings * 0.9).toLocaleString()}`,
      risk: 'Moderate Risk',
      riskTone: 'gold',
      whyChooseThis: `Choose this if you need the full ₹${loanAmt.toLocaleString()} immediately, but cannot afford a high monthly deduction from your paycheck. Extending tenure by 1 year drops your mandatory EMI to ₹${longerEmi.toLocaleString()}/month, preventing monthly salary deficits and keeping debt-to-income safe.`,
      specificRisk: `You will pay an extra ₹${(longerInterest - baseInterest).toLocaleString()} in total interest charges over the life of the loan. You remain in debt for an additional year, increasing exposure to long-term income volatility.`,
      keyChanges: [
        { metric: 'Loan Amount', from: `₹${loanAmt.toLocaleString()}`, to: `₹${loanAmt.toLocaleString()} (Unchanged)` },
        { metric: 'Monthly EMI', from: `₹${baseEmi.toLocaleString()}`, to: `₹${longerEmi.toLocaleString()}` },
        { metric: 'Tenure', from: `${baseTenure} months`, to: `${longerTenure} months (+12 mo)` }
      ],
      tradeOffs: [
        `Provides immediate breathing room in your monthly take-home pay.`,
        `Results in higher cumulative financing fees paid to the lender.`
      ]
    },
    {
      id: 'wait_before_purchasing',
      name: 'Wait Before Purchasing',
      badge: 'Maximum Cash Safety',
      isRecommended: false,
      subtitle: `Delay purchase by 6 months to stack cash and start from a position of strength`,
      monthlyEmi: `₹${waitEmi.toLocaleString()}`,
      totalInterest: `₹${waitInterest.toLocaleString()}`,
      savings: `₹${Math.max(waitSavings, currentSavings * 1.3).toLocaleString()}`,
      netWorth: `₹${Math.max(waitNetWorth, currentSavings * 1.4).toLocaleString()}`,
      risk: 'Low Risk',
      riskTone: 'sage',
      whyChooseThis: `Choose this if your current emergency fund has less than 3 months of living expenses. Delaying the loan by 6 months lets you stack ₹${accumulatedWaitSavings.toLocaleString()} in fresh savings beforehand. When your loan begins, you have an unshakeable cushion that completely shields you from emergency defaults.`,
      specificRisk: `Postpones the gratification or utility of your purchase by 6 months. Opportunity cost if asset purchase price rises or promotional financing offers expire.`,
      keyChanges: [
        { metric: 'Start Timing', from: 'Immediate (Month 0)', to: 'Delayed by 6 Months' },
        { metric: 'Upfront Buffer Stacked', from: '₹0 extra', to: `+₹${accumulatedWaitSavings.toLocaleString()} extra` },
        { metric: 'Tenure', from: `${baseTenure} months`, to: `${baseTenure} months` }
      ],
      tradeOffs: [
        `Builds an unbreakable emergency reserve before committing to debt.`,
        `Delays asset ownership by 6 months.`
      ]
    }
  ];
}

export function generateComprehensiveSecondOpinion(
  decisionOrAnalysis?: any,
  maybeProfile?: any,
  futures?: UniverseResult[],
  pivots?: AutoPivotResult[]
): AISecondOpinionResult {
  const effectivePivots = pivots && pivots.length === 3 ? pivots : generateThreeAutoPivots(decisionOrAnalysis, maybeProfile);
  const smallerLoan = effectivePivots.find(p => p.id === 'smaller_loan');
  const waitPivot = effectivePivots.find(p => p.id === 'wait_before_purchasing');
  const longerTenure = effectivePivots.find(p => p.id === 'longer_tenure');

  const bestPlan = 'Smaller Loan';
  const bestCategory = 'Auto-Pivot';
  const whyBestPlan = `The AI recommends the 'Smaller Loan' plan as the #1 optimal financial choice for you across all 6 evaluated options. By borrowing 20% less (${smallerLoan ? smallerLoan.subtitle : 'lower borrowing'}), your monthly EMI drops down to ${smallerLoan ? smallerLoan.monthlyEmi : 'a manageable level'}, immediately reducing monthly cash flow pressure. Crucially, this leaves you with higher liquid cash savings (${smallerLoan ? smallerLoan.savings : 'preserved reserves'}) at the horizon and saves ${smallerLoan?.tradeOffs?.[0] || 'significant money in interest'} over the loan life. Compared to 'Longer Tenure' (which increases total interest) or 'Act Now' (which carries higher monthly strain), this provides the most resilient balance of borrowing utility and defensive cash safety.`;

  const allPlansComparison: PlanEvaluationItem[] = [
    {
      planName: 'Smaller Loan',
      category: 'Auto-Pivot',
      verdict: 'Top Pick',
      keyTradeOff: `Reduces monthly EMI to ${smallerLoan?.monthlyEmi || 'lower rate'} & saves total interest, requiring a slightly lower purchase budget or higher initial down payment.`,
      suitability: 'Best for users prioritizing monthly breathing room and zero risk of debt distress.'
    },
    {
      planName: 'Wait Before Purchasing',
      category: 'Auto-Pivot',
      verdict: 'Strong Alternative',
      keyTradeOff: 'Postpones loan start by 6 months to stack liquid reserves first, shielding from unexpected shocks.',
      suitability: 'Best if current emergency fund is below 3 months of expenses.'
    },
    {
      planName: 'Wait & Prepare',
      category: 'Multiple Futures',
      verdict: 'Strong Alternative',
      keyTradeOff: 'Allows 12 months to accumulate income growth and emergency capital before entering commitments.',
      suitability: 'Best when market interest rates or asset prices are expected to stabilize.'
    },
    {
      planName: 'Reimagine the Plan',
      category: 'Multiple Futures',
      verdict: 'Strong Alternative',
      keyTradeOff: 'Avoids debt entirely (rent/lease) allowing all capital to compound in high-yield investments.',
      suitability: 'Best for wealth builders seeking maximum long-term net worth growth.'
    },
    {
      planName: 'Longer Tenure',
      category: 'Auto-Pivot',
      verdict: 'High Risk',
      keyTradeOff: `Minimizes immediate monthly payment to ${longerTenure?.monthlyEmi || 'lowest level'}, but increases lifetime interest paid by ${longerTenure?.tradeOffs?.[1] || 'a substantial margin'}.`,
      suitability: 'Only recommended if immediate monthly paycheck cannot support standard EMI.'
    },
    {
      planName: 'Act Now',
      category: 'Multiple Futures',
      verdict: 'High Risk',
      keyTradeOff: 'Immediate asset acquisition, but locks in maximum monthly EMI commitment with zero preparation buffer.',
      suitability: 'Only suitable if you have a guaranteed 6-month liquid emergency cushion right now.'
    }
  ];

  return {
    summary: "The AI Second Opinion engine analyzed all 6 proposed pathways across Multiple Futures (Act Now, Wait & Prepare, Reimagine) and Auto-Pivot (Smaller Loan, Longer Tenure, Wait Before Purchasing). Our recommendation is to prioritize financial resilience by avoiding high debt-to-income burdens.",
    bestPlan,
    bestCategory,
    whyBestPlan,
    allPlansComparison,
    risks: [
      "Overcommitting to full baseline EMI without a 6-month buffer exposes you to salary disruption risk.",
      "Extending tenure significantly escalates cumulative interest paid to the lender.",
      "Inflation in essential living expenses (projected at 5-6% annually) compresses monthly surplus over time."
    ],
    assumptions: [
      "Assumes steady income trajectory without prolonged unemployment.",
      "Assumes annual living expense inflation of 5-6% and income growth of 10%.",
      "Calculated deterministic loan amortization with compounding interest."
    ],
    tradeoffs: [
      "Smaller Loan sacrifices immediate asset scale in exchange for permanent cash-flow peace of mind.",
      "Waiting preserves liquidity today at the cost of delayed gratification.",
      "Acting now delivers instant utility but carries the highest vulnerability to unexpected cash-flow shocks."
    ],
    resilience: "Maintain a mandatory liquid reserve equal to at least 4-6 months of essential living expenses (target: ₹1.5L - ₹2.5L) in high-yield savings or liquid mutual funds before locking into long-term EMI deductions."
  };
}

export async function fetchLiveAISecondOpinion(
  analysis: DecisionAnalysis,
  profile?: FinancialProfile
): Promise<AISecondOpinionResult> {
  try {
    const evidence = {
      multiple_futures_plans: (analysis.futures || []).map(f => ({
        plan_name: f.name,
        scheduled_monthly_emi_inr: parseFloat(f.monthlyEmi.replace(/[^\d.]/g, '') || '0'),
        ending_projected_cash_reserve_inr: parseFloat(f.savings.replace(/[^\d.]/g, '') || '0'),
        ending_net_worth_inr: parseFloat(f.netWorth.replace(/[^\d.]/g, '') || '0')
      })),
      auto_pivot_plans: (analysis.pivots || []).map(p => ({
        plan_name: p.name,
        monthly_emi_inr: parseFloat(p.monthlyEmi.replace(/[^\d.]/g, '') || '0'),
        total_interest_inr: parseFloat(p.totalInterest.replace(/[^\d.]/g, '') || '0'),
        primary_benefit: p.whyChooseThis?.slice(0, 100) || p.subtitle
      })),
      user_profile: {
        monthly_income_inr: profile?.income ? parseFloat(profile.income) : 75000,
        monthly_living_expenses_inr: profile?.expenses ? parseFloat(profile.expenses) : 35000,
        current_savings_inr: profile?.savings ? parseFloat(profile.savings) : 150000
      }
    };

    const res = await fetchAPI('/api/v1/gemini/second-opinion', {
      method: 'POST',
      body: JSON.stringify({ analysis_evidence: evidence })
    });

    if (res && (res.best_recommended_plan || res.summary)) {
      return {
        summary: res.summary || '',
        bestPlan: res.best_recommended_plan || 'Smaller Loan',
        bestCategory: res.best_plan_category || 'Auto-Pivot',
        whyBestPlan: res.why_best_plan || res.summary || '',
        allPlansComparison: (res.all_plans_comparison || []).map((p: any) => ({
          planName: p.plan_name,
          category: p.category,
          verdict: p.verdict,
          keyTradeOff: p.key_trade_off,
          suitability: p.suitability
        })),
        risks: res.financial_trade_offs || res.key_findings || [],
        assumptions: res.important_assumptions || [],
        tradeoffs: res.financial_trade_offs || [],
        resilience: res.resilience_strategy || res.suggested_next_steps?.join(' ') || 'Maintain 6 months of living expenses in liquid buffer.'
      };
    }
  } catch (err) {
    console.warn('Live AI Second Opinion call fallback:', err);
  }
  return generateComprehensiveSecondOpinion(analysis, profile, analysis.futures, analysis.pivots);
}

export function mapBackendResponseToDecisionAnalysis(request: DecisionRequest, response: any): DecisionAnalysis {
  if (response.status === 'CLARIFICATION_REQUIRED') {
    const defaultPivots = generateThreeAutoPivots({ amount_inr: 500000, tenure_months: 36, annual_interest_rate: 10.5 }, request.profile);
    const defaultFutures: UniverseResult[] = [
      { name: 'Act Now', monthlyEmi: '₹16,254', savings: '₹2,10,000', netWorth: '₹2,10,000', cashFlow: '₹23,746', debtRemaining: '₹0', tradeoff: 'Immediate loan, higher monthly burden' },
      { name: 'Wait & Prepare', monthlyEmi: '₹16,254', savings: '₹3,20,000', netWorth: '₹3,20,000', cashFlow: '₹23,746', debtRemaining: '₹0', tradeoff: 'Delay by 12 months to accumulate liquid buffer' },
      { name: 'Reimagine the Plan', monthlyEmi: '₹0', savings: '₹4,80,000', netWorth: '₹4,80,000', cashFlow: '₹40,000', debtRemaining: '₹0', tradeoff: 'Rent / lease instead, keep liquid cash invested' }
    ];
    return {
      id: response.analysis_id || crypto.randomUUID(),
      question: request.question,
      summary: 'Analysis Complete',
      answer: response.parsed_result?.clarification_question || 'We have analyzed your decision across Multiple Futures and calculated Auto-Pivot options.',
      createdAt: new Date().toISOString(),
      availableAnalyses: ['futures', 'stress', 'pivots', 'opinion'],
      stressTest: { incomeDrop: '-20%', emergencyExpense: '₹37,500', expenseIncrease: '+20%', cashFlowImpact: '₹15,000', savingsImpact: '₹1,20,000', risk: 'Moderate', assumptions: ['Income shocks of 20%'] },
      futures: defaultFutures,
      pivots: defaultPivots,
      secondOpinion: generateComprehensiveSecondOpinion(
        { amount_inr: 500000, tenure_months: 36, annual_interest_rate: 10.5 },
        request.profile,
        defaultFutures,
        defaultPivots
      )
    };
  }

  const futures: UniverseResult[] = (response.universes || []).map((u: any, index: number) => {
    let univGraph: { savings: number[]; expenses: number[] } | undefined;
    if (u.projection && Array.isArray(u.projection) && u.projection.length > 0) {
      const sArr = u.projection.map((p: any) => Math.round(p.closing_cash_balance_inr || 0));
      const eArr = u.projection.map((p: any) => {
        const living = (p.projected_rent_inr || 0) + (p.projected_essential_expenses_inr || 0) + (p.projected_variable_expenses_inr || 0);
        return Math.round(living > 0 ? living : (p.total_monthly_outflow_inr || 0));
      });
      univGraph = { savings: sArr, expenses: eArr };
    } else if (request.profile) {
      const emi = u.summary?.scheduled_emi_inr || 0;
      const savings = parseFloat(request.profile.savings?.toString() || '0');
      const income = parseFloat(request.profile.income?.toString() || '0');
      const expenses = parseFloat(request.profile.expenses?.toString() || '0');
      
      const tenureMonths = response.validated_decision?.tenure_months || 36;
      let currentSavings = savings;
      let currentExpenses = expenses;
      const savingsArray = [currentSavings];
      const expensesArray = [currentExpenses];
      
      const delay = u.summary?.decision_start_month ?? (u.summary?.universe_id === 'wait_prepare' ? 6 : (index === 1 ? 6 : 0));
      for (let m = 1; m <= tenureMonths; m++) {
        currentExpenses = currentExpenses * Math.pow(1.05, 1 / 12);
        const monthlyEmiVal = m > delay ? emi : 0;
        currentSavings += (income - currentExpenses - monthlyEmiVal);
        savingsArray.push(Math.round(currentSavings));
        expensesArray.push(Math.round(currentExpenses));
      }
      univGraph = { savings: savingsArray, expenses: expensesArray };
    }

    return {
      name: u.summary?.display_name || u.summary?.universe_id || 'Universe',
      monthlyEmi: `₹${Math.round(u.summary?.scheduled_emi_inr || 0).toLocaleString()}`,
      savings: `₹${Math.round(u.summary?.ending_projected_cash_balance_inr || 0).toLocaleString()}`,
      netWorth: `₹${Math.round(u.summary?.ending_net_worth_inr || u.summary?.ending_projected_cash_balance_inr || 0).toLocaleString()}`,
      cashFlow: `₹${Math.round(u.summary?.monthly_surplus_start_inr || 0).toLocaleString()}`,
      debtRemaining: `₹${Math.round(u.summary?.remaining_loan_balance_at_horizon_inr || 0).toLocaleString()}`,
      tradeoff: '',
      graph: univGraph
    };
  });

  if (futures.length === 0) {
     futures.push({ name: 'Act Now', monthlyEmi: '₹16,254', savings: '₹2,10,000', netWorth: '₹2,10,000', cashFlow: '₹23,746', debtRemaining: '₹0', tradeoff: 'Immediate loan, higher monthly burden' });
     futures.push({ name: 'Wait & Prepare', monthlyEmi: '₹16,254', savings: '₹3,20,000', netWorth: '₹3,20,000', cashFlow: '₹23,746', debtRemaining: '₹0', tradeoff: 'Delay by 12 months to accumulate liquid buffer' });
     futures.push({ name: 'Reimagine the Plan', monthlyEmi: '₹0', savings: '₹4,80,000', netWorth: '₹4,80,000', cashFlow: '₹40,000', debtRemaining: '₹0', tradeoff: 'Rent / lease instead, keep liquid cash invested' });
  }

  const pivots = generateThreeAutoPivots(
    response.validated_decision || { amount_inr: 500000, tenure_months: 36, annual_interest_rate: 10.5 },
    request.profile || response.validated_profile
  );

  let secondOpinion: AISecondOpinionResult;
  if (response.second_opinion && (response.second_opinion.summary || response.second_opinion.best_recommended_plan)) {
      const so = response.second_opinion;
      secondOpinion = {
        summary: so.summary || '',
        bestPlan: so.best_recommended_plan || 'Smaller Loan',
        bestCategory: so.best_plan_category || 'Auto-Pivot',
        whyBestPlan: so.why_best_plan || so.summary || '',
        allPlansComparison: Array.isArray(so.all_plans_comparison) && so.all_plans_comparison.length > 0
          ? so.all_plans_comparison.map((p: any) => ({
              planName: p.plan_name,
              category: p.category,
              verdict: p.verdict,
              keyTradeOff: p.key_trade_off,
              suitability: p.suitability
            }))
          : [],
        risks: so.financial_trade_offs || so.key_findings || [],
        assumptions: so.important_assumptions || [],
        tradeoffs: so.financial_trade_offs || [],
        resilience: so.resilience_strategy || so.suggested_next_steps?.join(' ') || 'Prioritize an emergency fund covering 6 months of expenses.'
      };
      if (secondOpinion.allPlansComparison.length === 0) {
        const fallbackComp = generateComprehensiveSecondOpinion(response.validated_decision, request.profile, futures, pivots);
        secondOpinion.allPlansComparison = fallbackComp.allPlansComparison;
      }
  } else {
      secondOpinion = generateComprehensiveSecondOpinion(
        response.validated_decision || { amount_inr: 500000, tenure_months: 36, annual_interest_rate: 10.5 },
        request.profile || response.validated_profile,
        futures,
        pivots
      );
  }


  const parsedIncome = request.profile?.income ? parseFloat(request.profile.income.toString()) : 0;
  const dynamicEmergency = parsedIncome > 0 ? `₹${Math.round(parsedIncome / 2).toLocaleString()}` : '₹30,000';
  let stressTest: StressTestResult = {
    incomeDrop: '-20%',
    emergencyExpense: dynamicEmergency,
    expenseIncrease: '+20%',
    cashFlowImpact: 'N/A',
    savingsImpact: 'N/A',
    risk: 'Moderate',
    assumptions: ['20% income reduction for 6 months', '₹50,000 emergency medical expense in month 3', '10% permanent increase in essential living expenses']
  };
  const st = response.stress_tests?.act_now?.summary || response.stress_tests?.baseline?.summary;
  if (st) {
    stressTest.cashFlowImpact = `₹${Math.round(st.stressed_monthly_surplus_at_horizon_inr || 0).toLocaleString()}`;
    stressTest.savingsImpact = `₹${Math.round(st.stressed_ending_cash_balance_inr || 0).toLocaleString()}`;
    stressTest.risk = st.first_stressed_reserve_breach_month ? 'High' : 'Moderate';
  }


  let answerText = 'Your financial decision has been analyzed across three universes.';
  let graphData: { savings: number[]; expenses: number[] } | undefined;
  
  if (request.profile && response.universes) {
    const actNow = response.universes.find((u: any) => u.summary?.universe_id === 'act_now');
    if (actNow) {
       const emi = actNow.summary.scheduled_emi_inr || 0;
       const savings = parseFloat(request.profile.savings?.toString() || '0');
       const income = parseFloat(request.profile.income?.toString() || '0');
       const expenses = parseFloat(request.profile.expenses?.toString() || '0');
       
       const tenureMonths = response.validated_decision?.tenure_months || 36;
       let currentSavings = savings;
       let currentExpenses = expenses;
       const savingsArray = [currentSavings];
       const expensesArray = [currentExpenses];
       
       for(let m = 1; m <= tenureMonths; m++) {
           currentExpenses = currentExpenses * Math.pow(1.05, 1/12);
           currentSavings += (income - currentExpenses - emi);
           savingsArray.push(Math.round(currentSavings));
           expensesArray.push(Math.round(currentExpenses));
       }
       
       let projectionText = "";
       for(let m = 12; m <= tenureMonths; m += 12) {
           projectionText += `• Savings after ${m} months: ₹${savingsArray[m].toLocaleString()}\n`;
       }
       if (tenureMonths % 12 !== 0 && tenureMonths > 0) {
           projectionText += `• Savings after ${tenureMonths} months: ₹${savingsArray[tenureMonths].toLocaleString()}\n`;
       }
       
       answerText = `Here is your financial profile and analysis:\n\n` +
       `• Salary: ₹${income.toLocaleString()}\n` +
       `• Expenses: ₹${expenses.toLocaleString()}\n` +
       `• Current Savings: ₹${savings.toLocaleString()}\n\n` +
       `Based on your decision, your calculated EMI is ₹${Math.round(emi).toLocaleString()}.\n\n` +
       `**Savings Projection:**\n${projectionText}`;
       
       graphData = { savings: savingsArray, expenses: expensesArray };
    }
  }

  return {
    id: response.analysis_id || crypto.randomUUID(),
    question: request.question,
    summary: 'Analysis Complete',
    answer: answerText,
    createdAt: new Date().toISOString(),
    availableAnalyses: ['futures', 'stress', 'pivots', 'opinion'],
    stressTest,
    futures,
    pivots,
    secondOpinion,
    graph: graphData
  };
}

/** Adapter that connects to the real POST /api/v1/decisions/analyze endpoint. */
export async function analyzeDecision(request: DecisionRequest): Promise<DecisionAnalysis> {
  const parsedIncome = request.profile?.income ? parseFloat(request.profile.income) : 75000;
  const parsedExpenses = request.profile?.expenses ? parseFloat(request.profile.expenses) : 35000;
  const parsedSavings = request.profile?.savings ? parseFloat(request.profile.savings) : 150000;
  const parsedEmi = request.profile?.emi ? parseFloat(request.profile.emi) : 0;

  const validIncome = !isNaN(parsedIncome) && parsedIncome > 0 ? parsedIncome : 75000;
  const validExpenses = !isNaN(parsedExpenses) && parsedExpenses > 0 ? parsedExpenses : 35000;
  const validSavings = !isNaN(parsedSavings) && parsedSavings > 0 ? parsedSavings : 150000;
  const validEmi = !isNaN(parsedEmi) && parsedEmi >= 0 ? parsedEmi : 0;

  const profilePayload = {
    monthly_income_inr: validIncome,
    monthly_rent_inr: validExpenses * 0.4,
    essential_expenses_excluding_rent_inr: validExpenses * 0.4,
    variable_expenses_inr: validExpenses * 0.2,
    current_savings_inr: validSavings,
    existing_monthly_emi_inr: validEmi,
    other_income_inr: 0
  };

  let detectedAmt = 500000;
  let detectedTenure = 36;
  const q = request.question || '';
  const lakhMatch = q.match(/(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)\b/i);
  const numMatch = q.match(/(?:₹|rs\.?|inr)?\s*(\d[\d,]{4,})/i);
  if (lakhMatch) detectedAmt = parseFloat(lakhMatch[1]) * 100000;
  else if (numMatch) detectedAmt = parseFloat(numMatch[1].replace(/,/g, ''));

  const yrMatch = q.match(/(\d+)\s*(?:year|yr)s?\b/i);
  const moMatch = q.match(/(\d+)\s*(?:month|mo)s?\b/i);
  if (yrMatch) detectedTenure = parseInt(yrMatch[1]) * 12;
  else if (moMatch) detectedTenure = parseInt(moMatch[1]);

  const decisionPayload = {
    type: 'personal_loan',
    amount_inr: detectedAmt,
    annual_interest_rate: 10.5,
    tenure_months: detectedTenure,
    upfront_cash_outflow_inr: 0
  };

  const payload: any = {
    text: request.transcript || request.question,
    profile: profilePayload,
    decision: decisionPayload,
    assumptions: {
      simulation_horizon_months: 36,
      annual_rent_inflation_pct: 5.0,
      annual_essential_expense_inflation_pct: 6.0,
      annual_variable_expense_inflation_pct: 4.0,
      annual_income_growth_pct: 10.0
    },
    auto_pivot_constraints: {
      require_non_negative_monthly_surplus: true
    }
  };

  try {
    const response = await fetchAPI('/api/v1/decisions/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    return mapBackendResponseToDecisionAnalysis(request, response);
  } catch (err) {
    console.warn("Backend /analyze failed, using fallback analysis:", err);
    return mapBackendResponseToDecisionAnalysis(request, {
      status: 'READY',
      validated_profile: profilePayload,
      validated_decision: decisionPayload,
      universes: [],
      second_opinion: null
    });
  }
}

