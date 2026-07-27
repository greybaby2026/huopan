<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { catalogsApi, customersApi, exportApi } from '../api'

const loading = ref(false)
const customers = ref<any[]>([])
const catalogNames = ref<string[]>([])
const selectedCatalogName = ref('')
const selectedCustomerId = ref<number | undefined>()
const tableData = ref<any[]>([])
const total = ref(0)

const statusMap: Record<string, string> = {
  available: '可供', low_stock: '紧张', sold_out: '断货',
}

async function loadCatalogToSheet() {
  if (!selectedCatalogName.value) { ElMessage.warning('请选择货盘'); return }
  loading.value = true
  try {
    const params: Record<string, any> = { name: selectedCatalogName.value }
    if (selectedCustomerId.value) params.customer_id = selectedCustomerId.value
    const res = await catalogsApi.list(params)
    const items = res.data.items
    if (items.length === 0) { ElMessage.warning('货盘无数据'); return }

    tableData.value = items.map((item: any) => {
      const p = item.product || {}
      return {
        sku_code: p.sku_code || '',
        name: p.name || '',
        category: p.category || '',
        color: p.color || '',
        size_range: p.size_range || '',
        supply_price: p.supply_price || 0,
        price: item.price || 0,
        min_order_qty: item.min_order_qty || 1,
        stock_status: statusMap[item.stock_status] || '',
        note: item.note || '',
      }
    })
    total.value = items.length
    ElMessage.success(`已加载 ${items.length} 条货盘数据`)
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.message || '未知错误'))
  } finally { loading.value = false }
}

function exportExcel() {
  if (!selectedCatalogName.value) { ElMessage.warning('请先选择货盘'); return }
  window.open(exportApi.catalogExcelUrl(selectedCatalogName.value, selectedCustomerId.value), '_blank')
}

async function loadCatalogNames() {
  try {
    const res = await catalogsApi.list()
    const names = [...new Set(res.data.items.map((c: any) => c.name))]
    catalogNames.value = names
  } catch {}
}

onMounted(async () => {
  try {
    const res = await customersApi.list()
    customers.value = res.data
    await loadCatalogNames()
  } catch {}
})
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 12px">
      <div style="display: flex; gap: 8px; align-items: center">
        <span style="font-weight: bold">货盘排版</span>
        <el-select v-model="selectedCatalogName" placeholder="选择货盘" style="width: 240px" filterable>
          <el-option v-for="n in catalogNames" :key="n" :label="n" :value="n" />
        </el-select>
        <el-select v-model="selectedCustomerId" clearable placeholder="客户(可选)" style="width: 160px">
          <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" @click="loadCatalogToSheet" :loading="loading">加载到表格</el-button>
        <el-button @click="exportExcel">导出Excel</el-button>
        <span style="flex: 1"></span>
        <span style="color: #909399; font-size: 12px">加载货盘数据预览, 一键导出带图片的 Excel 文件</span>
      </div>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <template v-if="tableData.length > 0">
        <div style="margin-bottom: 8px; font-size: 16px; font-weight: bold">
          货盘表 - {{ selectedCatalogName }}
        </div>
        <el-table :data="tableData" border height="600" style="width: 100%" stripe>
          <el-table-column type="index" label="#" width="50" fixed />
          <el-table-column prop="sku_code" label="款号" width="120" />
          <el-table-column prop="name" label="名称" min-width="150" />
          <el-table-column prop="category" label="品类" width="100" />
          <el-table-column prop="color" label="颜色" width="80" />
          <el-table-column prop="size_range" label="尺码" width="100" />
          <el-table-column prop="supply_price" label="供应价" width="90" align="right">
            <template #default="{ row }">¥{{ Number(row.supply_price || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</template>
          </el-table-column>
          <el-table-column prop="price" label="货盘价" width="90" align="right">
            <template #default="{ row }">¥{{ row.price.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="min_order_qty" label="起订量" width="80" align="center" />
          <el-table-column prop="stock_status" label="状态" width="80" align="center" />
          <el-table-column prop="note" label="备注" min-width="120" />
        </el-table>
        <div style="margin-top: 8px; color: #909399; font-size: 12px">共 {{ total }} 条记录</div>
      </template>
      <el-empty v-else-if="!loading" description="请选择货盘并点击加载到表格" />
    </el-card>
  </div>
</template>

