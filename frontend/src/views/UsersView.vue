<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authApi } from '../api'

interface User {
  id: number
  username: string
  display_name: string | null
  role: string
  is_active: boolean
  assigned_customer_ids: string | null
}

const users = ref<User[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingUser = ref<{ id?: number; username: string; password: string; display_name: string; role: string }>({
  username: '', password: '', display_name: '', role: 'sales',
})

const roleMap: Record<string, string> = {
  admin: '管理员',
  sales: '业务员',
  warehouse: '仓库',
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await authApi.listUsers()
    users.value = res.data.items
  } catch (e: any) {
    ElMessage.error('加载失败: ' + (e.response?.data?.detail || e.message))
  } finally { loading.value = false }
}

function handleAdd() {
  isEdit.value = false
  editingUser.value = { username: '', password: '', display_name: '', role: 'sales' }
  dialogVisible.value = true
}

function handleEdit(row: User) {
  isEdit.value = true
  editingUser.value = { id: row.id, username: row.username, password: '', display_name: row.display_name || '', role: row.role }
  dialogVisible.value = true
}

async function handleSave() {
  if (!editingUser.value.username) { ElMessage.warning('用户名必填'); return }
  try {
    if (isEdit.value && editingUser.value.id) {
      await authApi.updateUser(editingUser.value.id, {
        username: editingUser.value.username,
        password: editingUser.value.password,
        display_name: editingUser.value.display_name,
        role: editingUser.value.role,
      })
      ElMessage.success('更新成功')
    } else {
      if (!editingUser.value.password) { ElMessage.warning('密码必填'); return }
      await authApi.createUser({
        username: editingUser.value.username,
        password: editingUser.value.password,
        display_name: editingUser.value.display_name || undefined,
        role: editingUser.value.role,
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
  } catch (e: any) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function handleToggleActive(row: User) {
  try {
    const res = await authApi.toggleActive(row.id)
    ElMessage.success(res.data.is_active ? '已启用' : '已停用')
    loadUsers()
  } catch (e: any) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(loadUsers)
</script>

<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 12px">
      <el-button type="success" @click="handleAdd">新增鐢埛</el-button>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <el-table :data="users" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="display_name" label="显示名" width="150" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">{{ roleMap[row.role] || row.role }}</template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '鍚敤' : '鍋滅敤' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" link @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" link :type="row.is_active ? 'warning' : 'success'" @click="handleToggleActive(row)">
              {{ row.is_active ? '鍋滅敤' : '鍚敤' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑鐢埛' : '新增鐢埛'" width="400px" destroy-on-close>
      <el-form :model="editingUser" label-width="80px">
        <el-form-item label="用户名" required><el-input v-model="editingUser.username" /></el-form-item>
        <el-form-item :label="isEdit ? '新密码' : '密码'" :required="!isEdit">
          <el-input v-model="editingUser.password" type="password" show-password :placeholder="isEdit ? '留空不修改' : ''" /></el-form-item>
        <el-form-item label="显示名"><el-input v-model="editingUser.display_name" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editingUser.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="业务员" value="sales" />
            <el-option label="仓库" value="warehouse" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

