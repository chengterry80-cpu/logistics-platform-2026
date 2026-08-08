import request from './request'

// ========================================================
// 认证 API
// ========================================================
export const login = (data) => request.post('/token/', data)
export const refreshToken = (data) => request.post('/token/refresh/', data)
export const register = (data) => request.post('/auth/register/', data)
export const getMe = () => request.get('/auth/me/')

// ========================================================
// 运输需求 API (ShippingRequest)
// ========================================================
export const listRequests = (params) => request.get('/shipping-requests/', { params })
export const getRequest = (id) => request.get(`/shipping-requests/${id}/`)
export const createRequest = (data) => request.post('/shipping-requests/', data)
export const updateRequest = (id, data) => request.put(`/shipping-requests/${id}/`, data)
export const deleteRequest = (id) => request.delete(`/shipping-requests/${id}/`)
export const cancelRequest = (id) => request.post(`/shipping-requests/${id}/cancel/`)
export const confirmQuoteRequest = (id, data) => request.post(`/shipping-requests/${id}/confirm-quote/`, data)

// ========================================================
// 报价 API (Quote)
// ========================================================
export const listQuotes = (params) => request.get('/quotes/', { params })
export const getQuote = (id) => request.get(`/quotes/${id}/`)
export const createQuote = (data) => request.post('/quotes/', data)
export const acceptQuote = (id) => request.post(`/quotes/${id}/accept/`)
export const rejectQuote = (id) => request.post(`/quotes/${id}/reject/`)

// ========================================================
// 运输任务 API (TransportTask)
// ========================================================
export const listTasks = (params) => request.get('/transport-tasks/', { params })
export const getTask = (id) => request.get(`/transport-tasks/${id}/`)
export const assignTask = (id, data) => request.post(`/transport-tasks/${id}/assign/`, data)
export const acceptTask = (id) => request.post(`/transport-tasks/${id}/accept/`)
export const deliverTask = (id) => request.post(`/transport-tasks/${id}/deliver/`)
export const completeTask = (id) => request.post(`/transport-tasks/${id}/complete/`)
export const cancelTask = (id) => request.post(`/transport-tasks/${id}/cancel/`)
export const updateTaskLocation = (id, data) => request.put(`/transport-tasks/${id}/location/`, data)
export const reportTaskAnomaly = (id, data) => request.post(`/transport-tasks/${id}/report-anomaly/`, data)
export const confirmTaskPayment = (id) => request.post(`/transport-tasks/${id}/confirm-payment/`)

// ========================================================
// 车辆 API (Vehicle)
// ========================================================
export const listVehicles = (params) => request.get('/vehicles/', { params })
export const getVehicle = (id) => request.get(`/vehicles/${id}/`)
export const createVehicle = (data) => request.post('/vehicles/', data)
export const updateVehicle = (id, data) => request.put(`/vehicles/${id}/`, data)
export const deleteVehicle = (id) => request.delete(`/vehicles/${id}/`)

// ========================================================
// 用户 API
// ========================================================
export const listUsers = (params) => request.get('/users/', { params })
export const getUser = (id) => request.get(`/users/${id}/`)
export const listShippers = (params) => request.get('/shippers/', { params })
export const listCarriers = (params) => request.get('/carriers/', { params })
export const listDrivers = (params) => request.get('/drivers/', { params })
export const createDriver = (data) => request.post('/drivers/', data)

// ========================================================
// 状态日志 API
// ========================================================
export const listStateLogs = (params) => request.get('/state-logs/', { params })

// ========================================================
// 装车推荐 API
// ========================================================
export const generateLoadingPlan = (data) => request.post('/loading-plan/generate/', data)
export const getLoadingPlanResult = (taskId) => request.get(`/loading-plan/result/${taskId}/`)
