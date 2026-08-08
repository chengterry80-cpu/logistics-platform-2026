<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">{{ isEdit ? '编辑需求' : '发布运输需求' }}</h2>
      <el-button link @click="$router.back()">
        <el-icon><Back /></el-icon> 返回
      </el-button>
    </div>
    <el-card shadow="never">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width:720px">
        <el-divider content-position="left">货物信息</el-divider>
        <el-form-item label="货物名称" prop="cargo_name">
          <el-input v-model="form.cargo_name" placeholder="如：电子产品" />
        </el-form-item>
        <el-form-item label="货物类型" prop="cargo_type">
          <el-select v-model="form.cargo_type" placeholder="请选择">
            <el-option label="普通货物" value="general" />
            <el-option label="易碎品" value="fragile" />
            <el-option label="冷藏品" value="cold" />
            <el-option label="危险品" value="dangerous" />
            <el-option label="大件" value="bulk" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="重量(kg)" prop="weight">
              <el-input-number v-model="form.weight" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="体积(m³)" prop="volume">
              <el-input-number v-model="form.volume" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="高度(cm)">
              <el-input-number v-model="form.cargo_height" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">运输信息</el-divider>
        <el-form-item label="起始地" prop="origin">
          <el-input v-model="form.origin" placeholder="如：北京市朝阳区" />
        </el-form-item>
        <el-form-item label="目的地" prop="destination">
          <el-input v-model="form.destination" placeholder="如：上海市浦东新区" />
        </el-form-item>
        <el-form-item label="期望送达时间" prop="expected_time">
          <el-date-picker v-model="form.expected_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="特殊要求">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="选填" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" size="large" @click="submit">确认发布</el-button>
          <el-button size="large" @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import { useRouter } from 'vue-router'
import { createRequest } from '@/api'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const saving = ref(false)
const isEdit = ref(false)

const form = reactive({
  cargo_name: '', cargo_type: 'general',
  weight: 1000, volume: 5, cargo_height: 150,
  origin: '', destination: '',
  expected_time: dayjs().add(2, 'day').format('YYYY-MM-DD HH:mm:ss'),
  remark: ''
})

const rules = {
  cargo_name: [{ required: true, message: '请填写货物名称' }],
  cargo_type: [{ required: true, message: '请选择货物类型' }],
  origin: [{ required: true, message: '请填写起始地' }],
  destination: [{ required: true, message: '请填写目的地' }],
  expected_time: [{ required: true, message: '请选择时间' }]
}

const submit = async () => {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = { ...form }
    // 回填 shipper_id（当前用户为货主时取其 ID）
    const me = userStore.userInfo
    payload.shipper_id = me?.shipper?.shipper_id || me?.id || 1
    await createRequest(payload)
    ElMessage.success('需求已发布，等待承运商报价')
    router.push('/shipper/requests')
  } finally { saving.value = false }
}
</script>
