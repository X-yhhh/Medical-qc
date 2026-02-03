<!-- src/views/auth/Login.vue -->
<template>
  <div class="auth-layout">
    <div class="auth-container">
      <!-- Logo / 标题 -->
      <div class="auth-header">
        <h1 class="platform-title">医学影像质控平台</h1>
        <p class="subtitle">Medical Imaging Quality Control System</p>
      </div>

      <el-card class="auth-card" shadow="hover">
        <div class="card-header">
          <h2>用户登录</h2>
        </div>

        <el-form
          :model="form"
          :rules="rules"
          ref="loginFormRef"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="用户名或邮箱" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名或注册邮箱"
              size="large"
              clearable
              prefix-icon="User"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              prefix-icon="Lock"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              style="width: 100%"
              :loading="loading"
              native-type="submit"
            >
              登录
            </el-button>
          </el-form-item>

          <div class="footer-links">
            <span>还没有账号？</span>
            <router-link to="/register" class="link">立即注册</router-link>
          </div>
        </el-form>
      </el-card>

      <div class="auth-footer">© 2026 医影质控平台</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login } from '@/api/auth'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)
const form = ref({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  await loginFormRef.value.validate()
  loading.value = true
  try {
    const res = await login(form.value)
    console.log('🚀 登录响应:', res)

    if (!res?.access_token) {
      throw new Error('No token in response')
    }

    sessionStorage.setItem('access_token', res.access_token)
    if (res.user && typeof res.user === 'object') {
      sessionStorage.setItem('user_info', JSON.stringify(res.user))
    } else {
      console.warn('⚠️ 后端未返回 user 字段，无法显示用户名')
    }
    ElMessage.success('登录成功！')
    router.push('/')
  } catch (error) {
    console.error('❌ 登录失败:', error)

    // ✅ 智能提取错误提示
    let errorMsg = '登录失败，请稍后重试'

    // 优先使用后端返回的 detail
    if (error.response?.data?.detail) {
      errorMsg = error.response.data.detail
    }
    // 其次用网络错误（如超时）
    else if (error.request) {
      errorMsg = '网络连接失败，请检查网络'
    }
    // 最后用 JS 错误
    else if (error.message) {
      errorMsg = error.message
    }

    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-layout {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4edf9 100%);
  padding: 20px;
}

.auth-container {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.platform-title {
  font-size: 28px;
  font-weight: 700;
  color: #1890ff;
  margin: 0 0 8px;
  letter-spacing: 1px;
}

.subtitle {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.auth-card {
  width: 100%;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.card-header {
  padding: 24px 24px 16px;
  text-align: center;
}

.card-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  display: inline-block;
}

:deep(.el-form) {
  padding-top: 8px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #5a5e66;
  padding-bottom: 6px;
  font-size: 14px;
}

:deep(.el-input__wrapper) {
  border: 1px solid #dcdfe6;
}

:deep(.el-input__inner) {
  padding: 10px 16px;
  font-size: 14px;
}

.footer-links {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  color: #606266;
  font-size: 14px;
}

.link {
  color: #1890ff;
  text-decoration: none;
  font-weight: 500;
}

.link:hover {
  color: #409eff;
}

.auth-footer {
  margin-top: 32px;
  color: #909399;
  font-size: 12px;
  text-align: center;
}
</style>
