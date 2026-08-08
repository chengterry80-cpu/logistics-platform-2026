<template>
  <div class="page-container">
    <div class="page-header"><h2 class="page-title">运输任务</h2></div>
    <el-card shadow="never">
      <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent>
        <el-form-item label="状态">
          <el-select v-model="filters.task_status" clearable placeholder="全部">
            <el-option label="待指派" value="pending" />
            <el-option label="已指派" value="assigned" />
            <el-option label="运输中" value="in_transit" />
            <el-option label="已送达" value="delivered" />
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
        <el-table-column prop="task_id" label="任务编号" width="90" />
        <el-table-column prop="request_id" label="需求编号" width="100" />
        <el-table-column label="承运商" width="140">
          <template #default="{ row }">{{ row.carrier?.company_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="司机/车牌" width="160">
          <template #default="{ row }">
            <div>{{ row.driver?.name || '-' }}</div>
            <div style="color:#909399;font-size:12px">{{ row.vehicle?.plate_number || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="当前位置" width="140">
          <template #default="{ row }">{{ row.current_location || '-' }}</template>
        </el-table-column>
        <el-table-column label="任务状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.task_status)" size="small" class="status-tag">
              {{ row.task_status_display || row.task_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="付款状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.payment_status==='paid'?'success':'warning'">
              {{ row.payment_status || 'unpaid' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="view(row)">详情</el-button>
            <el-popconfirm title="确认送达并完成任务?" @confirm="complete(row)" v-if="row.task_status==='delivered'">
              <template #reference><el-button link type="success" size="small">确认完成</el-button></template>
            </el-popconfirm>
            <el-popconfirm title="确认已支付?" @confirm="pay(row)" v-if="row.payment_status!=='paid' && row.task_status!=='cancelled'">
              <template #reference><el-button link type="warning" size="small">确认付款</el-button></template>
            </el-popconfirm>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { listTasks, completeTask, confirmTaskPayment } from '@/api'

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
const complete = async (row) => { await completeTask(row.task_id); ElMessage.success('任务已完成'); loadData() }
const pay = async (row) => { await confirmTaskPayment(row.task_id); ElMessage.success('付款已确认'); loadData() }

onMounted(loadData)
</script>

<style scoped>
.filter-form { margin-bottom: 0; }
.pagination { margin-top: 20px; justify-content: flex-end; display: flex; }
</style>
