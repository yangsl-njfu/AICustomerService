<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>AI客服系统</h2>
      </template>
      
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
        
        <el-form-item>
          <el-button text @click="handleRegister" style="width: 100%">
            还没有账号？去注册
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    loading.value = true
    const success = await authStore.login(form)
    loading.value = false

    if (success) {
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error('登录失败，请检查用户名和密码')
    }
  })
}

const handleRegister = () => {
  router.push('/register')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100vw;
  height: 100vh;
  background: radial-gradient(circle at top, rgba(56, 189, 248, 0.18), transparent 45%), var(--bg);
}

.login-card {
  width: 400px;
  background: var(--surface);
  border-radius: 16px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.login-card h2 {
  text-align: center;
  margin: 0;
  color: var(--text);
  font-weight: 700;
  letter-spacing: 0.4px;
}

.login-card :deep(.el-card__header) {
  border-bottom: 1px solid var(--border);
}

.login-card :deep(.el-card__body) {
  background: var(--surface);
}

.login-card :deep(.el-form-item__label) {
  color: var(--muted);
}

.login-card :deep(.el-input__wrapper) {
  background: var(--surface-2);
  border: 1px solid var(--border);
  box-shadow: none;
}

.login-card :deep(.el-input__inner) {
  color: var(--text);
}

.login-card :deep(.el-input__inner::placeholder) {
  color: rgba(148, 163, 184, 0.6);
}

.login-card :deep(.el-button--primary) {
  background: rgba(56, 189, 248, 0.2);
  border: 1px solid rgba(56, 189, 248, 0.45);
  color: var(--text);
  font-weight: 600;
  border-radius: 12px;
}

.login-card :deep(.el-button.is-text) {
  color: var(--accent);
}
</style>
