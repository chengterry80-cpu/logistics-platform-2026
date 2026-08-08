import { defineStore } from 'pinia'
import { login as apiLogin, getMe } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: '',
    refreshToken: '',
    userInfo: null,
    roleCode: ''  // shipper / carrier / driver / admin
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isShipper: (state) => state.roleCode === 'shipper',
    isCarrier: (state) => state.roleCode === 'carrier',
    isDriver: (state) => state.roleCode === 'driver',
    isAdmin: (state) => state.roleCode === 'admin'
  },
  actions: {
    async login(formData) {
      const res = await apiLogin(formData)
      this.token = res.access
      this.refreshToken = res.refresh
      await this.fetchUserInfo()
      return this.userInfo
    },
    async fetchUserInfo() {
      const user = await getMe()
      this.userInfo = user
      this.roleCode = user?.role_code || ''
      return user
    },
    logout() {
      this.token = ''
      this.refreshToken = ''
      this.userInfo = null
      this.roleCode = ''
    }
  },
  persist: {
    key: 'logistics_user',
    paths: ['token', 'refreshToken', 'userInfo', 'roleCode']
  }
})
