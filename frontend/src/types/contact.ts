export interface Contact {
  id: number
  contact_type: 'customer' | 'supplier' | 'both'
  company_name?: string
  contact_person?: string
  street: string
  zip_code: string
  city: string
  country: string
  tax_id?: string
  email?: string
  phone?: string
  website?: string
  notes?: string
  is_active: boolean
  created_by: number
  created_at: string
  updated_at: string
}

export interface ContactCreate {
  contact_type: 'customer' | 'supplier' | 'both'
  company_name?: string
  contact_person?: string
  street: string
  zip_code: string
  city: string
  country?: string
  tax_id?: string
  email?: string
  phone?: string
  website?: string
  notes?: string
  is_active?: boolean
}

export interface ContactList {
  id: number
  contact_type: string
  company_name?: string
  contact_person?: string
  city: string
  email?: string
  phone?: string
  is_active: boolean
}
