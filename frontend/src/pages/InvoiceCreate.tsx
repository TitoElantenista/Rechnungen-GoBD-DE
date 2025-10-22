import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, contactAPI } from '../services/api'
import type { ContactList, Contact } from '../types/contact'
import { extractErrorMessage } from '../utils/error'

interface LineItem {
  description: string
  quantity: number
  unit: string
  unit_price: number
  tax_rate: number
}

interface InvoiceFormData {
  seller: {
    name: string
    street: string
    zip: string
    city: string
    country: string
    tax_id: string
    email: string
    phone: string
  }
  buyer: {
    name: string
    street: string
    zip: string
    city: string
    country: string
    tax_id: string
    email: string
    phone: string
  }
  issue_date: string
  delivery_date_start: string
  delivery_date_end: string
  currency: string
  line_items: LineItem[]
  payment_terms: string
  notes: string
  tax_exempt: boolean
}

export default function InvoiceCreate() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [contacts, setContacts] = useState<ContactList[]>([])
  const [contactsLoaded, setContactsLoaded] = useState(false)
  const [contactsLoading, setContactsLoading] = useState(false)
  const [contactsError, setContactsError] = useState<string | null>(null)
  const [showContactPicker, setShowContactPicker] = useState(false)

  const today = new Date().toISOString().split('T')[0]

  const [formData, setFormData] = useState<InvoiceFormData>({
    seller: {
      name: 'Musterfirma Software GmbH',
      street: 'Innovationsstraße 42',
      zip: '10115',
      city: 'Berlin',
      country: 'DE',
      tax_id: 'DE123456789',
      email: 'rechnung@musterfirma.de',
      phone: '+49 30 12345678'
    },
    buyer: {
      name: '',
      street: '',
      zip: '',
      city: '',
      country: 'DE',
      tax_id: '',
      email: '',
      phone: ''
    },
    issue_date: today,
    delivery_date_start: today,
    delivery_date_end: today,
    currency: 'EUR',
    line_items: [
      {
        description: '',
        quantity: 1,
        unit: 'Stk',
        unit_price: 0,
        tax_rate: 19
      }
    ],
    payment_terms: 'Zahlbar innerhalb von 14 Tagen ohne Abzug.',
    notes: '',
    tax_exempt: false
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const toDateTime = (value?: string) => {
        if (!value) return undefined
        return `${value}T00:00:00`
      }

      const optional = (value?: string) => {
        if (value === undefined || value === null) return undefined
        const trimmed = value.trim()
        return trimmed.length > 0 ? trimmed : undefined
      }

      const payload = {
        ...formData,
        seller: {
          ...formData.seller,
          email: optional(formData.seller.email),
          phone: optional(formData.seller.phone)
        },
        buyer: {
          ...formData.buyer,
          tax_id: optional(formData.buyer.tax_id),
          email: optional(formData.buyer.email),
          phone: optional(formData.buyer.phone)
        },
        notes: optional(formData.notes),
        payment_terms: optional(formData.payment_terms),
        issue_date: toDateTime(formData.issue_date),
        delivery_date_start: toDateTime(formData.delivery_date_start),
        delivery_date_end: toDateTime(formData.delivery_date_end),
        line_items: formData.line_items.map((item) => ({
          ...item,
          description: item.description.trim(),
          quantity: Number(item.quantity),
          unit_price: Number(item.unit_price),
          tax_rate: Number(item.tax_rate)
        }))
      }

      const response = await api.post('/api/invoices', payload)
      navigate(`/invoices/${response.data.id}`)
    } catch (err: any) {
      setError(extractErrorMessage(err, 'Fehler beim Erstellen der Rechnung'))
    } finally {
      setLoading(false)
    }
  }

  const handleToggleContactPicker = async () => {
    setContactsError(null)
    if (!contactsLoaded) {
      setContactsLoading(true)
      try {
        const data = await contactAPI.list()
        setContacts(data)
        setContactsLoaded(true)
        setShowContactPicker(true)
      } catch (err: any) {
        setContactsError(extractErrorMessage(err, 'Kontakte konnten nicht geladen werden'))
      } finally {
        setContactsLoading(false)
      }
    } else {
      setShowContactPicker((prev) => !prev)
    }
  }

  const handleSelectContact = async (contactId: string) => {
    if (!contactId) return
    setContactsError(null)
    setContactsLoading(true)
    try {
      const contact: Contact = await contactAPI.get(Number(contactId))
      const buyerName = contact.company_name && contact.contact_person
        ? `${contact.company_name} (${contact.contact_person})`
        : contact.company_name || contact.contact_person || ''
      
      setFormData((prev) => ({
        ...prev,
        buyer: {
          ...prev.buyer,
          name: buyerName,
          street: contact.street || '',
          zip: contact.zip_code || '',
          city: contact.city || '',
          country: contact.country || 'DE',
          tax_id: contact.tax_id || '',
          email: contact.email || '',
          phone: contact.phone || ''
        }
      }))
    } catch (err: any) {
      setContactsError(extractErrorMessage(err, 'Kontakt konnte nicht geladen werden'))
    } finally {
      setContactsLoading(false)
    }
  }

  const addLineItem = () => {
    setFormData({
      ...formData,
      line_items: [
        ...formData.line_items,
        {
          description: '',
          quantity: 1,
          unit: 'Stk',
          unit_price: 0,
          tax_rate: 19
        }
      ]
    })
  }

  const removeLineItem = (index: number) => {
    setFormData({
      ...formData,
      line_items: formData.line_items.filter((_, i) => i !== index)
    })
  }

  const updateLineItem = (index: number, field: keyof LineItem, value: any) => {
    const newLineItems = [...formData.line_items]
    newLineItems[index] = { ...newLineItems[index], [field]: value }
    setFormData({ ...formData, line_items: newLineItems })
  }

  const calculateTotals = () => {
    let netTotal = 0
    let taxTotal = 0

    formData.line_items.forEach(item => {
      const lineNet = item.quantity * item.unit_price
      const taxAmount = lineNet * item.tax_rate / 100
      netTotal += lineNet
      taxTotal += taxAmount
    })

    return {
      net: netTotal.toFixed(2),
      tax: taxTotal.toFixed(2),
      gross: (netTotal + taxTotal).toFixed(2)
    }
  }

  const totals = calculateTotals()

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Neue Rechnung erstellen</h1>
        <button
          onClick={() => navigate('/invoices')}
          className="px-4 py-2 text-gray-600 hover:text-gray-900"
        >
          Abbrechen
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Verkäufer */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Verkäufer (Rechnungssteller)</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Firmenname *
              </label>
              <input
                type="text"
                required
                value={formData.seller.name}
                onChange={(e) => setFormData({
                  ...formData,
                  seller: { ...formData.seller, name: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Straße *
              </label>
              <input
                type="text"
                required
                value={formData.seller.street}
                onChange={(e) => setFormData({
                  ...formData,
                  seller: { ...formData.seller, street: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">PLZ *</label>
              <input
                type="text"
                required
                value={formData.seller.zip}
                onChange={(e) => setFormData({
                  ...formData,
                  seller: { ...formData.seller, zip: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stadt *</label>
              <input
                type="text"
                required
                value={formData.seller.city}
                onChange={(e) => setFormData({
                  ...formData,
                  seller: { ...formData.seller, city: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                USt-IdNr. *
              </label>
              <input
                type="text"
                required
                value={formData.seller.tax_id}
                onChange={(e) => setFormData({
                  ...formData,
                  seller: { ...formData.seller, tax_id: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="DE123456789"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">E-Mail</label>
              <input
                type="email"
                value={formData.seller.email}
                onChange={(e) => setFormData({
                  ...formData,
                  seller: { ...formData.seller, email: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Käufer */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Käufer (Rechnungsempfänger)</h2>
            <button
              type="button"
              onClick={handleToggleContactPicker}
              className="self-start md:self-auto text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              {contactsLoading
                ? 'Kontakte werden geladen...'
                : showContactPicker
                  ? 'Kontaktliste verbergen'
                  : 'Kontaktdaten importieren'}
            </button>
          </div>

          {contactsError && (
            <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
              {contactsError}
            </div>
          )}

          {showContactPicker && (
            <div className="mb-4 flex flex-col sm:flex-row sm:items-center gap-3">
              <select
                className="w-full sm:w-auto flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                defaultValue=""
                onChange={(e) => handleSelectContact(e.target.value)}
                disabled={contactsLoading || contacts.length === 0}
              >
                <option value="">Kontakt auswählen…</option>
                {contacts.map((contact) => {
                  const label = contact.company_name && contact.contact_person
                    ? `${contact.company_name} (${contact.contact_person})`
                    : contact.company_name || contact.contact_person || `Kontakt #${contact.id}`
                  return (
                    <option key={contact.id} value={contact.id}>
                      {label}
                    </option>
                  )
                })}
              </select>
              {contactsLoading && (
                <span className="text-sm text-gray-500">Lädt…</span>
              )}
            </div>
          )}
          {showContactPicker && !contactsLoading && contacts.length === 0 && !contactsError && (
            <p className="mb-4 text-sm text-gray-500">
              Es sind noch keine Kontakte vorhanden.
            </p>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Firmenname / Name *
              </label>
              <input
                type="text"
                required
                value={formData.buyer.name}
                onChange={(e) => setFormData({
                  ...formData,
                  buyer: { ...formData.buyer, name: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Straße *
              </label>
              <input
                type="text"
                required
                value={formData.buyer.street}
                onChange={(e) => setFormData({
                  ...formData,
                  buyer: { ...formData.buyer, street: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">PLZ *</label>
              <input
                type="text"
                required
                value={formData.buyer.zip}
                onChange={(e) => setFormData({
                  ...formData,
                  buyer: { ...formData.buyer, zip: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stadt *</label>
              <input
                type="text"
                required
                value={formData.buyer.city}
                onChange={(e) => setFormData({
                  ...formData,
                  buyer: { ...formData.buyer, city: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                USt-IdNr.
              </label>
              <input
                type="text"
                value={formData.buyer.tax_id}
                onChange={(e) => setFormData({
                  ...formData,
                  buyer: { ...formData.buyer, tax_id: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="DE987654321"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">E-Mail</label>
              <input
                type="email"
                value={formData.buyer.email}
                onChange={(e) => setFormData({
                  ...formData,
                  buyer: { ...formData.buyer, email: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Rechnungsdaten */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Rechnungsdaten</h2>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rechnungsdatum *
              </label>
              <input
                type="date"
                required
                value={formData.issue_date}
                onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lieferdatum von
              </label>
              <input
                type="date"
                value={formData.delivery_date_start}
                onChange={(e) => setFormData({ ...formData, delivery_date_start: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Lieferdatum bis
              </label>
              <input
                type="date"
                value={formData.delivery_date_end}
                onChange={(e) => setFormData({ ...formData, delivery_date_end: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Rechnungspositionen */}
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Rechnungspositionen</h2>
            <button
              type="button"
              onClick={addLineItem}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              + Position hinzufügen
            </button>
          </div>

          <div className="space-y-4">
            {formData.line_items.map((item, index) => (
              <div key={index} className="border border-gray-200 rounded-md p-4">
                <div className="grid grid-cols-12 gap-3">
                  <div className="col-span-5">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Beschreibung *
                    </label>
                    <input
                      type="text"
                      required
                      value={item.description}
                      onChange={(e) => updateLineItem(index, 'description', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="z.B. Softwareentwicklung"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Menge *
                    </label>
                    <input
                      type="number"
                      required
                      step="0.01"
                      min="0"
                      value={item.quantity}
                      onChange={(e) => updateLineItem(index, 'quantity', parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="col-span-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Einheit
                    </label>
                    <select
                      value={item.unit}
                      onChange={(e) => updateLineItem(index, 'unit', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="Stk">Stk</option>
                      <option value="H">H</option>
                      <option value="kg">kg</option>
                      <option value="m">m</option>
                      <option value="m²">m²</option>
                    </select>
                  </div>

                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Preis (€) *
                    </label>
                    <input
                      type="number"
                      required
                      step="0.01"
                      min="0"
                      value={item.unit_price}
                      onChange={(e) => updateLineItem(index, 'unit_price', parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div className="col-span-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      MwSt. %
                    </label>
                    <select
                      value={item.tax_rate}
                      onChange={(e) => updateLineItem(index, 'tax_rate', parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="19">19%</option>
                      <option value="7">7%</option>
                      <option value="0">0%</option>
                    </select>
                  </div>

                  <div className="col-span-1 flex items-end">
                    {formData.line_items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeLineItem(index)}
                        className="w-full px-3 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200"
                      >
                        ×
                      </button>
                    )}
                  </div>
                </div>

                <div className="mt-2 text-right text-sm text-gray-600">
                  Netto: {(item.quantity * item.unit_price).toFixed(2)} € | 
                  Brutto: {(item.quantity * item.unit_price * (1 + item.tax_rate / 100)).toFixed(2)} €
                </div>
              </div>
            ))}
          </div>

          {/* Summen */}
          <div className="mt-6 border-t pt-4">
            <div className="flex justify-end">
              <div className="w-64">
                <div className="flex justify-between py-2">
                  <span className="text-gray-600">Nettobetrag:</span>
                  <span className="font-semibold">{totals.net} €</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-gray-600">MwSt.:</span>
                  <span className="font-semibold">{totals.tax} €</span>
                </div>
                <div className="flex justify-between py-2 border-t-2 border-gray-800 text-lg">
                  <span className="font-bold">Bruttobetrag:</span>
                  <span className="font-bold">{totals.gross} €</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Zahlungsbedingungen & Hinweise */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Weitere Angaben</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Zahlungsbedingungen
              </label>
              <textarea
                rows={2}
                value={formData.payment_terms}
                onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="z.B. Zahlbar innerhalb von 14 Tagen ohne Abzug."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hinweise
              </label>
              <textarea
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="z.B. Vielen Dank für Ihren Auftrag!"
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/invoices')}
            className="px-6 py-3 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Abbrechen
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400"
          >
            {loading ? 'Erstelle...' : 'Rechnung erstellen'}
          </button>
        </div>
      </form>
    </div>
  )
}
