<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <h2>注册账号</h2>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleRegister" :loading="loading" style="width: 100%">
            注册
          </el-button>
        </el-form-item>

        <el-form-item>
          <el-button text @click="goLogin" style="width: 100%">
            已有账号？去登录
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
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (_: any, value: string, callback: any) => {
  if (!value) {
    callback(new Error('请确认密码'))
    return
  }
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  callback()
}

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: validateConfirmPassword, trigger: 'blur' }]
}

const handleRegister = async () => {
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    const success = await authStore.register({
      username: form.username,
      password: form.password
    })
    loading.value = false
    if (success) {
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } else {
      ElMessage.error('注册失败，请检查信息或用户名是否已存在')
    }
  })
}

const goLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100vw;
  height: 100vh;
  background: radial-gradient(circle at top, rgba(56, 189, 248, 0.18), transparent 45%), var(--bg);
}

.register-card {
  width: 420px;
  background: var(--surface);
  border-radius: 16px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.register-card h2 {
  text-align: center;
  margin: 0;
  color: var(--text);
  font-weight: 700;
  letter-spacing: 0.4px;
}

.register-card :deep(.el-card__header) {
  border-bottom: 1px solid var(--border);
}

.register-card :deep(.el-card__body) {
  background: var(--surface);
}

.register-card :deep(.el-form-item__label) {
  color: var(--muted);
}

.register-card :deep(.el-input__wrapper) {
  background: var(--surface-2);
  border: 1px solid var(--border);
  box-shadow: none;
}

.register-card :deep(.el-input__inner) {
  color: var(--text);
}

.register-card :deep(.el-input__inner::placeholder) {
  color: rgba(148, 163, 184, 0.6);
}

.register-card :deep(.el-button--primary) {
  background: rgba(56, 189, 248, 0.2);
  border: 1px solid rgba(56, 189, 248, 0.45);
  color: var(--text);
  font-weight: 600;
  border-radius: 12px;
}

.register-card :deep(.el-button.is-text) {
  color: var(--accent);
}
</style>
