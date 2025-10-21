import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import InvoiceList from './pages/InvoiceList'
import InvoiceCreate from './pages/InvoiceCreate'
import InvoiceDetail from './pages/InvoiceDetail'
import Contacts from './pages/Contacts'
import ContactForm from './pages/ContactForm'
import Login from './pages/Login'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="invoices" element={<InvoiceList />} />
        <Route path="invoices/create" element={<InvoiceCreate />} />
        <Route path="invoices/new" element={<InvoiceCreate />} />
        <Route path="invoices/:id" element={<InvoiceDetail />} />
        <Route path="contacts" element={<Contacts />} />
        <Route path="contacts/create" element={<ContactForm />} />
        <Route path="contacts/:id/edit" element={<ContactForm />} />
      </Route>
    </Routes>
  )
}

export default App
