<template>
  <div class="page-container">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-group">
        <h2 class="page-title">需求广场</h2>
        <p class="page-subtitle">浏览平台上的运输需求，快速报价获取订单</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filters" @submit.prevent>
        <el-form-item label="货物">
          <el-input v-model="filters.cargo_name" clearable placeholder="货物名称" style="width: 200px" />
        </el-form-item>
        <el-form-item label="起始地">
          <el-input v-model="filters.origin" clearable placeholder="起始地" style="width: 160px" />
        </el-form-item>
        <el-form-item label="目的地">
          <el-input v-model="filters.destination" clearable placeholder="目的地" style="width: 160px" />
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
        <el-table-column prop="request_id" label="编号" width="80" align="center">
          <template #default="{ row }">
            <span style="color:#94a3b8;font-weight:500">#{{ row.request_id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="货主" width="150">
          <template #default="{ row }">
            <span style="font-weight:500;color:#1e293b">{{ row.shipper?.company_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="货物名称" min-width="150">
          <template #default="{ row }">
            <div style="font-weight:500;color:#1e293b">{{ row.cargo_name }}</div>
            <el-tag size="small" effect="plain" style="margin-top:2px">{{ row.cargo_type_display || row.cargo_type || '普通货物' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="规格" width="130">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b;line-height:1.6">
              <div><el-icon><ScaleToOriginal /></el-icon> {{ row.weight }} kg</div>
              <div><el-icon><Box /></el-icon> {{ row.volume }} m³</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="运输路线" min-width="240">
          <template #default="{ row }">
            <div class="route-cell">
              <span class="route-point"><el-icon color="#3b82f6"><Location /></el-icon>{{ row.origin }}</span>
              <el-icon class="route-arrow"><Right /></el-icon>
              <span class="route-point"><el-icon color="#ef4444"><MapLocation /></el-icon>{{ row.destination }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="expected_time" label="期望时间" width="170">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b">{{ row.expected_time || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag class="status-tag" :type="row.status==='pending'?'warning':'primary'" effect="light" round>
              {{ row.status_display || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="view(row)">详情</el-button>
            <el-button link type="success" size="small" @click="openQuote(row)">立即报价</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pagination" background layout="total, prev, pager, next"
        :total="total" v-model:current-page="page" :page-size="20" @current-change="loadData" />
    </el-card>

    <!-- 报价弹窗 -->
    <el-dialog v-model="quoteVisible" title="提交报价" width="500px">
      <el-form :model="quoteForm" :rules="quoteRules" label-width="120px" ref="quoteFormRef">
        <el-form-item label="需求编号">
          <span style="font-weight:600;color:#1e293b">#{{ currentReq?.request_id }}</span>
        </el-form-item>
        <el-form-item label="报价类型">
          <el-radio-group v-model="quoteForm.quote_type">
            <el-radio label="total">总价</el-radio>
            <el-radio label="per_km">按公里</el-radio>
            <el-radio label="per_weight">按重量</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="报价金额(元)" prop="amount">
          <el-input-number v-model="quoteForm.amount" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="quoteForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quoteVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitQuote">提交报价</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listRequests, createQuote } from '@/api'
import { useUserStore } from '@/store/user'
import dayjs from 'dayjs'

const userStore = useUserStore()
const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const filters = reactive({ cargo_name: '', origin: '', destination: '', status: 'pending' })
const quoteVisible = ref(false)
const quoteFormRef = ref()
const currentReq = ref(null)
const saving = ref(false)
const quoteForm = reactive({ quote_type: 'total', amount: 0, remark: '' })
const quoteRules = { amount: [{ required: true, message: '请填写报价金额' }] }

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
  filters.cargo_name = ''; filters.origin = ''; filters.destination = '';
  filters.status = 'pending'; page.value = 1; loadData()
}
const view = (row) => ElMessageBox.alert(JSON.stringify(row, null, 2), '需求详情')
const openQuote = (row) => {
  currentReq.value = row
  quoteForm.amount = Math.round((row.weight || 1000) * 1.5)
  quoteForm.quote_type = 'total'
  quoteForm.remark = ''
  quoteVisible.value = true
}
const submitQuote = async () => {
  await quoteFormRef.value.validate()
  saving.value = true
  try {
    const me = userStore.userInfo
    await createQuote({
      request_id: currentReq.value.request_id,
      carrier_id: me?.carrier?.carrier_id || me?.id || 1,
      ...quoteForm,
      validity_period: dayjs().add(3, 'day').format('YYYY-MM-DD HH:mm:ss')
    })
    ElMessage.success('报价已提交')
    quoteVisible.value = false
  } finally { saving.value = false }
}

onMounted(loadData)
</script>

<style scoped>
</style>
