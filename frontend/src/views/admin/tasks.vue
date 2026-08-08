<template>
  <div class="page-container">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-group">
        <h2 class="page-title">任务管理</h2>
        <p class="page-subtitle">监控全平台运输任务状态与异常</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filters.task_status" clearable placeholder="全部" style="width: 130px">
            <el-option label="待指派" value="pending" />
            <el-option label="已指派" value="assigned" />
            <el-option label="运输中" value="in_transit" />
            <el-option label="已送达" value="delivered" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
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
        <el-table-column prop="task_id" label="编号" width="80" align="center">
          <template #default="{ row }">
            <span style="color:#94a3b8;font-weight:500">#{{ row.task_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="货物" min-width="140">
          <template #default="{ row }">
            <div style="font-weight:500;color:#1e293b">{{ row.cargo_name || row.request?.cargo_name || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="运输路线" min-width="260">
          <template #default="{ row }">
            <div class="route-cell">
              <span class="route-point"><el-icon color="#3b82f6"><Location /></el-icon>{{ row.origin || row.request?.origin || '-' }}</span>
              <el-icon class="route-arrow"><Right /></el-icon>
              <span class="route-point"><el-icon color="#ef4444"><MapLocation /></el-icon>{{ row.destination || row.request?.destination || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="司机/车牌" width="160">
          <template #default="{ row }">
            <div style="font-weight:500;color:#1e293b">{{ row.driver?.name || '-' }}</div>
            <div style="font-size:12px;color:#94a3b8;margin-top:2px">{{ row.vehicle_plate || row.vehicle?.plate_number || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="current_location" label="当前位置" width="140">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ row.current_location || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="任务状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag class="status-tag" size="small" effect="light" round :type="statusType(row.task_status)">
              {{ row.task_status_display || row.task_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="付款" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" round :type="row.payment_status==='paid'?'success':'warning'">
              {{ row.payment_status_display || row.payment_status || '未付' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="异常" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_anomaly" type="danger" size="small" effect="light" round>异常</el-tag>
            <span v-else style="color:#cbd5e1">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="view(row)">详情</el-button>
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
import { ElMessageBox } from 'element-plus'
import { listTasks } from '@/api'

const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const filters = reactive({ task_status: '' })

const statusType = (s) => ({
  pending: 'warning', assigned: 'primary', in_transit: 'primary',
  delivered: 'warning', completed: 'success', cancelled: 'info'
}[s] || 'info')

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, ...filters }
    const res = await listTasks(params)
    listData.value = res?.results || res || []
    total.value = res?.count || listData.value.length
  } finally { loading.value = false }
}

const view = (row) => ElMessageBox.alert(JSON.stringify(row, null, 2), '任务详情')
onMounted(loadData)
</script>

<style scoped>
</style>
