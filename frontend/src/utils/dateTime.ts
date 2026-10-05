import { parseISO } from 'date-fns'

/** The existing SQLite calendar API serializes UTC timestamps without a Z suffix. */
export function parseApiDateTime(value: string): Date {
  return parseISO(/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value) ? value : `${value}Z`)
}
