<template>
  <div class="register-page">
    <div class="ambient ambient-left"></div>
    <div class="ambient ambient-right"></div>

    <div class="register-shell">
      <section class="register-story">
        <span class="eyebrow">Create Access</span>
        <h1>Create an account for the redesigned workspace</h1>
        <p>
          The visual redesign stays, but the form flow is simplified so account creation
          remains stable and predictable.
        </p>

        <div class="register-points">
          <article class="point-card">
            <strong>One visual system</strong>
            <p>Auth, products, cart, orders, support and admin now feel like one product.</p>
          </article>
          <article class="point-card">
            <strong>Better for demos</strong>
            <p>The interface is closer to a polished commercial product than a typical dashboard.</p>
          </article>
          <article class="point-card">
            <strong>Safer form behavior</strong>
            <p>The register flow uses explicit validation instead of silent submission failures.</p>
          </article>
        </div>
      </section>

      <el-card class="register-card">
        <template #header>
          <div class="card-head">
            <span class="eyebrow">Join Now</span>
            <h2>Create account</h2>
            <p>Set up a username and password to enter the workspace.</p>
          </div>
        </template>

        <el-form label-position="top" @submit.prevent="handleRegister">
          <el-form-item label="Username">
            <el-input v-model.trim="form.username" placeholder="Choose a username" autocomplete="username" />
          </el-form-item>

          <el-form-item label="Password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="Create a password"
              show-password
              autocomplete="new-password"
            />
          </el-form-item>

          <el-form-item label="Confirm password">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="Enter the password again"
              show-password
              autocomplete="new-password"
              @keydown.enter.prevent="handleRegister"
            />
          </el-form-item>

          <el-form-item class="submit-row">
            <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%" @click="handleRegister">
              Create account
            </el-button>
          </el-form-item>

          <el-form-item class="helper-row">
            <el-button text style="width: 100%" @click="goLogin">Back to sign in</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

async function handleRegister() {
  if (loading.value) return

  const username = form.username.trim()
  const password = form.password
  const confirmPassword = form.confirmPassword

  if (!username) {
    ElMessage.warning('Please enter a username')
    return
  }

  if (!password) {
    ElMessage.warning('Please enter a password')
    return
  }

  if (password !== confirmPassword) {
    ElMessage.warning('Passwords do not match')
    return
  }

  loading.value = true

  try {
    const success = await authStore.register({
      username,
      password
    })

    if (success) {
      ElMessage.success('Registration successful. Please sign in.')
      router.push('/login')
      return
    }

    ElMessage.error('Registration failed. Check your input and try again.')
  } finally {
    loading.value = false
  }
}

function goLogin() {
  router.push('/login')
}
</script>

<style scoped>
.register-page {
  position: relative;
  min-height: 100vh;
  padding: 18px;
  overflow: hidden;
}

.ambient {
  position: absolute;
  border-radius: 999px;
  filter: blur(34px);
  pointer-events: none;
}

.ambient-left {
  top: -100px;
  left: -80px;
  width: 280px;
  height: 280px;
  background: rgba(15, 23, 42, 0.12);
}

.ambient-right {
  right: -70px;
  bottom: -100px;
  width: 300px;
  height: 300px;
  background: rgba(0, 113, 227, 0.16);
}

.register-shell {
  position: relative;
  z-index: 1;
  min-height: calc(100vh - 36px);
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, 430px);
  gap: 18px;
}

.register-story {
  padding: 42px;
  border-radius: 34px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.12), transparent 34%),
    linear-gradient(145deg, #071422 0%, #12375f 54%, #0a84ff 100%);
  color: #f8fbff;
  box-shadow: var(--shadow-lg);
}

.register-story :deep(.eyebrow) {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.16);
  color: #f8fbff;
}

.register-story h1 {
  margin: 24px 0 14px;
  font-size: clamp(40px, 4.6vw, 68px);
  line-height: 0.96;
  letter-spacing: -0.06em;
}

.register-story > p {
  margin: 0;
  max-width: 620px;
  color: rgba(248, 251, 255, 0.8);
  font-size: 16px;
  line-height: 1.8;
}

.register-points {
  margin-top: 34px;
  display: grid;
  gap: 14px;
}

.point-card {
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.point-card strong {
  display: block;
  margin-bottom: 8px;
  font-size: 18px;
}

.point-card p {
  margin: 0;
  color: rgba(248, 251, 255, 0.78);
  font-size: 14px;
  line-height: 1.7;
}

.register-card {
  align-self: center;
  padding: 8px;
  border-radius: 30px;
}

.card-head {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card-head h2 {
  margin: 0;
  font-size: 32px;
  line-height: 1;
  letter-spacing: -0.05em;
}

.card-head p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.register-card :deep(.el-card__header) {
  padding: 28px 28px 18px;
}

.register-card :deep(.el-card__body) {
  padding: 18px 28px 28px;
}

.register-card :deep(.el-form-item) {
  margin-bottom: 22px;
}

.register-card :deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-weight: 700;
}

.register-card :deep(.el-input__wrapper) {
  min-height: 50px;
}

.register-card :deep(.el-button--primary) {
  min-height: 50px;
  font-weight: 700;
}

.submit-row {
  margin-top: 8px;
}

.helper-row {
  margin-bottom: 0 !important;
}

.register-card :deep(.el-button.is-text) {
  color: var(--primary);
}

@media (max-width: 1080px) {
  .register-shell {
    grid-template-columns: 1fr;
  }

  .register-card {
    width: min(100%, 460px);
    justify-self: center;
  }
}

@media (max-width: 720px) {
  .register-page {
    padding: 12px;
  }

  .register-story {
    padding: 28px 22px;
  }

  .register-card :deep(.el-card__header),
  .register-card :deep(.el-card__body) {
    padding-left: 20px;
    padding-right: 20px;
  }
}
</style>
