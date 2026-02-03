<!-- src/views/layout/Layout.vue -->
<template>
  <el-container style="height: 100vh">
    <!-- 顶部导航栏 -->
    <el-header class="header">
      <div class="header-left">医学影像质控平台</div>
      <div class="header-right">
        <el-dropdown @command="handleCommand" placement="bottom-end">
          <span class="user-info">
            <el-icon><User /></el-icon>
            <span class="username">{{ currentUser }}</span>
            <el-icon class="arrow"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout" icon="switch-button"> 退出登录 </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <!-- 主体区域 -->
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="220px" style="background: #333; color: white">
        <el-menu
          router
          background-color="#333"
          text-color="#fff"
          active-text-color="#409EFF"
          :default-active="$route.path"
          class="sidebar-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-menu-item>

          <el-sub-menu index="quality-group">
            <template #title>
              <el-icon><DocumentRemove /></el-icon>
              <span>影像质控</span>
            </template>
            <el-menu-item index="/head">CT头部平扫</el-menu-item>
            <el-menu-item index="/hemorrhage">头部出血检测</el-menu-item>
            <el-menu-item index="/chest-non-contrast">CT胸部平扫</el-menu-item>
            <el-menu-item index="/chest-contrast">CT胸部增强</el-menu-item>
            <el-menu-item index="/coronary-cta">冠脉CTA</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/issues">
            <el-icon><Warning /></el-icon>
            <span>异常汇总</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 页面内容区 -->
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { computed } from 'vue'
import { User, ArrowDown, House, DocumentRemove, Warning } from '@element-plus/icons-vue'

const router = useRouter()

const handleCommand = (command) => {
  if (command === 'logout') {
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('user_info')
    ElMessage.success('已退出登录')
    router.push('/login')
  }
}

const currentUser = computed(() => {
  const userInfoStr = sessionStorage.getItem('user_info')

  // ✅ 先判断是否为有效字符串
  if (!userInfoStr || typeof userInfoStr !== 'string') {
    return '用户'
  }

  try {
    const userInfo = JSON.parse(userInfoStr)

    // ✅ 再判断解析结果是否为对象且不为 null
    if (userInfo && typeof userInfo === 'object' && !Array.isArray(userInfo)) {
      return userInfo.username || userInfo.full_name || '用户'
    } else {
      return '用户'
    }
  } catch (e) {
    console.warn('user_info 解析失败:', e)
    return '用户'
  }
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #409eff;
  color: white;
  padding: 0 20px;
  font-size: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.header-left {
  font-weight: bold;
}
.header-right {
  display: flex;
  align-items: center;
}
.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: white;
  font-size: 14px;
}
.user-info .el-icon {
  margin-right: 6px;
}
.arrow {
  margin-left: 4px;
  font-size: 12px;
}
.sidebar-menu :deep(.el-sub-menu__title) {
  font-weight: normal;
}
.sidebar-menu :deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}
</style>
