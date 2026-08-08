<template>
  <div class="page-container">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-group">
        <h2 class="page-title">状态日志</h2>
        <p class="page-subtitle">追踪所有业务对象的状态流转记录</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="对象类型">
          <el-select v-model="filters.object_type" clearable placeholder="全部" style="width:140px">
            <el-option label="运输需求" value="request" />
            <el-option label="报价" value="quote" />
            <el-option label="运输任务" value="task" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="filters.actor" clearable placeholder="用户名" style="width:160px" />
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
        <el-table-column prop="log_id" label="编号" width="80" align="center">
          <template #default="{ row }">
            <span style="color:#94a3b8;font-weight:500">#{{ row.log_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="对象" min-width="200">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" round>{{ row.model_name || row.object_type }}</el-tag>
            <span style="margin-left:8px;color:#94a3b8;font-weight:500">#{{ row.object_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态流转" min-width="240">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:6px">
              <el-tag size="small" effect="light" round type="info">{{ row.old_status || row.from_state || '初始' }}</el-tag>
              <el-icon style="color:#3b82f6"><ArrowRight /></el-icon>
              <el-tag size="small" effect="light" round type="success">{{ row.new_status || row.to_state || '-' }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="transition" label="操作" width="130">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ row.transition || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="操作人" width="130">
          <template #default="{ row }">
            <div style="font-weight:500;color:#1e293b">{{ row.changed_by || row.actor || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="160">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ row.remark || row.note || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ formatTime(row.changed_at || row.timestamp) }}</div>
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
import { listStateLogs } from '@/api'
import dayjs from 'dayjs'

const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const filters = reactive({ object_type: '', actor: '' })

const formatTime = (t) => t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-'

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, ...filters }
    const res = await listStateLogs(params)
    listData.value = res?.results || res || []
    total.value = res?.count || listData.value.length
  } finally { loading.value = false }
}

onMounted(loadData)
</script>

<style scoped>
</style>
