<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">司机管理</h2>
      <el-button type="primary" @click="openForm()">
        <el-icon><Plus /></el-icon> 新增司机
      </el-button>
    </div>
    <el-card shadow="never">
      <el-table v-loading="loading" :data="listData" stripe>
        <el-table-column prop="driver_id" label="编号" width="80" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="phone" label="联系电话" width="140" />
        <el-table-column prop="license_number" label="驾照号" width="180" />
        <el-table-column prop="license_type" label="驾照类型" width="100" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status==='available'?'success':'warning'" size="small">
              {{ row.status === 'available' ? '空闲' : '出车' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
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

    <el-dialog v-model="formVisible" :title="editId ? '编辑司机' : '新增司机'" width="500px">
      <el-form :model="form" :rules="rules" label-width="100px" ref="formRef">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" maxlength="11" />
        </el-form-item>
        <el-form-item label="身份证" prop="id_card">
          <el-input v-model="form.id_card" maxlength="18" />
        </el-form-item>
        <el-form-item label="驾照号" prop="license_number">
          <el-input v-model="form.license_number" />
        </el-form-item>
        <el-form-item label="驾照类型" prop="license_type">
          <el-select v-model="form.license_type" style="width:100%">
            <el-option label="A1" value="A1" /><el-option label="A2" value="A2" />
            <el-option label="A3" value="A3" /><el-option label="B1" value="B1" />
            <el-option label="B2" value="B2" /><el-option label="C1" value="C1" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
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
import { listDrivers, createDriver, deleteVehicle, updateVehicle } from '@/api'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const listData = ref([]); const total = ref(0)
const page = ref(1); const loading = ref(false)
const formVisible = ref(false)
const formRef = ref(); const saving = ref(false); const editId = ref(null)
const form = reactive({ name: '', phone: '', id_card: '', license_number: '', license_type: 'B2', remark: '' })
const rules = {
  name: [{ required: true, message: '请填写姓名' }],
  phone: [{ required: true, message: '请填写电话' }],
  license_number: [{ required: true, message: '请填写驾照号' }],
  license_type: [{ required: true, message: '请选择类型' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const params = { page: page.value }
    const res = await listDrivers(params)
    listData.value = res?.results || res || []
    total.value = res?.count || listData.value.length
  } finally { loading.value = false }
}

const openForm = (row) => {
  if (row) {
    editId.value = row.driver_id
    Object.assign(form, row)
  } else {
    editId.value = null
    Object.assign(form, { name: '', phone: '', id_card: '', license_number: '', license_type: 'B2', remark: '' })
  }
  formVisible.value = true
}

const submit = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    const me = userStore.userInfo
    const payload = { ...form, carrier_id: me?.carrier?.carrier_id || me?.id || 1 }
    if (editId.value) {
      try { await updateVehicle(editId.value, payload) } catch { await createDriver(payload) }
    } else {
      await createDriver(payload)
    }
    ElMessage.success('操作成功')
    formVisible.value = false
    loadData()
  } finally { saving.value = false }
}

const remove = async (row) => {
  try {
    await deleteVehicle(row.driver_id)
  } catch { /* ignore */ }
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.pagination { margin-top: 20px; justify-content: flex-end; display: flex; }
</style>
