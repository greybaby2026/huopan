<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { VxeTableInstance } from 'vxe-table'
import { productsApi, UPLOAD_BASE } from '../api'

interface ProductImage {
  id: number
  original_path: string
  thumbnail_path: string | null
  sort_order: number
}

interface Product {
  id: number
  sku_code: string
  name: string
  category: string | null
  color: string | null
  pattern: string | null
  season: string | null
  style: string | null
  fabric: string | null
  size_range: string | null
  cost_price: number
  retail_price: number
  supply_price: number
  stock: number
  status: string
  note: string | null
  created_at: string
  updated_at: string
  images: ProductImage[]
}

const tableData = ref<Product[]>([])
const loading = ref(false)
const total = ref(0)
const page = reactive({ currentPage: 1, pageSize: 20 })

const searchForm = reactive({
  keyword: '',
  category: '',
  color: '',
  season: '',
  status: '',
})

const categoryOptions = ref<string[]>([])
const xTable = ref<VxeTableInstance>()

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '鑽夌', type: 'info' },
  active: { label: '涓婃灦', type: 'success' },
  archived: { label: '褰掓', type: 'danger' },
}

const dialogVisible = ref(false)
const dialogTitle = ref('')
const editingProduct = ref<Partial<Product>>({})
const isEdit = ref(false)

const imageDialogVisible = ref(false)
const imageProductId = ref<number>(0)
const imageProductName = ref('')
const uploadedFiles = ref<File[]>([])

const selectedRows = ref<Product[]>([])

const batchDialogVisible = ref(false)
const batchForm = reactive({
  type: 'percent' as 'percent' | 'fixed',
  value: 0,
  field: 'supply_price' as 'supply_price' | 'cost_price',
})

// Excel 瀵煎叆寮圭獥
const importDialogVisible = ref(false)
const importFile = ref<File | null>(null)
const importResult = ref<{ created: number; skipped: number; errors: string[] } | null>(null)
const importing = ref(false)

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.currentPage,
      page_size: page.pageSize,
    }
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.category) params.category = searchForm.category
    if (searchForm.color) params.color = searchForm.color
    if (searchForm.season) params.season = searchForm.season
    if (searchForm.status) params.status = searchForm.status

    const res = await productsApi.list(params)
    tableData.value = res.data.items
    total.value = res.data.total
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const res = await productsApi.categories()
    categoryOptions.value = res.data.categories
  } catch {
    // 蹇界暐
  }
}

function handleSearch() {
  page.currentPage = 1
  loadData()
}

function handleReset() {
  Object.assign(searchForm, { keyword: '', category: '', color: '', season: '', status: '' })
  handleSearch()
}

function handleAdd() {
  isEdit.value = false
  dialogTitle.value = '新增产品'
  editingProduct.value = {
    sku_code: '', name: '', category: '', color: '', pattern: '',
    season: '', style: '', fabric: '', size_range: '',
    cost_price: 0, supply_price: 0, retail_price: 0, stock: 0, status: 'draft', note: '',
  }
  dialogVisible.value = true
}

function handleEdit(row: Product) {
  isEdit.value = true
  dialogTitle.value = '编辑产品'
  editingProduct.value = { ...row }
  dialogVisible.value = true
}

async function handleSave() {
  if (!editingProduct.value.sku_code || !editingProduct.value.name) {
    ElMessage.warning('货号和名称必填')
    return
  }
  try {
    if (isEdit.value && editingProduct.value.id) {
      await productsApi.update(editingProduct.value.id, editingProduct.value)
      ElMessage.success('鏇存柊鎴愬姛')
    } else {
      await productsApi.create(editingProduct.value)
      ElMessage.success('鍒涘缓鎴愬姛')
    }
    dialogVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error('保存澶辫触: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleDelete(row: Product) {
  try {
    await ElMessageBox.confirm('确定删除 ' + row.sku_code + ' ' + row.name + '?', '提示', { type: 'warning' })
    await productsApi.delete(row.id)
    ElMessage.success('已删除')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('删除澶辫触: ' + (e.response?.data?.detail || e.message))
  }
}

function handleImages(row: Product) {
  imageProductId.value = row.id
  imageProductName.value = `${row.sku_code} ${row.name}`
  uploadedFiles.value = []
  imageDialogVisible.value = true
}

function handleFileChange(file: any) {
  if (file.raw) uploadedFiles.value.push(file.raw)
}

async function handleUploadImages() {
  if (uploadedFiles.value.length === 0) {
    ElMessage.warning('请先选择图片')
    return
  }
  try {
    await productsApi.uploadImages(imageProductId.value, uploadedFiles.value)
    ElMessage.success('已成功上传 ' + uploadedFiles.value.length + ' 张图片')
    imageDialogVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error('涓婁紶澶辫触: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleDeleteImage(productId: number, imageId: number) {
  try {
    await productsApi.deleteImage(productId, imageId)
    ElMessage.success('图片已删除')
    loadData()
  } catch (e: any) {
    ElMessage.error('删除澶辫触: ' + e.message)
  }
}

function handleSelectionChange({ records }: any) {
  selectedRows.value = records || []
}

function handleBatchPrice() {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('璇峰厛閫夋嫨产品')
    return
  }
  batchDialogVisible.value = true
}

async function handleBatchUpdate() {
  const ids = selectedRows.value.map((r) => r.id)
  try {
    if (batchForm.type === 'percent') {
      for (const row of selectedRows.value) {
        const oldValue = (row as any)[batchForm.field] || 0
        const newValue = Number((oldValue * (1 + batchForm.value / 100)).toFixed(2))
        await productsApi.update(row.id, { [batchForm.field]: newValue })
      }
    } else {
      await productsApi.batchUpdate(ids, { [batchForm.field]: batchForm.value })
    }
    ElMessage.success('\\u5df2\\u6279\\u91cf\\u8c03\\u6574 ' + ids.length + ' \\u4e2a\\u4ea7\\u54c1')
    batchDialogVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error('批量更新失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleBatchStatus(status: string) {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('璇峰厛閫夋嫨产品')
    return
  }
  const ids = selectedRows.value.map((r) => r.id)
  try {
    await productsApi.batchUpdate(ids, { status })
    ElMessage.success('已更新 ' + ids.length + ' 个产品状态')
    loadData()
  } catch (e: any) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 涓嬭浇瀵煎叆妯澘
function handleDownloadTemplate() {
  window.open(productsApi.importTemplate(), '_blank')
}

// 瀵煎叆鏂囦欢閫夋嫨
function handleImportFileChange(file: any) {
  importFile.value = file.raw
}

// 鎵瀵煎叆
async function handleImport() {
  if (!importFile.value) {
    ElMessage.warning('璇峰厛閫夋嫨鏂囦欢')
    return
  }
  importing.value = true
  importResult.value = null
  try {
    const res = await productsApi.importProducts(importFile.value)
    importResult.value = res.data
    ElMessage.success(res.data.message)
    loadData()
  } catch (e: any) {
    ElMessage.error('瀵煎叆澶辫触: ' + (e.response?.data?.detail || e.message))
  } finally {
    importing.value = false
  }
}

function imageUrl(path: string | null): string {
  if (!path) return ''
  return `${UPLOAD_BASE}/uploads/${path}`
}

function handlePageChange({ currentPage, pageSize }: any) {
  page.currentPage = currentPage
  page.pageSize = pageSize
  loadData()
}

onMounted(() => {
  loadCategories()
  loadData()
})
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 12px">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="货号/名称" clearable style="width: 160px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="品类">
          <el-select v-model="searchForm.category" clearable placeholder="全部" style="width: 120px">
            <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="颜色">
          <el-input v-model="searchForm.color" clearable style="width: 100px" />
        </el-form-item>
        <el-form-item label="季节">
          <el-select v-model="searchForm.season" clearable style="width: 100px">
            <el-option label="春" value="春" />
            <el-option label="夏" value="夏" />
            <el-option label="秋" value="秋" />
            <el-option label="冬" value="冬" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" clearable style="width: 100px">
            <el-option label="草稿" value="draft" />
            <el-option label="上架" value="active" />
            <el-option label="归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" style="margin-bottom: 12px">
      <div style="display: flex; gap: 8px">
        <el-button type="primary" @click="handleAdd">新增产品</el-button>
        <el-button @click="handleBatchPrice">鎵归噺鏀逛环</el-button>
        <el-button @click="handleBatchStatus('active')">鎵归噺涓婃灦</el-button>
        <el-button @click="handleBatchStatus('archived')">鎵归噺褰掓</el-button>
        <el-button @click="importDialogVisible = true">Excel瀵煎叆</el-button>
        <el-button @click="handleDownloadTemplate">涓嬭浇妯澘</el-button>
        <span style="flex: 1"></span>
        <span style="color: #909399; line-height: 32px">共 {{ total }} 条</span>
      </div>
    </el-card>

    <el-card shadow="never">
      <vxe-table
        ref="xTable"
        :data="tableData"
        :loading="loading"
        height="600"
        :row-config="{ isHover: true }"
        :column-config="{ resizable: true }"
        :checkbox-config="{ range: true }"
        @checkbox-change="handleSelectionChange"
        @checkbox-all="handleSelectionChange"
      >
        <vxe-column type="checkbox" width="50" />
        <vxe-column type="seq" title="#" width="50" />
        <vxe-column field="images" title="图片" width="80">
          <template #default="{ row }">
            <el-image
              v-if="row.images && row.images.length > 0"
              :src="imageUrl(row.images[0].thumbnail_path || row.images[0].original_path)"
              :preview-src-list="row.images.map((img: ProductImage) => imageUrl(img.original_path))"
              fit="cover"
              style="width: 50px; height: 50px; border-radius: 4px"
              :preview-teleported="true"
            />
            <span v-else style="color: #c0c4cc">无图</span>
          </template>
        </vxe-column>
        <vxe-column field="sku_code" title="娆惧彿" width="120" sortable />
        <vxe-column field="name" title="鍚嶇" min-width="150" />
        <vxe-column field="category" title="品类" width="100" sortable />
        <vxe-column field="color" title="颜色" width="80" />
        <vxe-column field="season" title="季节" width="70" />
        <vxe-column field="size_range" title="尺码" width="120" />
        <vxe-column field="cost_price" title="成本价" width="90" align="right" sortable>
          <template #default="{ row }">¥{{ row.cost_price?.toFixed(2) }}</template>
        </vxe-column>
        <vxe-column field="supply_price" title="供应价" width="90" align="right" sortable>
          <template #default="{ row }">¥{{ Number(row.supply_price || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</template>
        </vxe-column>
        <vxe-column field="stock" title="库存" width="80" align="right" sortable />
        <vxe-column field="status" title="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type" size="small">
              {{ statusMap[row.status]?.label }}
            </el-tag>
          </template>
        </vxe-column>
        <vxe-column title="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" link type="primary" @click="handleImages(row)">图片</el-button>
            <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </vxe-column>
      </vxe-table>

      <vxe-pager
        :current-page="page.currentPage"
        :page-size="page.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        @page-change="handlePageChange"
        style="margin-top: 12px"
      />
    </el-card>

    <!-- 新增/编辑寮圭獥 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" destroy-on-close>
      <el-form :model="editingProduct" label-width="80px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="娆惧彿" required>
              <el-input v-model="editingProduct.sku_code" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="鍚嶇" required>
              <el-input v-model="editingProduct.name" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="品类">
              <el-select v-model="editingProduct.category" filterable allow-create style="width: 100%">
                <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="颜色">
              <el-input v-model="editingProduct.color" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="季节">
              <el-select v-model="editingProduct.season" style="width: 100%">
                <el-option label="鏄? value="鏄? />
                <el-option label="澶? value="澶? />
                <el-option label="绉? value="绉? />
                <el-option label="鍐? value="鍐? />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="鑺卞瀷">
              <el-input v-model="editingProduct.pattern" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="椋庢牸">
              <el-input v-model="editingProduct.style" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="闈枡">
              <el-input v-model="editingProduct.fabric" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="成本价">
              <el-input-number v-model="editingProduct.cost_price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="供应价">
              <el-input-number v-model="editingProduct.supply_price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="零售价">
              <el-input-number v-model="editingProduct.retail_price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="搴撳瓨">
              <el-input-number v-model="editingProduct.stock" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="灏虹爜">
              <el-input v-model="editingProduct.size_range" placeholder="S,M,L,XL" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="editingProduct.status" style="width: 100%">
                <el-option label="鑽夌" value="draft" />
                <el-option label="涓婃灦" value="active" />
                <el-option label="褰掓" value="archived" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="澶囨敞">
          <el-input v-model="editingProduct.note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 鎵归噺鏀逛环寮圭獥 -->
    <el-dialog v-model="batchDialogVisible" title="鎵归噺鏀逛环" width="400px">
      <el-form :model="batchForm" label-width="80px">
        <el-form-item label="鏀逛环瀛楁">
          <el-radio-group v-model="batchForm.field">
            <el-radio value="supply_price">供应价</el-radio>
            <el-radio value="cost_price">成本价</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="璋冩暣鏂瑰紡">
          <el-radio-group v-model="batchForm.type">
            <el-radio value="percent">百分比(%)</el-radio>
            <el-radio value="fixed">固定值</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="数值">
          <el-input-number v-model="batchForm.value" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchUpdate">确定</el-button>
      </template>
    </el-dialog>

    <!-- Excel 瀵煎叆寮圭獥 -->
    <el-dialog v-model="importDialogVisible" title="Excel 鎵归噺瀵煎叆产品" width="500px" destroy-on-close>
      <el-alert type="info" :closable="false" style="margin-bottom: 12px">
        鍏堜笅杞芥鏉垮鍐? 鍐嶄笂浼犲鍏傚凡瀛樺湪鐨勬鍙疯嚜鍔烦杩囥?      </el-alert>
      <el-upload
        action="#"
        :auto-upload="false"
        :on-change="handleImportFileChange"
        accept=".xlsx,.xls"
        :limit="1"
      >
        <el-button type="primary">閫夋嫨 Excel 鏂囦欢</el-button>
        <template #tip>
          <div style="color: #909399; font-size: 12px">浠呮敮鎸?.xlsx 鏍煎紡</div>
        </template>
      </el-upload>
      <div v-if="importResult" style="margin-top: 12px">
        <el-alert
          :type="importResult.errors.length > 0 ? 'warning' : 'success'"
          :title="'新增 ' + importResult.created + ' 个, 跳过 ' + importResult.skipped + ' 个'"
          :closable="false"
        />
        <div v-if="importResult.errors.length > 0" style="margin-top: 8px; max-height: 150px; overflow-y: auto">
          <div v-for="(err, i) in importResult.errors" :key="i" style="color: #e6a23c; font-size: 12px">
            {{ err }}
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleImport" :loading="importing">开始导入</el-button>
      </template>
    </el-dialog>

    <!-- 图片绠悊寮圭獥 -->
    <el-dialog v-model="imageDialogVisible" :title="'图片管理 - ' + imageProductName" width="600px">
      <el-upload
        action="#"
        :auto-upload="false"
        :on-change="handleFileChange"
        multiple
        accept="image/jpeg,image/png,image/webp"
        list-type="picture"
      >
        <el-button type="primary">閫夋嫨图片</el-button>
        <template #tip>
          <div style="color: #909399; font-size: 12px">鏀寔 JPG/PNG/WebP, 鍗曞紶鏈澶?10MB</div>
        </template>
      </el-upload>
      <el-divider />
      <div v-if="imageProductId">
        <h4>宸叉湁图片</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 8px">
          <div
            v-for="img in tableData.find(p => p.id === imageProductId)?.images || []"
            :key="img.id"
            style="position: relative"
          >
            <el-image
              :src="imageUrl(img.thumbnail_path || img.original_path)"
              :preview-src-list="[imageUrl(img.original_path)]"
              fit="cover"
              style="width: 100px; height: 100px; border-radius: 4px; border: 1px solid #e4e7ed"
              :preview-teleported="true"
            />
            <el-button
              size="small"
              type="danger"
              circle
              :icon="'Delete'"
              style="position: absolute; top: -8px; right: -8px"
              @click="handleDeleteImage(imageProductId, img.id)"
            />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="imageDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUploadImages">涓婁紶閫変腑图片</el-button>
      </template>
    </el-dialog>
  </div>
</template>

