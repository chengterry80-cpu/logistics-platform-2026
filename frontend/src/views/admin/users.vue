<template>
  <div class="page-container">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-group">
        <h2 class="page-title">用户管理</h2>
        <p class="page-subtitle">管理平台所有用户账号与角色权限</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="角色">
          <el-select v-model="filters.role_code" clearable placeholder="全部" style="width: 130px">
            <el-option label="货主" value="shipper" />
            <el-option label="承运商" value="carrier" />
            <el-option label="司机" value="driver" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="filters.username" clearable placeholder="搜索用户名" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>&nbsp;查询
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table v-loading="loading" :data="listData" stripe style="width: 100%"
        :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: 600 }">
        <el-table-column prop="id" label="编号" width="80" align="center">
          <template #default="{ row }">
            <span style="color:#94a3b8;font-weight:500">#{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="140">
          <template #default="{ row }">
            <div style="font-weight:500;color:#1e293b">{{ row.username }}</div>
          </template>
        </el-table-column>
        <el-table-column label="姓名/公司" min-width="160">
          <template #default="{ row }">
            <div style="font-weight:500;color:#1e293b">{{ row.full_name || row.shipper?.company_name || row.carrier?.company_name || row.driver?.name || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="联系方式" width="180">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ row.phone || row.shipper?.contact_phone || row.carrier?.contact_phone || row.driver?.phone || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" round :type="roleType(row.role_code)">
              {{ row.role_name || roleName(row.role_code) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag class="status-tag" size="small" effect="light" round
              :type="row.is_active ? 'success' : 'danger'">
              {{ row.status_display || (row.is_active ? '启用' : '禁用') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date_joined" label="注册时间" width="170">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ formatTime(row.date_joined) }}</div>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        class="pagination"
        background
        layout="total, prev, pager, next"
        :total="total"
        v-model:current-page="page"
        :page-size="20"
        @current-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { listUsers } from '@/api'
import dayjs from 'dayjs'

const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const filters = reactive({ role_code: '', username: '' })

const roleName = (r) => ({ shipper: '货主', carrier: '承运商', driver: '司机', admin: '管理员' }[r] || '-')
const roleType = (r) => ({ shipper: 'primary', carrier: 'success', driver: 'warning', admin: 'danger' }[r] || 'info')
const formatTime = (t) => t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-'

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, ...filters }
    const res = await listUsers(params)
    listData.value = res?.results || res || []
    total.value = res?.count || listData.value.length
  } finally { loading.value = false }
}

onMounted(loadData)
</script>

<style scoped>
</style>
