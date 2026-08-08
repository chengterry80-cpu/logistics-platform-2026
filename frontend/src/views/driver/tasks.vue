<template>
  <div class="page-container">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-group">
        <h2 class="page-title">我的任务</h2>
        <p class="page-subtitle">查看分配给你的运输任务，更新运输状态</p>
      </div>
      <el-tag :type="statusCount > 0 ? 'success' : 'info'" effect="light" round size="large">
        当前在途任务: {{ statusCount }}
      </el-tag>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filters.task_status" clearable placeholder="全部" style="width: 130px">
            <el-option label="已指派" value="assigned" />
            <el-option label="运输中" value="in_transit" />
            <el-option label="已送达" value="delivered" />
            <el-option label="已完成" value="completed" />
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
        <el-table-column label="货物" width="140">
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
        <el-table-column label="期望送达" width="170">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ formatTime(row.expected_time || row.request?.expected_time) }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="current_location" label="当前位置" width="150">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ row.current_location || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag class="status-tag" size="small" effect="light" round :type="statusType(row.task_status)">
              {{ row.task_status_display || row.task_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="view(row)">详情</el-button>
            <el-popconfirm title="开始运输?" @confirm="start(row)" v-if="row.task_status==='assigned'">
              <template #reference><el-button link type="primary" size="small">开始运输</el-button></template>
            </el-popconfirm>
            <el-button link type="warning" size="small" @click="updateLoc(row)" v-if="row.task_status==='in_transit'">更新位置</el-button>
            <el-popconfirm title="确认货物已送达?" @confirm="deliver(row)" v-if="row.task_status==='in_transit'">
              <template #reference><el-button link type="success" size="small">送达</el-button></template>
            </el-popconfirm>
            <el-popconfirm title="上报异常?" @confirm="anomaly(row)" v-if="['assigned','in_transit'].includes(row.task_status)">
              <template #reference><el-button link type="danger" size="small">异常</el-button></template>
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

    <el-dialog v-model="locVisible" title="更新位置" width="400px">
      <el-form label-width="80px" :model="locForm">
        <el-form-item label="位置">
          <el-input v-model="locForm.current_location" placeholder="当前所在位置" />
        </el-form-item>
        <el-form-item label="进度(%)">
          <el-slider v-model="locForm.progress" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="locVisible=false">取消</el-button>
        <el-button type="primary" @click="submitLoc">确认上报</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listTasks, acceptTask, deliverTask, updateTaskLocation, reportTaskAnomaly } from '@/api'
import dayjs from 'dayjs'

const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const filters = reactive({ task_status: '' })
const locVisible = ref(false); const currentTask = ref(null)
const locForm = reactive({ current_location: '', progress: 50 })

const statusCount = computed(() => listData.value.filter(t => t.task_status === 'in_transit').length)

const statusType = (s) => ({
  assigned: 'primary', in_transit: 'primary',
  delivered: 'warning', completed: 'success', cancelled: 'info'
}[s] || 'info')

const formatTime = (t) => t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-'

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
const start = async (row) => { await acceptTask(row.task_id); ElMessage.success('任务已接受，开始运输'); loadData() }
const deliver = async (row) => { await deliverTask(row.task_id); ElMessage.success('已标记送达'); loadData() }
const updateLoc = (row) => {
  currentTask.value = row
  locForm.current_location = row.current_location || ''
  locForm.progress = 50
  locVisible.value = true
}
const submitLoc = async () => {
  await updateTaskLocation(currentTask.value.task_id, locForm)
  ElMessage.success('位置已上报')
  locVisible.value = false
  loadData()
}
const anomaly = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt('请描述异常情况', '异常上报', { inputPlaceholder: '如：堵车 / 车辆故障' })
    await reportTaskAnomaly(row.task_id, { description: value || '运输异常' })
    ElMessage.success('已上报')
    loadData()
  } catch (e) { /* cancel */ }
}

onMounted(loadData)
</script>

<style scoped>
</style>
