<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '../api'

interface LogItem {
  id: number
  user_id: number | null
  username: string | null
  action: string
  resource_type: string
  resource_id: number | null
  detail: string | null
  created_at: string
}

const logs = ref<LogItem[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(50)
const filterAction = ref('')
const filterType = ref('')

const actionMap: Record<string, string> = {
  create: '创建', update: '修改', delete: '删除',
  batch_update: '批量修改', export: '导出',
}
const typeMap: Record<string, string> = {
  product: '产品', customer: '客户', catalog: '货盘', user: '用户',
}

async function loadLogs() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: page.value, page_size: pageSize.value }
    if (filterAction.value) params.action = filterAction.value
    if (filterType.value) params.resource_type = filterType.value
    const res = await authApi.listLogs(params)
    logs.value = res.data.items
    total.value = res.data.total
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.response?.data?.detail || e.message))
  } finally { loading.value = false }
}

onMounted(loadLogs)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 12px">
      <el-form :inline="true">
        <el-form-item label="操作类型">
          <el-select v-model="filterAction" clearable style="width: 120px" @change="loadLogs">
            <el-option v-for="(v,k) in actionMap" :key="k" :label="v" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="资源类型">
          <el-select v-model="filterType" clearable style="width: 120px" @change="loadLogs">
            <el-option v-for="(v,k) in typeMap" :key="k" :label="v" :value="k" />
          </el-select>
        </el-form-item>
        <el-button type="primary" @click="loadLogs">刷新</el-button>
      </el-form>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <el-table :data="logs" border style="width: 100%" max-height="700">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="username" label="操作人" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">{{ actionMap[row.action] || row.action }}</template>
        </el-table-column>
        <el-table-column label="资源类型" width="100">
          <template #default="{ row }">{{ typeMap[row.resource_type] || row.resource_type }}</template>
        </el-table-column>
        <el-table-column prop="resource_id" label="资源ID" width="80" />
        <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
      </el-table>
      <el-pagination
        v-if="total > pageSize"
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadLogs"
        style="margin-top: 12px"
      />
    </el-card>
  </div>
</template>

