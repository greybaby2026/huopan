<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '../api'
const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
async function handleLogin() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await authApi.login(username.value, password.value)
    localStorage.setItem('huopan_token', res.data.token)
    localStorage.setItem('huopan_user', JSON.stringify(res.data))
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e: any) {
    ElMessage.error('登录失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}
async function handleInitAdmin() {
  try {
    const res = await authApi.initAdmin()
    ElMessage.success(res.data.message)
    username.value = 'admin'
    password.value = 'admin123'
  } catch (e: any) {
    ElMessage.error('初始化失败: ' + (e.response?.data?.detail || e.message))
  }
}
</script>
<template>
  <div style="height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
    <el-card style="width: 400px; border-radius: 8px">
      <div style="text-align: center; margin-bottom: 24px">
        <h2 style="margin: 0; color: #303133">令将货盘系统</h2>
        <p style="color: #909399; margin-top: 8px">请登录</p>
      </div>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" prefix-icon="User" size="large" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" prefix-icon="Lock" size="large" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" size="large" style="width: 100%" :loading="loading" @click="handleLogin">
          登录
        </el-button>
      </el-form>
      <div style="text-align: center; margin-top: 16px">
        <el-button link type="info" @click="handleInitAdmin">初始化管理员账号</el-button>
      </div>
    </el-card>
  </div>
</template>

