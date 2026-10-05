import { FinanceSummaryCards as BaseFinanceSummaryCards } from './FinanceSummaryCards'

export function FinanceSummaryCards(props: { balance: number; income: number; expense: number; budget: number }) {
  return <><h2 className="sr-only">Tài chính</h2><BaseFinanceSummaryCards {...props} /></>
}
