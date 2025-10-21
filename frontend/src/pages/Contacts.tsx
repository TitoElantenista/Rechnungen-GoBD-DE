import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { contactAPI } from '../services/api'
import { ContactList } from '../types/contact'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Contacts() {
  const navigate = useNavigate()
  const [contacts, setContacts] = useState<ContactList[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('all')

  const loadContacts = async () => {
    try {
      setLoading(true)
      setError(null)
      const params: any = {}
      
      if (searchTerm) {
        params.q = searchTerm
      }
      
      if (filterType !== 'all') {
        params.contact_type = filterType
      }
      
      const data = await contactAPI.list(params)
      setContacts(data)
    } catch (err: any) {
      console.error('Error loading contacts:', err)
      setError(err.response?.data?.detail || 'Fehler beim Laden der Kontakte')
      setContacts([]) // Clear contacts on error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Debounce search to avoid too many requests
    const timeoutId = setTimeout(() => {
      loadContacts()
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [searchTerm, filterType])

  const handleDelete = async (id: number) => {
    if (!confirm('Möchten Sie diesen Kontakt wirklich löschen?')) {
      return
    }

    try {
      await contactAPI.delete(id)
      loadContacts()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen des Kontakts')
    }
  }

  const getContactTypeLabel = (type: string) => {
    switch (type) {
      case 'customer':
        return '👤 Kunde'
      case 'supplier':
        return '🏢 Lieferant'
      case 'both':
        return '🔄 Beide'
      default:
        return type
    }
  }

  const getDisplayName = (contact: ContactList) => {
    if (contact.company_name && contact.contact_person) {
      return `${contact.company_name} (${contact.contact_person})`
    }
    return contact.company_name || contact.contact_person || 'Unbekannt'
  }

  if (loading && contacts.length === 0) {
    return <LoadingSpinner message="Kontakte werden geladen..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Kontakte</h1>
          <p className="text-gray-600 mt-1">Verwalten Sie Ihre Kunden und Lieferanten</p>
        </div>
        <button
          onClick={() => navigate('/contacts/create')}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
        >
          ➕ Neuer Kontakt
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Search and Filter */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🔍 Suche
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Name, Email, Steuernummer..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🏷️ Typ
            </label>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">Alle</option>
              <option value="customer">Kunden</option>
              <option value="supplier">Lieferanten</option>
              <option value="both">Beide</option>
            </select>
          </div>
        </div>
      </div>

      {/* Contacts List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {contacts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">Keine Kontakte gefunden</p>
            <p className="text-sm mt-2">Erstellen Sie Ihren ersten Kontakt</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Typ
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stadt
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Telefon
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Aktionen
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {contacts.map((contact) => (
                  <tr
                    key={contact.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/contacts/${contact.id}`)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {getContactTypeLabel(contact.contact_type)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {getDisplayName(contact)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {contact.city}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {contact.email || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {contact.phone || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          contact.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {contact.is_active ? 'Aktiv' : 'Inaktiv'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/contacts/${contact.id}/edit`)
                        }}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        ✏️ Bearbeiten
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(contact.id)
                        }}
                        className="text-red-600 hover:text-red-900"
                      >
                        🗑️ Löschen
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <p className="text-sm text-gray-600">
          Insgesamt <span className="font-semibold">{contacts.length}</span> Kontakte gefunden
        </p>
      </div>
    </div>
  )
}
