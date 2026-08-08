<template>
  <el-container class="main-layout">
    <el-aside width="240px" class="aside">
      <!-- Logo 区域 -->
      <div class="logo-area">
        <div class="logo-badge">
          <el-icon><Van /></el-icon>
        </div>
        <div class="logo-text">
          <span class="logo-title">智能物流</span>
          <span class="logo-sub">Logistics Platform</span>
        </div>
      </div>
      <!-- 侧边菜单 -->
      <el-scrollbar class="menu-scroll">
        <el-menu
          :default-active="$route.path"
          router
          class="side-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <span>工作台</span>
          </el-menu-item>
          <template v-for="m in menus" :key="m.path">
            <el-menu-item :index="m.path">
              <el-icon><component :is="m.icon" /></el-icon>
              <span>{{ m.title }}</span>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <!-- 顶栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">
              <el-icon style="vertical-align: text-top"><HomeFilled /></el-icon> 首页
            </el-breadcrumb-item>
            <el-breadcrumb-item v-if="$route.meta.title">{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tooltip content="刷新数据" placement="bottom">
            <el-button link :icon="Refresh" class="header-btn" @click="refreshPage" />
          </el-tooltip>
          <el-divider direction="vertical" />
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="34" class="avatar">{{ user?.username?.[0]?.toUpperCase() || 'U' }}</el-avatar>
              <div class="user-meta">
                <span class="username">{{ user?.username || '用户' }}</span>
                <el-tag size="small" :type="roleTagType" effect="light" round class="role-tag">{{ roleName }}</el-tag>
              </div>
              <el-icon class="caret"><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile"><el-icon><User /></el-icon> 个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided><el-icon><SwitchButton /></el-icon> 退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { Refresh } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const user = computed(() => userStore.userInfo)

const roleName = computed(() => ({
  shipper: '货主', carrier: '承运商', driver: '司机', admin: '管理员'
}[userStore.roleCode] || '未认证'))

const roleTagType = computed(() => ({
  shipper: 'primary', carrier: 'success', driver: 'warning', admin: 'danger'
}[userStore.roleCode] || 'info'))

const menus = computed(() => {
  const roles = {
    shipper: [
      { path: '/shipper/requests', title: '运输需求', icon: 'Goods' },
      { path: '/shipper/quotes', title: '报价管理', icon: 'PriceTag' },
      { path: '/shipper/tasks', title: '运输任务', icon: 'Van' }
    ],
    carrier: [
      { path: '/carrier/market', title: '需求广场', icon: 'Shop' },
      { path: '/carrier/quotes', title: '我的报价', icon: 'PriceTag' },
      { path: '/carrier/tasks', title: '运输任务', icon: 'Van' },
      { path: '/carrier/drivers', title: '司机管理', icon: 'User' },
      { path: '/carrier/vehicles', title: '车辆管理', icon: 'Truck' },
      { path: '/carrier/loading-plan', title: '装车推荐', icon: 'Grid' }
    ],
    driver: [
      { path: '/driver/tasks', title: '我的任务', icon: 'Van' },
      { path: '/driver/location', title: '位置上报', icon: 'Location' }
    ],
    admin: [
      { path: '/admin/users', title: '用户管理', icon: 'UserFilled' },
      { path: '/admin/requests', title: '需求管理', icon: 'Goods' },
      { path: '/admin/quotes', title: '报价管理', icon: 'PriceTag' },
      { path: '/admin/tasks', title: '任务管理', icon: 'Van' },
      { path: '/admin/logs', title: '状态日志', icon: 'Document' }
    ]
  }
  return roles[userStore.roleCode] || []
})

const refreshPage = () => window.location.reload()

const handleCommand = async (cmd) => {
  if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
      userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch (e) { /* 取消 */ }
  } else if (cmd === 'profile') {
    ElMessage.info('个人信息页面（开发中）')
  }
}
</script>

<style scoped>
.main-layout { height: 100vh; }

/* === 侧边栏 === */
.aside {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}
.logo-badge {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}
.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}
.logo-title {
  color: #f1f5f9;
  font-size: 16px;
  font-weight: 700;
}
.logo-sub {
  color: #64748b;
  font-size: 10px;
  letter-spacing: 0.5px;
}
.menu-scroll {
  flex: 1;
  overflow-x: hidden;
}
.side-menu {
  border: none;
  background: transparent !important;
  padding: 8px 12px;
}
.side-menu :deep(.el-menu-item) {
  height: 46px;
  line-height: 46px;
  margin-bottom: 4px;
  border-radius: 10px;
  color: #94a3b8;
  font-size: 14px;
  transition: all 0.2s;
}
.side-menu :deep(.el-menu-item:hover) {
  background: rgba(59, 130, 246, 0.1);
  color: #e2e8f0;
}
.side-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* === 顶栏 === */
.header {
  background: #fff;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
  z-index: 10;
}
.header-left { font-size: 14px; }
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-btn { font-size: 18px; color: #64748b; }
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 10px 4px 4px;
  border-radius: 10px;
  transition: background 0.2s;
}
.user-info:hover { background: #f8fafc; }
.avatar {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  font-weight: 600;
  font-size: 14px;
}
.user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.2;
}
.username {
  color: #1e293b;
  font-weight: 600;
  font-size: 13px;
}
.role-tag { transform: scale(0.85); transform-origin: left; }
.caret { color: #94a3b8; font-size: 12px; }

/* === 主内容区 === */
.main {
  background: #f1f5f9;
  padding: 24px;
  overflow: auto;
}
</style>
