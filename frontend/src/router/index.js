import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'HomeFilled' }
      },
      // ========== 货主端 ==========
      {
        path: 'shipper/requests',
        name: 'ShipperRequests',
        component: () => import('@/views/shipper/requests.vue'),
        meta: { title: '运输需求', roles: ['shipper'], icon: 'Goods' }
      },
      {
        path: 'shipper/requests/new',
        name: 'ShipperRequestNew',
        component: () => import('@/views/shipper/request-form.vue'),
        meta: { title: '发布需求', roles: ['shipper'], hidden: true }
      },
      {
        path: 'shipper/quotes',
        name: 'ShipperQuotes',
        component: () => import('@/views/shipper/quotes.vue'),
        meta: { title: '报价管理', roles: ['shipper'], icon: 'PriceTag' }
      },
      {
        path: 'shipper/tasks',
        name: 'ShipperTasks',
        component: () => import('@/views/shipper/tasks.vue'),
        meta: { title: '运输任务', roles: ['shipper'], icon: 'Van' }
      },
      // ========== 承运商端 ==========
      {
        path: 'carrier/market',
        name: 'CarrierMarket',
        component: () => import('@/views/carrier/market.vue'),
        meta: { title: '需求广场', roles: ['carrier'], icon: 'Shop' }
      },
      {
        path: 'carrier/quotes',
        name: 'CarrierQuotes',
        component: () => import('@/views/carrier/quotes.vue'),
        meta: { title: '我的报价', roles: ['carrier'], icon: 'PriceTag' }
      },
      {
        path: 'carrier/tasks',
        name: 'CarrierTasks',
        component: () => import('@/views/carrier/tasks.vue'),
        meta: { title: '运输任务', roles: ['carrier'], icon: 'Van' }
      },
      {
        path: 'carrier/drivers',
        name: 'CarrierDrivers',
        component: () => import('@/views/carrier/drivers.vue'),
        meta: { title: '司机管理', roles: ['carrier'], icon: 'User' }
      },
      {
        path: 'carrier/vehicles',
        name: 'CarrierVehicles',
        component: () => import('@/views/carrier/vehicles.vue'),
        meta: { title: '车辆管理', roles: ['carrier'], icon: 'Truck' }
      },
      {
        path: 'carrier/loading-plan',
        name: 'CarrierLoadingPlan',
        component: () => import('@/views/carrier/loading-plan.vue'),
        meta: { title: '装车推荐', roles: ['carrier'], icon: 'Grid' }
      },
      // ========== 司机端 ==========
      {
        path: 'driver/tasks',
        name: 'DriverTasks',
        component: () => import('@/views/driver/tasks.vue'),
        meta: { title: '我的任务', roles: ['driver'], icon: 'Van' }
      },
      {
        path: 'driver/location',
        name: 'DriverLocation',
        component: () => import('@/views/driver/location.vue'),
        meta: { title: '位置上报', roles: ['driver'], icon: 'Location' }
      },
      // ========== 管理员端 ==========
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/users.vue'),
        meta: { title: '用户管理', roles: ['admin'], icon: 'UserFilled' }
      },
      {
        path: 'admin/requests',
        name: 'AdminRequests',
        component: () => import('@/views/admin/requests.vue'),
        meta: { title: '需求管理', roles: ['admin'], icon: 'Goods' }
      },
      {
        path: 'admin/quotes',
        name: 'AdminQuotes',
        component: () => import('@/views/admin/quotes.vue'),
        meta: { title: '报价管理', roles: ['admin'], icon: 'PriceTag' }
      },
      {
        path: 'admin/tasks',
        name: 'AdminTasks',
        component: () => import('@/views/admin/tasks.vue'),
        meta: { title: '任务管理', roles: ['admin'], icon: 'Van' }
      },
      {
        path: 'admin/logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/logs.vue'),
        meta: { title: '状态日志', roles: ['admin'], icon: 'Document' }
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const userStore = useUserStore()
  if (to.meta.public) return true
  if (!userStore.isLoggedIn) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.meta.roles && !to.meta.roles.includes(userStore.roleCode)) {
    return { path: '/dashboard' }
  }
  return true
})

export default router
