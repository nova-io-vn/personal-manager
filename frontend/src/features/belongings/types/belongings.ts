export interface PersonalItem {
  id: number
  name: string
  category: string
  condition: string
  purchase_date: string | null
  purchase_price: string | null
  warranty_until: string | null
  note: string | null
  created_at: string
  updated_at: string
}

export type PersonalItemPayload = Omit<PersonalItem, 'id' | 'created_at' | 'updated_at'>
