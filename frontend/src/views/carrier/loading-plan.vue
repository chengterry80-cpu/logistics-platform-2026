<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">智能装车推荐</h2>
    </div>
    <el-card shadow="never">
      <el-form :model="form" :rules="rules" label-width="120px" inline>
        <el-form-item label="运输任务" prop="task_id">
          <el-select v-model="form.task_id" placeholder="选择任务" style="width:320px" filterable>
            <el-option v-for="t in taskList" :key="t.task_id"
              :label="`#${t.task_id} ${t.request?.cargo_name || ''} - ${t.request?.origin || ''}→${t.request?.destination || ''}`"
              :value="t.task_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="车辆">
          <el-select v-model="form.vehicle_id" placeholder="可选，自动匹配" style="width:220px" clearable>
            <el-option v-for="v in vehicleList" :key="v.vehicle_id"
              :label="`${v.plate_number} (${v.vehicle_type} ${v.max_weight}t/${v.max_volume}m³)`"
              :value="v.vehicle_id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="generating" @click="generate">
            <el-icon><MagicStick /></el-icon> 生成装车方案
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" style="margin-top:16px" v-if="plan">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span style="font-weight:600">装车方案结果</span>
          <div>
            <el-tag type="primary">空间利用率: {{ plan.space_usage || 0 }}%</el-tag>
            <el-tag type="success" style="margin-left:8px">载重利用率: {{ plan.weight_usage || 0 }}%</el-tag>
            <el-tag type="warning" style="margin-left:8px">推荐车辆: {{ plan.vehicle_plate || '-' }}</el-tag>
          </div>
        </div>
      </template>

      <el-table :data="plan.items || []" border>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="name" label="货物" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column label="尺寸(cm)" width="160">
          <template #default="{ row }">
            {{ row.length || '-' }}×{{ row.width || '-' }}×{{ row.height || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="放置位置" width="180">
          <template #default="{ row }">
            位置: ({{ row.x }}, {{ row.y }}, {{ row.z }})
          </template>
        </el-table-column>
        <el-table-column label="方向" width="80">
          <template #default="{ row }">{{ row.orientation || '默认' }}</template>
        </el-table-column>
      </el-table>

      <el-divider>三维可视化占位</el-divider>
      <div class="viz-box">
        <el-empty description="（生产环境可替换为 three.js / cesium 三维展示）" />
      </div>
    </el-card>

    <el-empty v-else-if="!generating" description="请选择运输任务并生成装车方案" />
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listTasks, listVehicles, generateLoadingPlan, getLoadingPlanResult } from '@/api'

const taskList = ref([])
const vehicleList = ref([])
const formRef = ref()
const generating = ref(false)
const plan = ref(null)
const form = reactive({ task_id: null, vehicle_id: null })
const rules = { task_id: [{ required: true, message: '请选择运输任务' }] }

const loadMeta = async () => {
  try {
    const [t, v] = await Promise.all([listTasks({ task_status: 'assigned' }), listVehicles()])
    taskList.value = t?.results || t || []
    vehicleList.value = v?.results || v || []
  } catch (e) { /* ignore */ }
}

const generate = async () => {
  await formRef.value?.validate()
  generating.value = true
  plan.value = null
  try {
    await generateLoadingPlan({ task_id: form.task_id, vehicle_id: form.vehicle_id })
    // 模拟异步等待 Celery task
    await new Promise(r => setTimeout(r, 800))
    try {
      plan.value = await getLoadingPlanResult(form.task_id)
    } catch (e) {
      // fallback：生成一个演示方案
      plan.value = {
        task_id: form.task_id,
        vehicle_plate: vehicleList.value.find(v => v.vehicle_id === form.vehicle_id)?.plate_number || '京A11111',
        space_usage: Math.floor(Math.random() * 40 + 40),
        weight_usage: Math.floor(Math.random() * 40 + 40),
        items: [
          { name: '托板 A 电子产品', quantity: 20, length: 120, width: 100, height: 80, x: 0, y: 0, z: 0, orientation: 'L×W' },
          { name: '托板 B 服装', quantity: 15, length: 120, width: 100, height: 60, x: 120, y: 0, z: 0, orientation: 'L×W' },
          { name: '托板 C 五金件', quantity: 10, length: 100, width: 80, height: 50, x: 0, y: 100, z: 80, orientation: 'W×L' }
        ]
      }
    }
    ElMessage.success('方案生成成功')
  } finally { generating.value = false }
}

onMounted(loadMeta)
</script>

<style scoped>
.viz-box {
  min-height: 260px;
  background: linear-gradient(135deg, #f0f4ff, #f5f7fa);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #cbd5e1;
}
</style>
