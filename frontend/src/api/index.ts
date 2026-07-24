const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

// 请求拦截: 自动带 token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('huopan_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截: 401 弹窗提示 (不强制跳转, 避免误触)
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 不自动清 token 跳登录, 弹窗让用户确认
      ElMessage.warning('登录已过期, 请重新登录')
      import('element-plus').then(({ ElMessageBox }) => {
        ElMessageBox.confirm('登录已过期, 是否重新登录?', '提示', {
          confirmButtonText: '登录',
          cancelButtonText: '取消',
          type: 'warning',
        }).then(() => {
          localStorage.removeItem('huopan_token')
          localStorage.removeItem('huopan_user')
          window.location.href = '/login'
        }).catch(() => {})
      })
      // 不 reject 让调用方 catch 不到
      return Promise.reject(error)
    }
    return Promise.reject(error)
  }
)

// 产品 API
export const productsApi = {
  list: (params: Record<string, any>) => http.get('/products', { params }),
  get: (id: number) => http.get(`/products/${id}`),
  create: (data: Record<string, any>) => http.post('/products', data),
  update: (id: number, data: Record<string, any>) => http.put(`/products/${id}`, data),
  delete: (id: number) => http.delete(`/products/${id}`),
  batchUpdate: (ids: number[], updates: Record<string, any>) =>
    http.post('/products/batch', { ids, updates }),
  uploadImages: (id: number, files: File[]) => {
    const formData = new FormData()
    files.forEach((f) => formData.append('files', f))
    return http.post(`/products/${id}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteImage: (productId: number, imageId: number) =>
    http.delete(`/products/${productId}/images/${imageId}`),
  categories: () => http.get('/products/meta/categories'),
  importTemplate: () => `${API_BASE}/products/import/template`,
  importProducts: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return http.post('/products/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

// 客户 API
export const customersApi = {
  list: (params?: Record<string, any>) => http.get('/customers', { params }),
  create: (data: Record<string, any>) => http.post('/customers', data),
  update: (id: number, data: Record<string, any>) => http.put(`/customers/${id}`, data),
  delete: (id: number) => http.delete(`/customers/${id}`),
  levels: () => http.get('/customers/levels'),
  createLevel: (data: Record<string, any>) => http.post('/customers/levels', data),
  updateLevel: (id: number, data: Record<string, any>) => http.put(`/customers/levels/${id}`, data),
  deleteLevel: (id: number) => http.delete(`/customers/levels/${id}`),
}

// 认证 API
export const authApi = {
  login: (username: string, password: string) =>
    http.post('/auth/login', { username, password }),
  me: () => http.get('/auth/me'),
  initAdmin: () => http.post('/auth/init-admin'),
  listUsers: () => http.get('/auth/users'),
  updateUser: (id: number, data: Record<string, any>) => http.put(`/auth/users/${id}`, data),
  toggleActive: (id: number) => http.post(`/auth/users/${id}/toggle-active`),
  createUser: (data: Record<string, any>) => http.post('/auth/users', data),
  listLogs: (params: Record<string, any>) => http.get('/logs', { params }),
  listDicts: (type: string) => http.get(`/dicts/${type}`),
  createDict: (type: string, data: Record<string, any>) => http.post(`/dicts/${type}`, data),
  deleteDict: (type: string, id: number) => http.delete(`/dicts/${type}/${id}`),
}

// 货盘 API
export const catalogsApi = {
  list: (params?: Record<string, any>) => http.get('/catalogs', { params }),
  create: (data: Record<string, any>) => http.post('/catalogs', data),
  update: (id: number, data: Record<string, any>) => http.put(`/catalogs/${id}`, data),
  delete: (id: number) => http.delete(`/catalogs/${id}`),
  batchCreate: (data: Record<string, any>) => http.post('/catalogs/batch', data),
  priceHistory: (productId: number) => http.get(`/catalogs/price-history/${productId}`),
}

// 导出 API
export const exportApi = {
  catalogExcelUrl: (catalogName: string, customerId?: number) => {
    const base = `${API_BASE}/export/catalog/${encodeURIComponent(catalogName)}/excel`
    return customerId ? `${base}?customer_id=${customerId}` : base
  },
  catalogImagesUrl: (catalogName: string, customerId?: number) => {
    const base = `${API_BASE}/export/catalog/${encodeURIComponent(catalogName)}/images`
    return customerId ? `${base}?customer_id=${customerId}` : base
  },
}

export const UPLOAD_BASE = ''
