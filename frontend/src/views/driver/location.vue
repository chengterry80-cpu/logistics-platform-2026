<template>
  <div class="page-container">
    <div class="page-header"><h2 class="page-title">位置上报</h2></div>
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">当前任务</span></template>
          <el-empty v-if="!current" description="当前没有进行中的任务" />
          <template v-else>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="任务编号">{{ current.task_id }}</el-descriptions-item>
              <el-descriptions-item label="货物">{{ current.request?.cargo_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="起点">{{ current.request?.origin || '-' }}</el-descriptions-item>
              <el-descriptions-item label="终点">{{ current.request?.destination || '-' }}</el-descriptions-item>
              <el-descriptions-item label="当前位置">
                <el-tag type="primary" size="small">{{ form.current_location || '-' }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="运输进度">
                <el-progress :percentage="form.progress" />
              </el-descriptions-item>
            </el-descriptions>
            <el-divider />
            <el-form label-width="90px">
              <el-form-item label="位置">
                <el-input v-model="form.current_location" placeholder="如：G4高速保定段" />
              </el-form-item>
              <el-form-item label="进度">
                <el-slider v-model="form.progress" :min="0" :max="100" :marks="{ 0: '0%', 50: '50%', 100: '100%' }" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="submitReport">
                  <el-icon><Location /></el-icon> 上报位置
                </el-button>
                <el-button @click="reportInterval = !reportInterval" :type="reportInterval ? 'danger' : 'success'">
                  {{ reportInterval ? '停止自动上报' : '启动自动上报' }}
                </el-button>
              </el-form-item>
            </el-form>
          </template>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">位置上报记录</span></template>
          <el-table :data="records" empty-text="暂无记录" stripe>
            <el-table-column prop="time" label="时间" width="170" />
            <el-table-column prop="location" label="位置" />
            <el-table-column prop="progress" label="进度" width="120">
              <template #default="{ row }">
                <el-progress :percentage="row.progress" :stroke-width="12" />
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { listTasks, updateTaskLocation } from '@/api'

const current = ref(null)
const records = ref([])
const reportInterval = ref(false)
let timer = null
const form = reactive({ current_location: '', progress: 0 })

const loadCurrent = async () => {
  try {
    const res = await listTasks({ task_status: 'in_transit' })
    const list = res?.results || res || []
    current.value = list[0] || null
    if (current.value) {
      form.current_location = current.value.current_location || current.value.request?.origin || ''
      form.progress = current.value.progress_percent || 0
    }
  } catch (e) { /* ignore */ }
}

const submitReport = async () => {
  if (!current.value) { ElMessage.warning('没有进行中的任务'); return }
  await updateTaskLocation(current.value.task_id, form)
  records.value.unshift({
    time: new Date().toLocaleString('zh-CN'),
    location: form.current_location,
    progress: form.progress
  })
  ElMessage.success('位置已上报')
}

const startAuto = () => {
  timer = setInterval(() => {
    if (form.progress < 100) form.progress = Math.min(100, form.progress + 1)
    submitReport().catch(() => {})
  }, 60 * 1000) // 每分钟上报一次
}

import { watch } from 'vue'
watch(reportInterval, (v) => {
  if (v) startAuto()
  else if (timer) { clearInterval(timer); timer = null; ElMessage.success('已停止自动上报') }
})

onMounted(loadCurrent)
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>
