import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { PlusIcon, DocumentTextIcon } from '@heroicons/react/24/outline'
import { invoiceAPI } from '../services/api'

export default function Dashboard() {
  const currentYear = new Date().getFullYear()
  
  const { data: recentInvoices } = useQuery({
    queryKey: ['invoices', 'recent'],
    queryFn: () => invoiceAPI.list({ limit: 5 }),
  })

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Willkommen im Rechnungsgenerator
        </h2>
        <p className="text-gray-600">
          GoBD-konforme Rechnungsverwaltung mit PDF/A-3 + ZUGFeRD
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Link
          to="/invoices/new"
          className="card hover:shadow-lg transition-shadow border-2 border-primary-200 hover:border-primary-300"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Neue Rechnung
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Rechnung erstellen
              </p>
            </div>
            <PlusIcon className="h-8 w-8 text-primary-600" />
          </div>
        </Link>

        <Link
          to="/invoices"
          className="card hover:shadow-lg transition-shadow"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Alle Rechnungen
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Liste durchsuchen
              </p>
            </div>
            <DocumentTextIcon className="h-8 w-8 text-gray-600" />
          </div>
        </Link>

        <div className="card bg-primary-50">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Jahr {currentYear}
          </h3>
          <p className="text-3xl font-bold text-primary-600">
            {recentInvoices?.length || 0}
          </p>
          <p className="text-sm text-gray-600 mt-1">Rechnungen</p>
        </div>
      </div>

      {/* Recent Invoices */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Aktuelle Rechnungen
          </h3>
          <Link
            to="/invoices"
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            Alle anzeigen →
          </Link>
        </div>

        {recentInvoices && recentInvoices.length > 0 ? (
          <div className="space-y-3">
            {recentInvoices.map((invoice: any) => (
              <Link
                key={invoice.id}
                to={`/invoices/${invoice.id}`}
                className="block p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">
                      {invoice.invoice_number}
                    </p>
                    <p className="text-sm text-gray-600">
                      {invoice.buyer_name}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900">
                      {invoice.gross_total.toFixed(2)} {invoice.currency}
                    </p>
                    <p className="text-sm text-gray-600">
                      {new Date(invoice.issue_date).toLocaleDateString('de-DE')}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-center text-gray-500 py-8">
            Noch keine Rechnungen vorhanden
          </p>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">
          ℹ️ GoBD-Konformität
        </h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>✓ PDF/A-3 mit eingebettetem ZUGFeRD XML (EN-16931)</li>
          <li>✓ RFC3161 Zeitstempel für Revisionssicherheit</li>
          <li>✓ Unveränderbare Archivierung mit Versionierung</li>
          <li>✓ Vollständige Audit-Logs aller Aktionen</li>
          <li>✓ Lückenlose, fortlaufende Rechnungsnummern</li>
        </ul>
      </div>
    </div>
  )
}
