<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { customersApi } from '../api'

interface CustomerLevel {
  id: number
  name: string
  discount_rate: number
  default_min_qty: number
  sort_order: number
}

interface Customer {
  id: number
  name: string
  company: string | null
  contact: string | null
  phone: string | null
  address: string | null
  level_id: number | null
  is_active: boolean
  note: string | null
  created_at: string
  updated_at: string
}

const activeTab = ref('customers')
const levels = ref<CustomerLevel[]>([])
const customers = ref<Customer[]>([])
const loading = ref(false)

const searchKeyword = ref('')

const dialogVisible = ref(false)
const dialogTitle = ref('')
const editingCustomer = ref<Partial<Customer>>({})
const isEdit = ref(false)

const levelDialogVisible = ref(false)
const editingLevel = ref<Partial<CustomerLevel>>({})

async function loadLevels() {
  try {
    const res = await customersApi.levels()
    levels.value = res.data
  } catch (e: any) {
    ElMessage.error('加载失败: ' + e.message)
  }
}

async function loadCustomers() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (searchKeyword.value) params.keyword = searchKeyword.value
    const res = await customersApi.list(params)
    customers.value = res.data
  } catch (e: any) {
    ElMessage.error('加载失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

function levelName(id: number | null): string {
  if (!id) return '-'
  const level = levels.value.find((l) => l.id === id)
  return level ? `${level.name}(${(level.discount_rate * 10).toFixed(1)}折` : '-'
}

function handleAdd() {
  isEdit.value = false
  dialogTitle.value = '新增客户'
  editingCustomer.value = { name: '', company: '', contact: '', phone: '', address: '', level_id: null, is_active: true, note: '' }
  dialogVisible.value = true
}

function handleEdit(row: Customer) {
  isEdit.value = true
  dialogTitle.value = '编辑客户'
  editingCustomer.value = { ...row }
  dialogVisible.value = true
}

async function handleSave() {
  if (!editingCustomer.value.name) {
    ElMessage.warning('客户名称必填')
    return
  }
  try {
    if (isEdit.value && editingCustomer.value.id) {
      await customersApi.update(editingCustomer.value.id, editingCustomer.value)
      ElMessage.success('更新成功')
    } else {
      await customersApi.create(editingCustomer.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadCustomers()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleDelete(row: Customer) {
  try {
    await ElMessageBox.confirm(`确定删除客户 ${row.name}?`, '提示', { type: 'warning' })
    await customersApi.delete(row.id)
    ElMessage.success('已删除')
    loadCustomers()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('删除失败: ' + e.message)
  }
}

function handleAddLevel() {
  editingLevel.value = { name: '', discount_rate: 1.0, default_min_qty: 1, sort_order: 0 }
  levelDialogVisible.value = true
}

function handleEditLevel(row: CustomerLevel) {
  editingLevel.value = { ...row }
  levelDialogVisible.value = true
}

async function handleSaveLevel() {
  if (!editingLevel.value.name) {
    ElMessage.warning('级别名称必填')
    return
  }
  try {
    if (editingLevel.value.id) {
      await customersApi.updateLevel(editingLevel.value.id, editingLevel.value)
      ElMessage.success('更新成功')
    } else {
      await customersApi.createLevel(editingLevel.value)
      ElMessage.success('创建成功')
    }
    levelDialogVisible.value = false
    loadLevels()
  } catch (e: any) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleDeleteLevel(row: CustomerLevel) {
  try {
    await ElMessageBox.confirm(`确定删除级别 ${row.name}?`, '提示', { type: 'warning' })
    await customersApi.deleteLevel(row.id)
    ElMessage.success('已删除')
    loadLevels()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('删除失败: ' + e.message)
  }
}

onMounted(() => {
  loadLevels()
  loadCustomers()
})
</script>

<template>
  <el-tabs v-model="activeTab">
    <!-- 客户列表 -->
    <el-tab-pane label="客户列表" name="customers">
      <el-card shadow="never" style="margin-bottom: 12px">
        <div style="display: flex; gap: 8px">
          <el-input v-model="searchKeyword" placeholder="搜索客户名称/公司/联系人" clearable style="width: 240px" @keyup.enter="loadCustomers" />
          <el-button type="primary" @click="loadCustomers">搜索</el-button>
          <el-button type="success" @click="handleAdd">新增客户</el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <el-table :data="customers" v-loading="loading" border style="width: 100%">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="name" label="客户名称" width="150" />
          <el-table-column prop="company" label="公司" width="150" />
          <el-table-column prop="contact" label="联系人" width="100" />
          <el-table-column prop="phone" label="电话" width="130" />
          <el-table-column label="级别" width="120">
            <template #default="{ row }">{{ levelName(row.level_id) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="note" label="备注" min-width="120" show-overflow-tooltip />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" link @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-tab-pane>

    <!-- 客户分级 -->
    <el-tab-pane label="客户分级" name="levels">
      <el-card shadow="never" style="margin-bottom: 12px">
        <el-button type="success" @click="handleAddLevel">新增级别</el-button>
      </el-card>
      <el-card shadow="never">
        <el-table :data="levels" border style="width: 100%">
          <el-table-column prop="name" label="级别名称" width="120" />
          <el-table-column label="折扣率" width="120">
            <template #default="{ row }">{{ (row.discount_rate * 10).toFixed(1) }}折({{ (row.discount_rate * 100).toFixed(0) }}%)</template>
          </el-table-column>
          <el-table-column prop="default_min_qty" label="默认起订量" width="130" />
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" link @click="handleEditLevel(row)">编辑</el-button>
              <el-button size="small" link type="danger" @click="handleDeleteLevel(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-tab-pane>
  </el-tabs>

  <!-- 客户弹窗 -->
  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px" destroy-on-close>
    <el-form :model="editingCustomer" label-width="80px">
      <el-form-item label="名称" required><el-input v-model="editingCustomer.name" /></el-form-item>
      <el-form-item label="公司"><el-input v-model="editingCustomer.company" /></el-form-item>
      <el-form-item label="联系人"><el-input v-model="editingCustomer.contact" /></el-form-item>
      <el-form-item label="电话"><el-input v-model="editingCustomer.phone" /></el-form-item>
      <el-form-item label="地址"><el-input v-model="editingCustomer.address" /></el-form-item>
      <el-form-item label="级别">
        <el-select v-model="editingCustomer.level_id" clearable style="width: 100%">
          <el-option v-for="l in levels" :key="l.id" :label="`${l.name} (${(l.discount_rate * 10).toFixed(1)}折`" :value="l.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-switch v-model="editingCustomer.is_active" />
      </el-form-item>
      <el-form-item label="备注"><el-input v-model="editingCustomer.note" type="textarea" :rows="2" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>

  <!-- 级别弹窗 -->
  <el-dialog v-model="levelDialogVisible" :title="editingLevel.id ? '编辑级别' : '新增级别'" width="400px" destroy-on-close>
    <el-form :model="editingLevel" label-width="100px">
      <el-form-item label="级别名称" required><el-input v-model="editingLevel.name" placeholder="A/B/C" /></el-form-item>
      <el-form-item label="折扣率">
        <el-input-number v-model="editingLevel.discount_rate" :min="0" :max="1" :step="0.05" :precision="2" style="width: 100%" />
        <div style="color: #909399; font-size: 12px">1.0=原价, 0.8=8折</div>
      </el-form-item>
      <el-form-item label="默认起订量">
        <el-input-number v-model="editingLevel.default_min_qty" :min="1" style="width: 100%" />
      </el-form-item>
      <el-form-item label="排序">
        <el-input-number v-model="editingLevel.sort_order" style="width: 100%" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="levelDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSaveLevel">保存</el-button>
    </template>
  </el-dialog>
</template>

