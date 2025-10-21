import { Outlet, NavLink } from 'react-router-dom'
import { DocumentTextIcon, HomeIcon, UserGroupIcon } from '@heroicons/react/24/outline'
import ErrorBoundary from './ErrorBoundary'

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-bold text-primary-600">
                Rechnungsgenerator GoBD
              </h1>
              
              <nav className="flex space-x-4">
                <NavLink
                  to="/"
                  className={({ isActive }) =>
                    `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`
                  }
                >
                  <HomeIcon className="h-5 w-5" />
                  <span>Dashboard</span>
                </NavLink>
                
                <NavLink
                  to="/invoices"
                  className={({ isActive }) =>
                    `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`
                  }
                >
                  <DocumentTextIcon className="h-5 w-5" />
                  <span>Rechnungen</span>
                </NavLink>
                
                <NavLink
                  to="/contacts"
                  className={({ isActive }) =>
                    `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`
                  }
                >
                  <UserGroupIcon className="h-5 w-5" />
                  <span>Kontakte</span>
                </NavLink>
              </nav>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Benutzer: Admin
              </span>
              <button
                onClick={() => {
                  localStorage.removeItem('token')
                  window.location.href = '/login'
                }}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Abmelden
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2025 Rechnungsgenerator GoBD - PDF/A-3 mit ZUGFeRD - GoBD-konforme Archivierung
          </p>
        </div>
      </footer>
    </div>
  )
}
