<template>
  <div class="page-container">
    <div class="page-header"><h2 class="page-title">报价管理</h2></div>
    <el-card shadow="never">
      <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部">
            <el-option label="待确认" value="pending" />
            <el-option label="已接受" value="accepted" />
            <el-option label="已拒绝" value="rejected" />
            <el-option label="已过期" value="expired" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card shadow="never" style="margin-top:16px">
      <el-table v-loading="loading" :data="listData" stripe>
        <el-table-column prop="quote_id" label="编号" width="80" />
        <el-table-column prop="request_id" label="需求编号" width="100" />
        <el-table-column label="承运商" width="160">
          <template #default="{ row }">{{ row.carrier?.company_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="报价(元)" width="110">
          <template #default="{ row }">
            <span style="color:#f56c6c;font-weight:600">¥ {{ Number(row.amount).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)" class="status-tag">
              {{ row.status_display || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="validity_period" label="有效期" width="160" />
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
import { listQuotes } from '@/api'

const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const filters = reactive({ status: '' })

const statusType = (s) => ({
  pending: 'warning', accepted: 'success', rejected: 'danger', expired: 'info'
}[s] || 'info')

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, ...filters }
    const res = await listQuotes(params)
    listData.value = res?.results || res || []
    total.value = res?.count || listData.value.length
  } finally { loading.value = false }
}
const view = (row) => ElMessageBox.alert(JSON.stringify(row, null, 2), '报价详情')

onMounted(loadData)
</script>

<style scoped>
.filter-form { margin-bottom: 0; }
.pagination { margin-top: 20px; justify-content: flex-end; display: flex; }
</style>
