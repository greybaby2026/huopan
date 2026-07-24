<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { catalogsApi, customersApi, exportApi, UPLOAD_BASE } from '../api'

interface CatalogItem {
  id: number
  name: string
  customer_id: number | null
  product_id: number
  price: number
  min_order_qty: number
  stock_status: string
  note: string | null
  created_at: string
  updated_at: string
  product: {
    id: number
    sku_code: string
    name: string
    category: string | null
    color: string | null
    size_range: string | null
    supply_price: number
    images: Array<{ thumbnail_path: string | null; original_path: string }>
  } | null
  customer: { id: number; name: string } | null
}

interface CustomerLevel {
  id: number
  name: string
  discount_rate: number
  default_min_qty: number
}

interface Customer {
  id: number
  name: string
  level_id: number | null
}

const catalogs = ref<CatalogItem[]>([])
const customers = ref<Customer[]>([])
const levels = ref<CustomerLevel[]>([])
const loading = ref(false)

const searchName = ref('')
const searchCustomerId = ref<number | undefined>()

const statusMap: Record<string, { label: string; type: string }> = {
  available: { label: '鍙緵', type: 'success' },
  low_stock: { label: '绱紶', type: 'warning' },
  sold_out: { label: '鏂揣', type: 'danger' },
}

// 鎵归噺鐢熸垚寮圭獥
const batchDialogVisible = ref(false)
const batchForm = reactive({
  name: '',
  customer_id: undefined as number | undefined,
  level_discount_rate: 0.8,
  min_order_qty: 1,
  selectedProductIds: [] as number[],
})

// 货盘名称分组
const catalogGroups = computed(() => {
  const groups: Record<string, CatalogItem[]> = {}
  for (const c of catalogs.value) {
    if (!groups[c.name]) groups[c.name] = []
    groups[c.name].push(c)
  }
  return groups
})

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (searchName.value) params.name = searchName.value
    if (searchCustomerId.value) params.customer_id = searchCustomerId.value
    const res = await catalogsApi.list(params)
    catalogs.value = res.data.items
  } catch (e: any) {
    ElMessage.error('加载失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function loadCustomers() {
  try {
    const res = await customersApi.list()
    customers.value = res.data
    const lvlRes = await customersApi.levels()
    levels.value = lvlRes.data
  } catch {
    // 蹇界暐
  }
}

function imageUrl(path: string | null): string {
  if (!path) return ''
  return `${UPLOAD_BASE}/uploads/${path}`
}

async function handleUpdatePrice(row: CatalogItem) {
  try {
    await catalogsApi.update(row.id, { price: row.price })
    ElMessage.success('价格已更新')
  } catch (e: any) {
    ElMessage.error('更新失败: ' + e.message)
  }
}

async function handleUpdateStatus(row: CatalogItem, status: string) {
  try {
    await catalogsApi.update(row.id, { stock_status: status })
    row.stock_status = status
    ElMessage.success('鐘舵佸凡鏇存柊')
  } catch (e: any) {
    ElMessage.error('更新失败: ' + e.message)
  }
}

async function handleDelete(row: CatalogItem) {
  try {
    await ElMessageBox.confirm(`确定删除璐洏椤?${row.product?.sku_code}?`, '提示', { type: 'warning' })
    await catalogsApi.delete(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('删除失败: ' + e.message)
  }
}

function openBatchDialog() {
  batchForm.name = ''
  batchForm.customer_id = undefined
  batchForm.level_discount_rate = 0.8
  batchForm.min_order_qty = 1
  batchForm.selectedProductIds = []
  batchDialogVisible.value = true
}

async function handleBatchCreate() {
  if (!batchForm.name) {
    ElMessage.warning('请填写货盘名称')
    return
  }
  if (batchForm.selectedProductIds.length === 0) {
    ElMessage.warning('请选择产品')
    return
  }
  try {
    await catalogsApi.batchCreate({
      name: batchForm.name,
      customer_id: batchForm.customer_id,
      level_discount_rate: batchForm.level_discount_rate,
      min_order_qty: batchForm.min_order_qty,
      product_ids: batchForm.selectedProductIds,
    })
    ElMessage.success(`宸茬敓鎴?${batchForm.selectedProductIds.length} 个产品`)
    batchDialogVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error('鐢熸垚失败: ' + (e.response?.data?.detail || e.message))
  }
}

function handleExportExcel(catalogName: string, customerId?: number) {
  const url = exportApi.catalogExcelUrl(catalogName, customerId)
  window.open(url, '_blank')
}

function handleExportImages(catalogName: string, customerId?: number) {
  const url = exportApi.catalogImagesUrl(catalogName, customerId)
  window.open(url, '_blank')
}

onMounted(() => {
  loadCustomers()
  loadData()
})
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 12px">
      <div style="display: flex; gap: 8px; align-items: center">
        <el-input v-model="searchName" placeholder="璐洏鍚嶇" clearable style="width: 200px" @keyup.enter="loadData" />
        <el-select v-model="searchCustomerId" clearable placeholder="瀹埛" style="width: 160px" @change="loadData">
          <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" @click="loadData">搜索</el-button>
        <el-button type="success" @click="openBatchDialog">鐢熸垚璐洏</el-button>
      </div>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <div v-for="(items, name) in catalogGroups" :key="name" style="margin-bottom: 24px">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px">
          <h3 style="margin: 0">{{ name }} ({{ items.length }}娆?</h3>
          <div style="display: flex; gap: 8px">
            <el-button size="small" type="primary" @click="handleExportExcel(name, items[0]?.customer_id || undefined)">
              导出Excel
            </el-button>
            <el-button size="small" @click="handleExportImages(name, items[0]?.customer_id || undefined)">
              导出图片鍖?            </el-button>
          </div>
        </div>
        <el-table :data="items" border size="small">
          <el-table-column label="图片" width="70">
            <template #default="{ row }">
              <el-image
                v-if="row.product?.images?.length"
                :src="imageUrl(row.product.images[0].thumbnail_path || row.product.images[0].original_path)"
                fit="cover"
                style="width: 50px; height: 50px; border-radius: 4px"
                :preview-src-list="[imageUrl(row.product.images[0].original_path)]"
                :preview-teleported="true"
              />
              <span v-else style="color: #c0c4cc">无图</span>
            </template>
          </el-table-column>
          <el-table-column label="娆惧彿" width="120">
            <template #default="{ row }">{{ row.product?.sku_code }}</template>
          </el-table-column>
          <el-table-column label="鍚嶇" min-width="120">
            <template #default="{ row }">{{ row.product?.name }}</template>
          </el-table-column>
          <el-table-column label="品类" width="80">
            <template #default="{ row }">{{ row.product?.category }}</template>
          </el-table-column>
          <el-table-column label="颜色" width="70">
            <template #default="{ row }">{{ row.product?.color }}</template>
          </el-table-column>
          <el-table-column label="供应价" width="90" align="right">
            <template #default="{ row }">¥{{ Number(row.product?.supply_price || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</template>
          </el-table-column>
          <el-table-column label="货盘价" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.price" :min="0" :precision="2" size="small" style="width: 110px" @change="handleUpdatePrice(row)" />
            </template>
          </el-table-column>
          <el-table-column label="起订量" width="90">
            <template #default="{ row }">{{ row.min_order_qty }}</template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-select :model-value="row.stock_status" size="small" style="width: 100px" @change="(v: string) => handleUpdateStatus(row, v)">
                <el-option label="鍙緵" value="available" />
                <el-option label="绱紶" value="low_stock" />
                <el-option label="鏂揣" value="sold_out" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-if="catalogs.length === 0" description="鏆傛棤璐洏鏁版嵁" />
    </el-card>

    <!-- 鎵归噺鐢熸垚寮圭獥 -->
    <el-dialog v-model="batchDialogVisible" title="鐢熸垚璐洏" width="600px" destroy-on-close>
      <el-form :model="batchForm" label-width="100px">
        <el-form-item label="货盘名称" required>
          <el-input v-model="batchForm.name" placeholder="如: 2026春季-A级客户" />
        </el-form-item>
        <el-form-item label="客户">
          <el-select v-model="batchForm.customer_id" clearable style="width: 100%">
            <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="折扣率">
          <el-input-number v-model="batchForm.level_discount_rate" :min="0" :max="1" :step="0.05" :precision="2" style="width: 100%" />
          <div style="color: #909399; font-size: 12px">用供应价乘以此折扣率自动算价, 0.8=8折</div>
        </el-form-item>
        <el-form-item label="起订量">
          <el-input-number v-model="batchForm.min_order_qty" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="产品ID">
          <el-input
            v-model="batchForm.selectedProductIds"
            placeholder="杈撳叆产品ID, 閫楀彿鍒嗛殧"
          />
          <div style="color: #909399; font-size: 12px">用供应价乘以此折扣率自动算价, 0.8=8折</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchCreate">鐢熸垚</el-button>
      </template>
    </el-dialog>
  </div>
</template>

