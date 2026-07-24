<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { productsApi, customersApi, catalogsApi, authApi } from '../api'
const totalProducts = ref(0)
const activeProducts = ref(0)
const draftProducts = ref(0)
const totalCustomers = ref(0)
const totalCatalogs = ref(0)
const totalUsers = ref(0)
const recentLogs = ref<any[]>([])
const loading = ref(false)
async function loadDashboard() {
  loading.value = true
  try {
    const [prodRes, custRes, catRes, userRes, logRes] = await Promise.all([
      productsApi.list({ page: 1, page_size: 1 }),
      customersApi.list(),
      catalogsApi.list(),
      authApi.listUsers(),
      authApi.listLogs({ page: 1, page_size: 5 }),
    ])
    totalProducts.value = prodRes.data.total || 0
    totalCustomers.value = custRes.data.length || 0
    totalCatalogs.value = catRes.data.items?.length || 0
    totalUsers.value = userRes.data.items?.length || 0
    recentLogs.value = logRes.data.items?.slice(0, 5) || []
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.response?.data?.detail || e.message))
  } finally { loading.value = false }
}
const actionMap: Record<string, string> = {
  create: '创建', update: '修改', delete: '删除', batch_update: '批量修改', export: '导出',
}
const typeMap: Record<string, string> = {
  product: '产品', customer: '客户', catalog: '货盘', user: '用户',
}
onMounted(loadDashboard)
</script>
<template>
  <div v-loading="loading">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="never">
          <div style="text-align: center">
            <div style="font-size: 36px; color: #409eff; font-weight: bold">{{ totalProducts }}</div>
            <div style="color: #909399; margin-top: 4px">产品总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div style="text-align: center">
            <div style="font-size: 36px; color: #67c23a; font-weight: bold">{{ totalCustomers }}</div>
            <div style="color: #909399; margin-top: 4px">客户总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div style="text-align: center">
            <div style="font-size: 36px; color: #e6a23c; font-weight: bold">{{ totalCatalogs }}</div>
            <div style="color: #909399; margin-top: 4px">货盘总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div style="text-align: center">
            <div style="font-size: 36px; color: #f56c6c; font-weight: bold">{{ totalUsers }}</div>
            <div style="color: #909399; margin-top: 4px">系统用户</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-card shadow="never" style="margin-top: 16px">
      <template #header><span>最近操作</span></template>
      <el-table :data="recentLogs" border>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
        </el-table-column>
        <el-table-column prop="username" label="操作人" width="100" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">{{ actionMap[row.action] || row.action }}</template>
        </el-table-column>
        <el-table-column label="资源" width="100">
          <template #default="{ row }">{{ typeMap[row.resource_type] || row.resource_type }}#{{ row.resource_id }}</template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>
