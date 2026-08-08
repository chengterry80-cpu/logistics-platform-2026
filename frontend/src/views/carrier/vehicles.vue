<template>
  <div class="page-container">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title-group">
        <h2 class="page-title">车辆管理</h2>
        <p class="page-subtitle">维护承运商车队信息，包括载重与尺寸</p>
      </div>
      <el-button type="primary" round @click="openForm()">
        <el-icon><Plus /></el-icon>&nbsp;新增车辆
      </el-button>
    </div>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table v-loading="loading" :data="listData" stripe style="width: 100%"
        :header-cell-style="{ background: '#f8fafc', color: '#475569', fontWeight: 600 }">
        <el-table-column prop="vehicle_id" label="编号" width="80" align="center">
          <template #default="{ row }">
            <span style="color:#94a3b8;font-weight:500">#{{ row.vehicle_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="plate_number" label="车牌号" width="140">
          <template #default="{ row }">
            <span style="font-weight:600;color:#1e293b">{{ row.plate_number }}</span>
          </template>
        </el-table-column>
        <el-table-column label="车型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.vehicle_type_display || row.vehicle_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="载重 / 容积" width="140">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b;line-height:1.6">
              <div><el-icon><ScaleToOriginal /></el-icon> {{ row.max_weight }} t</div>
              <div><el-icon><Box /></el-icon> {{ row.max_volume }} m³</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="尺寸 (长宽高)" width="140">
          <template #default="{ row }">
            <div style="font-size:13px;color:#64748b;line-height:1.6">
              <div>长 {{ row.length }} m</div>
              <div>宽 {{ row.width }} m</div>
              <div>高 {{ row.height }} m</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="owner" label="承运商" width="140">
          <template #default="{ row }">
            <span style="color:#475569">{{ row.owner || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag class="status-tag" :type="row.status==='available'?'success':'warning'" effect="light" round>
              {{ row.status === 'available' ? '空闲' : '出车' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openForm(row)">编辑</el-button>
            <el-popconfirm title="确定删除?" @confirm="remove(row)">
              <template #reference><el-button link type="danger" size="small">删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pagination" background layout="total, prev, pager, next"
        :total="total" v-model:current-page="page" :page-size="20" @current-change="loadData" />
    </el-card>

    <!-- 车辆表单弹窗 -->
    <el-dialog v-model="formVisible" :title="editId ? '编辑车辆' : '新增车辆'" width="560px">
      <el-form :model="form" :rules="rules" label-width="100px" ref="formRef">
        <el-form-item label="车牌号" prop="plate_number">
          <el-input v-model="form.plate_number" placeholder="如：京A12345" />
        </el-form-item>
        <el-form-item label="车型" prop="vehicle_type">
          <el-select v-model="form.vehicle_type" style="width:100%">
            <el-option label="厢式货车" value="van" />
            <el-option label="平板货车" value="flatbed" />
            <el-option label="冷藏车" value="refrigerated" />
            <el-option label="高栏车" value="fence" />
            <el-option label="半挂车" value="semi-trailer" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="载重(t)" prop="max_weight">
              <el-input-number v-model="form.max_weight" :min="0" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="容积(m³)" prop="max_volume">
              <el-input-number v-model="form.max_volume" :min="0" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="限高(m)">
              <el-input-number v-model="form.max_height" :min="0" :step="0.1" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="长(m)"><el-input-number v-model="form.length" :min="0" :step="0.1" style="width:100%" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="宽(m)"><el-input-number v-model="form.width" :min="0" :step="0.1" style="width:100%" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="高(m)"><el-input-number v-model="form.height" :min="0" :step="0.1" style="width:100%" /></el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="formVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listVehicles, createVehicle, updateVehicle, deleteVehicle } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const formVisible = ref(false)
const formRef = ref(); const saving = ref(false); const editId = ref(null)
const form = reactive({
  plate_number: '', vehicle_type: 'van',
  max_weight: 5, max_volume: 20, max_height: 4,
  length: 6.8, width: 2.4, height: 2.6
})
const rules = {
  plate_number: [{ required: true, message: '请填写车牌号' }],
  vehicle_type: [{ required: true, message: '请选择车型' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value }
    const res = await listVehicles(params)
    listData.value = res?.results || res || []
    total.value = res?.count || listData.value.length
  } finally { loading.value = false }
}

const openForm = (row) => {
  if (row) {
    editId.value = row.vehicle_id
    Object.assign(form, row)
  } else {
    editId.value = null
    Object.assign(form, {
      plate_number: '', vehicle_type: 'van',
      max_weight: 5, max_volume: 20, max_height: 4,
      length: 6.8, width: 2.4, height: 2.6
    })
  }
  formVisible.value = true
}

const submit = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    const me = userStore.userInfo
    const payload = { ...form, carrier_id: me?.carrier?.carrier_id || me?.id || 1 }
    if (editId.value) await updateVehicle(editId.value, payload)
    else await createVehicle(payload)
    ElMessage.success('操作成功')
    formVisible.value = false
    loadData()
  } finally { saving.value = false }
}

const remove = async (row) => { await deleteVehicle(row.vehicle_id); ElMessage.success('已删除'); loadData() }

onMounted(loadData)
</script>

<style scoped>
</style>
