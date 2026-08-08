<template>
  <div class="page-container">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-group">
        <h2 class="page-title">运输需求</h2>
        <p class="page-subtitle">管理您发布的所有货物运输需求，跟踪报价与指派状态</p>
      </div>
      <el-button type="primary" size="default" round @click="$router.push('/shipper/requests/new')">
        <el-icon><Plus /></el-icon>&nbsp;发布需求
      </el-button>
    </div>

    <!-- 统计概览 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <el-card class="stat-card" shadow="never">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div class="stat-label">{{ card.label }}</div>
              <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
            </div>
            <div class="stat-icon-wrap" :style="{ background: card.bg }">
              <el-icon><component :is="card.icon" /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 130px">
            <el-option label="待报价" value="pending" />
            <el-option label="已报价" value="quoted" />
            <el-option label="已指派" value="assigned" />
            <el-option label="运输中" value="in_transit" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="货物">
          <el-input v-model="filters.cargo_name" clearable placeholder="货物名称" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>&nbsp;查询
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table v-loading="loading" :data="listData" stripe style="width: 100%"
        :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: 600 }">
        <el-table-column prop="request_id" label="编号" width="70" align="center">
          <template #default="{ row }">
            <span style="color:#94a3b8;font-weight:500">#{{ row.request_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="cargo_name" label="货物名称" min-width="140">
          <template #default="{ row }">
            <div style="font-weight:500;color:#1e293b">{{ row.cargo_name }}</div>
            <el-tag size="small" effect="plain" style="margin-top:2px">{{ row.cargo_type_display || row.cargo_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="规格" width="130">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">
              <div><el-icon><ScaleToOriginal /></el-icon> {{ row.weight }} 吨</div>
              <div><el-icon><Box /></el-icon> {{ row.volume }} m³</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="运输路线" min-width="260">
          <template #default="{ row }">
            <div class="route-cell">
              <span class="route-point"><el-icon color="#3b82f6"><Location /></el-icon>{{ row.origin }}</span>
              <el-icon class="route-arrow"><Right /></el-icon>
              <span class="route-point"><el-icon color="#ef4444"><MapLocation /></el-icon>{{ row.destination }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="expected_time" label="期望送达" width="170">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ formatTime(row.expected_time) }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag class="status-tag" :type="statusType(row.status)" effect="light" round>
              {{ row.status_display || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">详情</el-button>
            <el-button link type="success" size="small" @click="viewQuotes(row)" v-if="row.status==='quoted'">查看报价</el-button>
            <el-popconfirm title="确定取消该需求?" @confirm="cancelRequest(row)" v-if="row.status==='pending'||row.status==='quoted'">
              <template #reference>
                <el-button link type="danger" size="small">取消</el-button>
              </template>
            </el-popconfirm>
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

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="需求详情" width="560px">
      <el-descriptions v-if="currentRow" :column="2" border size="default">
        <el-descriptions-item label="需求编号">#{{ currentRow.request_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(currentRow.status)" size="small">{{ currentRow.status_display }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="货物名称">{{ currentRow.cargo_name }}</el-descriptions-item>
        <el-descriptions-item label="货物类型">{{ currentRow.cargo_type_display }}</el-descriptions-item>
        <el-descriptions-item label="重量">{{ currentRow.weight }} 吨</el-descriptions-item>
        <el-descriptions-item label="体积">{{ currentRow.volume }} m³</el-descriptions-item>
        <el-descriptions-item label="起始地">{{ currentRow.origin }}</el-descriptions-item>
        <el-descriptions-item label="目的地">{{ currentRow.destination }}</el-descriptions-item>
        <el-descriptions-item label="期望送达" :span="2">{{ formatTime(currentRow.expected_time) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { listRequests, cancelRequest as apiCancel } from '@/api'

const router = useRouter()
const listData = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const detailVisible = ref(false)
const currentRow = ref(null)

const filters = reactive({ status: '', cargo_name: '' })

const statusType = (s) => ({
  pending: 'warning', quoted: 'primary', assigned: 'primary',
  in_transit: 'info', completed: 'success', cancelled: 'info'
}[s] || 'info')

const formatTime = (t) => t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-'

const statCards = computed(() => {
  const counts = { pending: 0, quoted: 0, in_transit: 0, completed: 0 }
  listData.value.forEach(r => { if (counts[r.status] !== undefined) counts[r.status]++ })
  return [
    { label: '待报价', value: counts.pending, icon: 'Clock', color: '#e6a23c', bg: 'linear-gradient(135deg,#f59e0b,#f97316)' },
    { label: '已报价', value: counts.quoted, icon: 'PriceTag', color: '#3b82f6', bg: 'linear-gradient(135deg,#3b82f6,#06b6d4)' },
    { label: '运输中', value: counts.in_transit, icon: 'Van', color: '#8b5cf6', bg: 'linear-gradient(135deg,#8b5cf6,#6366f1)' },
    { label: '已完成', value: counts.completed, icon: 'CircleCheck', color: '#22c55e', bg: 'linear-gradient(135deg,#22c55e,#10b981)' },
  ]
})

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value, ...filters }
    const res = await listRequests(params)
    listData.value = res?.results || res || []
    total.value = res?.count || listData.value.length
  } finally { loading.value = false }
}

const resetFilter = () => {
  filters.status = ''; filters.cargo_name = ''; page.value = 1; loadData()
}

const cancelRequest = async (row) => {
  await apiCancel(row.request_id)
  ElMessage.success('已取消')
  loadData()
}

const viewDetail = (row) => { currentRow.value = row; detailVisible.value = true }
const viewQuotes = (row) => router.push({ path: '/shipper/quotes', query: { request: row.request_id } })

onMounted(loadData)
</script>

<style scoped>
.stat-row { margin-bottom: 16px; }
.stat-card { margin-bottom: 0; }
</style>
