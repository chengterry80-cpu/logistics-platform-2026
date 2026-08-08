<template>
  <div class="page-container">
    <div class="page-header"><h2 class="page-title">需求管理</h2></div>
    <el-card shadow="never">
      <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部">
            <el-option label="待报价" value="pending" />
            <el-option label="已报价" value="quoted" />
            <el-option label="已指派" value="assigned" />
            <el-option label="运输中" value="in_transit" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card shadow="never" style="margin-top:16px">
      <el-table v-loading="loading" :data="listData" stripe>
        <el-table-column prop="request_id" label="编号" width="80" />
        <el-table-column label="货主" width="140">
          <template #default="{ row }">{{ row.shipper?.company_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="cargo_name" label="货物名称" />
        <el-table-column label="重/体" width="130">
          <template #default="{ row }">{{ row.weight }}kg / {{ row.volume }}m³</template>
        </el-table-column>
        <el-table-column label="路线" min-width="220">
          <template #default="{ row }">
            <el-icon><Location /></el-icon> {{ row.origin }}
            <el-icon style="margin:0 6px"><Right /></el-icon>
            <el-icon><MapLocation /></el-icon> {{ row.destination }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" class="status-tag" :type="statusType(row.status)">
              {{ row.status_display || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="view(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pagination" background layout="total, prev, pager, next"
        :total="total" v-model:current-page="page" :page-size="20" @current-change="loadData" />
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { listRequests } from '@/api'

const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const filters = reactive({ status: '' })

const statusType = (s) => ({
  pending: 'warning', quoted: 'primary', assigned: 'primary',
  in_transit: 'info', completed: 'success', cancelled: 'info'
}[s] || 'info')

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, ...filters }
    const res = await listRequests(params)
    listData.value = res?.results || res || []
    total.value = res?.count || listData.value.length
  } finally { loading.value = false }
}

const view = (row) => ElMessageBox.alert(JSON.stringify(row, null, 2), '需求详情')
onMounted(loadData)
</script>

<style scoped>
.filter-form { margin-bottom: 0; }
.pagination { margin-top: 20px; justify-content: flex-end; display: flex; }
</style>
