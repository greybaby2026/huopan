<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authApi } from '../api'
interface DictItem {
  id: number
  name: string
  sort_order: number
}
const activeTab = ref('categories')
const categories = ref<DictItem[]>([])
const sizes = ref<DictItem[]>([])
const loading = ref(false)
const newName = ref('')
const newSort = ref(0)
// API
const dictApi = {
  categories: () => authApi.listLogs ? (() => { throw 'use direct axios' })() : null
}
async function loadCategories() {
  loading.value = true
  try {
    const res = await authApi.listDicts('categories')
    categories.value = res.data.items
  } catch (e: any) {
    ElMessage.error('加载品类失败: ' + (e.response?.data?.detail || e.message))
  } finally { loading.value = false }
}
async function loadSizes() {
  loading.value = true
  try {
    const res = await authApi.listDicts('sizes')
    sizes.value = res.data.items
  } catch (e: any) {
    ElMessage.error('加载尺码失败: ' + (e.response?.data?.detail || e.message))
  } finally { loading.value = false }
}
async function addCategory() {
  if (!newName.value.trim()) { ElMessage.warning('请输入品类名称'); return }
  try {
    await authApi.createDict('categories', { name: newName.value.trim(), sort_order: newSort.value })
    ElMessage.success('添加成功')
    newName.value = ''; newSort.value = 0
    loadCategories()
  } catch (e: any) {
    ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message))
  }
}
async function deleteCategory(id: number) {
  try {
    await ElMessageBox.confirm('确定删除?', '提示', { type: 'warning' })
    await authApi.deleteDict('categories', id)
    ElMessage.success('已删除')
    loadCategories()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}
async function addSize() {
  if (!newName.value.trim()) { ElMessage.warning('请输入尺码'); return }
  try {
    await authApi.createDict('sizes', { name: newName.value.trim(), sort_order: newSort.value })
    ElMessage.success('添加成功')
    newName.value = ''; newSort.value = 0
    loadSizes()
  } catch (e: any) {
    ElMessage.error('添加失败: ' + (e.response?.data?.detail || e.message))
  }
}
async function deleteSize(id: number) {
  try {
    await ElMessageBox.confirm('确定删除?', '提示', { type: 'warning' })
    await authApi.deleteDict('sizes', id)
    ElMessage.success('已删除')
    loadSizes()
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}
onMounted(() => {
  loadCategories()
  loadSizes()
})
</script>
<template>
  <el-tabs v-model="activeTab">
    <el-tab-pane label="品类库" name="categories">
      <el-card shadow="never" style="margin-bottom: 12px">
        <el-form :inline="true">
          <el-form-item label="品类名称">
            <el-input v-model="newName" placeholder="如: 衬衫/卫衣/夹克" clearable />
          </el-form-item>
          <el-form-item label="排序">
            <el-input-number v-model="newSort" :min="0" />
          </el-form-item>
          <el-button type="primary" @click="addCategory">添加品类</el-button>
        </el-form>
      </el-card>
      <el-card shadow="never" v-loading="loading">
        <el-table :data="categories" border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="品类名称" min-width="200" />
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" link type="danger" @click="deleteCategory(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-tab-pane>
    <el-tab-pane label="尺码库" name="sizes">
      <el-card shadow="never" style="margin-bottom: 12px">
        <el-form :inline="true">
          <el-form-item label="尺码">
            <el-input v-model="newName" placeholder="如: S/M/L/XL/XXL" clearable />
          </el-form-item>
          <el-form-item label="排序">
            <el-input-number v-model="newSort" :min="0" />
          </el-form-item>
          <el-button type="primary" @click="addSize">添加尺码</el-button>
        </el-form>
      </el-card>
      <el-card shadow="never" v-loading="loading">
        <el-table :data="sizes" border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="尺码" min-width="200" />
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button size="small" link type="danger" @click="deleteSize(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-tab-pane>
  </el-tabs>
</template>

