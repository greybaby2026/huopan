<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Box, User, Document, Grid, UserFilled, List, Coin, DataAnalysis, SwitchButton } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)

const userInfo = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('huopan_user') || '{}')
  } catch {
    return {}
  }
})

const roleMap: Record<string, string> = {
  admin: '管理员',
  sales: '业务员',
  warehouse: '仓库',
}

function handleLogout() {
  localStorage.removeItem('huopan_token')
  localStorage.removeItem('huopan_user')
  router.push('/login')
}
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '200px'" style="background: #304156">
      <div style="height: 60px; display: flex; align-items: center; justify-content: center; color: #fff">
        <span v-if="!isCollapse" style="font-size: 16px; font-weight: bold">浠ゅ皢璐х洏绯荤粺</span>
        <el-icon v-else :size="24"><Box /></el-icon>
      </div>
      <el-menu
        :default-active="route.path"
        router
        :collapse="isCollapse"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据控制台</span>
        </el-menu-item>
        <el-menu-item index="/products">
          <el-icon><Box /></el-icon>
          <span>产品库</span>
        </el-menu-item>
        <el-menu-item index="/customers">
          <el-icon><User /></el-icon>
          <span>客户管理</span>
        </el-menu-item>
        <el-menu-item index="/catalogs">
          <el-icon><Document /></el-icon>
          <span>货盘管理</span>
        </el-menu-item>
        <el-menu-item index="/spreadsheet">
          <el-icon><Grid /></el-icon>
          <span>货盘排版</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/logs">
          <el-icon><List /></el-icon>
          <span>操作日志</span>
        </el-menu-item>
        <el-menu-item index="/dicts">
          <el-icon><Coin /></el-icon>
          <span>品类灏虹爜</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="background: #fff; border-bottom: 1px solid #e6e6e6; display: flex; align-items: center; justify-content: space-between">
        <div style="display: flex; align-items: center; gap: 12px">
          <el-icon :size="20" style="cursor: pointer" @click="isCollapse = !isCollapse">
            <component :is="isCollapse ? 'Expand' : 'Fold'" />
          </el-icon>
          <span style="font-size: 18px; font-weight: 500">{{ route.meta.title }}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px">
          <el-tag type="info" size="small">{{ roleMap[userInfo.role] || userInfo.role }}</el-tag>
          <span style="font-size: 14px; color: #606266">{{ userInfo.display_name || userInfo.username }}</span>
          <el-button :icon="SwitchButton" link @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main style="background: #f0f2f5; padding: 16px">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

