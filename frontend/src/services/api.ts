import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: async (username: string, password: string) => {
    const response = await api.post('/api/auth/login', { username, password })
    return response.data
  },
}

// Invoice API
export const invoiceAPI = {
  list: async (params?: {
    year?: number
    q?: string
    status?: string
    page?: number
    limit?: number
  }) => {
    const response = await api.get('/api/invoices', { params })
    return response.data
  },

  get: async (id: number) => {
    const response = await api.get(`/api/invoices/${id}`)
    return response.data
  },

  create: async (data: any) => {
    const response = await api.post('/api/invoices', data)
    return response.data
  },

  preview: async (id: number) => {
    const response = await api.get(`/api/invoices/${id}/preview`, {
      responseType: 'blob',
    })
    return response.data
  },

  download: async (id: number) => {
    const response = await api.get(`/api/invoices/${id}/download`, {
      responseType: 'blob',
    })
    return response.data
  },

  cancel: async (id: number, reason: string) => {
    const response = await api.delete(`/api/invoices/${id}`, {
      params: { reason },
    })
    return response.data
  },
}

// Contact API
export const contactAPI = {
  list: async (params?: {
    contact_type?: string
    q?: string
    active_only?: boolean
    page?: number
    limit?: number
  }) => {
    const response = await api.get('/api/contacts', { params })
    return response.data
  },

  get: async (id: number) => {
    const response = await api.get(`/api/contacts/${id}`)
    return response.data
  },

  create: async (data: any) => {
    const response = await api.post('/api/contacts', data)
    return response.data
  },

  update: async (id: number, data: any) => {
    const response = await api.put(`/api/contacts/${id}`, data)
    return response.data
  },

  delete: async (id: number) => {
    const response = await api.delete(`/api/contacts/${id}`)
    return response.data
  },
}
