<template>
  <div class="page-container">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-group">
        <h2 class="page-title">运输任务</h2>
        <p class="page-subtitle">管理已接单的运输任务，指派司机与车辆</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filters.task_status" clearable placeholder="全部" style="width: 140px">
            <el-option label="待指派" value="pending" />
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
        <el-table-column prop="task_id" label="任务编号" width="90" align="center">
          <template #default="{ row }">
            <span style="color:#94a3b8;font-weight:500">#{{ row.task_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="request_id" label="需求编号" width="100" align="center">
          <template #default="{ row }">
            <span style="color:#94a3b8;font-weight:500">#{{ row.request_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="司机 / 车牌" width="170">
          <template #default="{ row }">
            <div style="font-weight:500;color:#1e293b">
              <el-icon><User /></el-icon> {{ row.driver?.name || '-' }}
            </div>
            <div style="color:#94a3b8;font-size:12px;margin-top:2px">
              <el-icon><Postcard /></el-icon> {{ row.vehicle?.plate_number || '-' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="当前位置" width="150">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">
              <el-icon><Location /></el-icon> {{ row.current_location || '-' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="任务状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag class="status-tag" :type="statusType(row.task_status)" effect="light" round>
              {{ row.task_status_display || row.task_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="付款状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="light" round :type="row.payment_status==='paid'?'success':'warning'">
              {{ row.payment_status === 'paid' ? '已付款' : '未付款' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="view(row)">详情</el-button>
            <el-button link type="warning" size="small" @click="assignTask(row)" v-if="row.task_status==='pending'">指派</el-button>
            <el-popconfirm title="确认已送达?" @confirm="deliver(row)" v-if="row.task_status==='in_transit'">
              <template #reference><el-button link type="success" size="small">确认送达</el-button></template>
            </el-popconfirm>
            <el-popconfirm title="标记异常?" @confirm="anomaly(row)" v-if="['pending','assigned','in_transit'].includes(row.task_status)">
              <template #reference><el-button link type="danger" size="small">异常上报</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pagination" background layout="total, prev, pager, next"
        :total="total" v-model:current-page="page" :page-size="20" @current-change="loadData" />
    </el-card>

    <!-- 指派弹窗 -->
    <el-dialog v-model="assignVisible" title="指派司机与车辆" width="500px">
      <el-form :model="assignForm" :rules="assignRules" label-width="100px" ref="assignFormRef">
        <el-form-item label="司机" prop="driver_id">
          <el-select v-model="assignForm.driver_id" style="width:100%" placeholder="选择司机">
            <el-option v-for="d in driverList" :key="d.driver_id" :label="`${d.name} - ${d.phone}`" :value="d.driver_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="车辆" prop="vehicle_id">
          <el-select v-model="assignForm.vehicle_id" style="width:100%" placeholder="选择车辆">
            <el-option v-for="v in vehicleList" :key="v.vehicle_id" :label="`${v.plate_number} (${v.vehicle_type})`" :value="v.vehicle_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitAssign">确认指派</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listTasks, assignTask as apiAssign, deliverTask, reportTaskAnomaly, listDrivers, listVehicles } from '@/api'

const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const filters = reactive({ task_status: '' })
const assignVisible = ref(false)
const currentTask = ref(null)
const driverList = ref([])
const vehicleList = ref([])
const assignFormRef = ref()
const saving = ref(false)
const assignForm = reactive({ driver_id: null, vehicle_id: null })
const assignRules = {
  driver_id: [{ required: true, message: '请选择司机' }],
  vehicle_id: [{ required: true, message: '请选择车辆' }]
}

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

const loadMeta = async () => {
  try {
    const [d, v] = await Promise.all([listDrivers(), listVehicles()])
    driverList.value = d?.results || d || []
    vehicleList.value = v?.results || v || []
  } catch (e) { /* ignore */ }
}

const view = (row) => ElMessageBox.alert(JSON.stringify(row, null, 2), '任务详情')
const assignTask = async (row) => {
  await loadMeta()
  currentTask.value = row
  assignForm.driver_id = null
  assignForm.vehicle_id = null
  assignVisible.value = true
}
const submitAssign = async () => {
  await assignFormRef.value.validate()
  saving.value = true
  try {
    await apiAssign(currentTask.value.task_id, assignForm)
    ElMessage.success('指派成功')
    assignVisible.value = false
    loadData()
  } finally { saving.value = false }
}
const deliver = async (row) => { await deliverTask(row.task_id); ElMessage.success('已标记送达'); loadData() }
const anomaly = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt('请描述异常情况', '异常上报', { inputPlaceholder: '如：堵车 / 事故' })
    await reportTaskAnomaly(row.task_id, { description: value || '运输异常' })
    ElMessage.success('已上报')
    loadData()
  } catch (e) { /* 取消 */ }
}

onMounted(loadData)
</script>

<style scoped>
</style>
