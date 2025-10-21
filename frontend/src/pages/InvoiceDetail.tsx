import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { invoiceAPI } from '../services/api'

interface LineItem {
  id: number
  position: number
  description: string
  quantity: number
  unit: string
  unit_price: number
  tax_rate: number
  line_net: number
  tax_amount: number
  line_gross: number
}

interface Invoice {
  id: number
  invoice_number: string
  issue_date: string
  delivery_date_start?: string
  delivery_date_end?: string
  seller_name: string
  seller_street: string
  seller_zip: string
  seller_city: string
  seller_country: string
  seller_tax_id: string
  seller_email?: string
  seller_phone?: string
  buyer_name: string
  buyer_street: string
  buyer_zip: string
  buyer_city: string
  buyer_country: string
  buyer_tax_id?: string
  buyer_email?: string
  buyer_phone?: string
  currency: string
  net_total: number
  tax_total: number
  gross_total: number
  payment_terms?: string
  notes?: string
  status: string
  pdf_hash: string
  tsa_token: any
  created_at: string
  line_items: LineItem[]
}

export default function InvoiceDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [invoice, setInvoice] = useState<Invoice | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      loadInvoice(parseInt(id))
    }
  }, [id])

  const loadInvoice = async (invoiceId: number) => {
    try {
      setLoading(true)
      setError(null)
      const data = await invoiceAPI.get(invoiceId)
      setInvoice(data)
    } catch (err: any) {
      console.error('Error loading invoice:', err)
      setError('Fehler beim Laden der Rechnung')
      setInvoice(null)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!invoice) return

    try {
      const blob = await invoiceAPI.download(invoice.id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${invoice.invoice_number}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      alert('Fehler beim Herunterladen')
    }
  }

  const handlePreview = async () => {
    if (!invoice) return

    try {
      const blob = await invoiceAPI.preview(invoice.id)
      const url = window.URL.createObjectURL(blob)
      window.open(url, '_blank')
    } catch (err) {
      alert('Fehler beim Öffnen der Vorschau')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'issued': return 'bg-green-100 text-green-800'
      case 'cancelled': return 'bg-red-100 text-red-800'
      case 'draft': return 'bg-gray-100 text-gray-800'
      default: return 'bg-blue-100 text-blue-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'issued': return 'Erstellt'
      case 'cancelled': return 'Storniert'
      case 'draft': return 'Entwurf'
      default: return status
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Lade Rechnung...</div>
      </div>
    )
  }

  if (error || !invoice) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        {error || 'Rechnung nicht gefunden'}
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <h1 className="text-3xl font-bold text-gray-900">
              {invoice.invoice_number}
            </h1>
            <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(invoice.status)}`}>
              {getStatusText(invoice.status)}
            </span>
          </div>
          <p className="text-gray-600">
            Erstellt am {new Date(invoice.created_at).toLocaleDateString('de-DE')}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/invoices')}
            className="px-4 py-2 text-gray-600 hover:text-gray-900"
          >
            ← Zurück
          </button>
          <button
            onClick={handlePreview}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Vorschau
          </button>
          <button
            onClick={handleDownload}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            PDF Download
          </button>
        </div>
      </div>

      {/* Rechnungsinformationen */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Verkäufer */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4 text-gray-900">Rechnungssteller</h2>
          <div className="space-y-1 text-sm">
            <p className="font-semibold">{invoice.seller_name}</p>
            <p>{invoice.seller_street}</p>
            <p>{invoice.seller_zip} {invoice.seller_city}</p>
            <p>{invoice.seller_country}</p>
            <p className="pt-2">USt-IdNr: {invoice.seller_tax_id}</p>
            {invoice.seller_email && <p>E-Mail: {invoice.seller_email}</p>}
            {invoice.seller_phone && <p>Tel: {invoice.seller_phone}</p>}
          </div>
        </div>

        {/* Käufer */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4 text-gray-900">Rechnungsempfänger</h2>
          <div className="space-y-1 text-sm">
            <p className="font-semibold">{invoice.buyer_name}</p>
            <p>{invoice.buyer_street}</p>
            <p>{invoice.buyer_zip} {invoice.buyer_city}</p>
            <p>{invoice.buyer_country}</p>
            {invoice.buyer_tax_id && <p className="pt-2">USt-IdNr: {invoice.buyer_tax_id}</p>}
            {invoice.buyer_email && <p>E-Mail: {invoice.buyer_email}</p>}
            {invoice.buyer_phone && <p>Tel: {invoice.buyer_phone}</p>}
          </div>
        </div>
      </div>

      {/* Rechnungsdaten */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">Rechnungsdaten</h2>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-gray-600">Rechnungsdatum:</p>
            <p className="font-semibold">
              {new Date(invoice.issue_date).toLocaleDateString('de-DE')}
            </p>
          </div>
          {invoice.delivery_date_start && (
            <div>
              <p className="text-gray-600">Lieferdatum:</p>
              <p className="font-semibold">
                {new Date(invoice.delivery_date_start).toLocaleDateString('de-DE')}
                {invoice.delivery_date_end && invoice.delivery_date_end !== invoice.delivery_date_start && 
                  ` - ${new Date(invoice.delivery_date_end).toLocaleDateString('de-DE')}`
                }
              </p>
            </div>
          )}
          <div>
            <p className="text-gray-600">Währung:</p>
            <p className="font-semibold">{invoice.currency}</p>
          </div>
        </div>
      </div>

      {/* Rechnungspositionen */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">Rechnungspositionen</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Pos.</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Beschreibung</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Menge</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Einheit</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Preis</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">MwSt.</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Gesamt</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {invoice.line_items.map((item) => (
                <tr key={item.id}>
                  <td className="px-4 py-3 text-sm text-gray-900">{item.position}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{item.description}</td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right">{item.quantity.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm text-gray-900">{item.unit}</td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right">
                    {item.unit_price.toFixed(2)} {invoice.currency}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right">{item.tax_rate.toFixed(0)}%</td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right font-semibold">
                    {item.line_gross.toFixed(2)} {invoice.currency}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summen */}
        <div className="mt-6 border-t pt-4">
          <div className="flex justify-end">
            <div className="w-72">
              <div className="flex justify-between py-2">
                <span className="text-gray-600">Nettobetrag:</span>
                <span className="font-semibold">{invoice.net_total.toFixed(2)} {invoice.currency}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-gray-600">MwSt.:</span>
                <span className="font-semibold">{invoice.tax_total.toFixed(2)} {invoice.currency}</span>
              </div>
              <div className="flex justify-between py-3 border-t-2 border-gray-800 text-lg">
                <span className="font-bold">Bruttobetrag:</span>
                <span className="font-bold">{invoice.gross_total.toFixed(2)} {invoice.currency}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Zahlungsbedingungen & Hinweise */}
      {(invoice.payment_terms || invoice.notes) && (
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900">Weitere Angaben</h2>
          {invoice.payment_terms && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-700 mb-1">Zahlungsbedingungen:</p>
              <p className="text-sm text-gray-900">{invoice.payment_terms}</p>
            </div>
          )}
          {invoice.notes && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-1">Hinweise:</p>
              <p className="text-sm text-gray-900">{invoice.notes}</p>
            </div>
          )}
        </div>
      )}

      {/* GoBD-Informationen */}
      <div className="bg-blue-50 p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">GoBD-Informationen</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600">PDF-Hash (SHA-256):</p>
            <p className="font-mono text-xs break-all">{invoice.pdf_hash}</p>
          </div>
          <div>
            <p className="text-gray-600">TSA-Zeitstempel:</p>
            <p className="font-mono text-xs">
              {invoice.tsa_token?.timestamp || 'N/A'}
            </p>
          </div>
        </div>
        <div className="mt-4 text-xs text-gray-600">
          ✓ PDF/A-3 Format mit eingebettetem ZUGFeRD XML (EN-16931)<br/>
          ✓ RFC3161 Zeitstempel für Revisionssicherheit<br/>
          ✓ Unveränderbare Archivierung nach GoBD
        </div>
      </div>
    </div>
  )
}
