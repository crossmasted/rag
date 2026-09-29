<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">{{ isRegister ? '注册账号' : '登录' }}</h2>
      <p class="login-sub">RAG 知识库问答系统</p>

      <el-form @submit.prevent="submit" :model="form">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="用户名（2-50 字符）"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码（至少 6 位）"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="submit"
          />
        </el-form-item>
        <el-button
          type="primary"
          class="submit-btn"
          :loading="loading"
          @click="submit"
        >
          {{ isRegister ? '注册并登录' : '登录' }}
        </el-button>
      </el-form>

      <div class="switch-line">
        <el-link type="primary" @click="toggleMode">
          {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
        </el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { login, register } from '../api'

const emit = defineEmits(['logged-in'])

const form = ref({ username: '', password: '' })
const loading = ref(false)
const isRegister = ref(false)

const toggleMode = () => {
  isRegister.value = !isRegister.value
  form.value.password = ''
}

const submit = async () => {
  const username = form.value.username.trim()
  const password = form.value.password
  if (!username || !password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    if (isRegister.value) {
      await register(username, password)
      ElMessage.success('注册成功，已自动登录')
    }
    const data = await login(username, password)
    emit('logged-in', data.user)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败：' + err.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #2b5876, #4e4376);
}

.login-card {
  width: 380px;
  padding: 12px 8px;
  border-radius: 10px;
}

.login-title {
  margin: 0 0 4px;
  font-size: 22px;
  text-align: center;
}

.login-sub {
  margin: 0 0 20px;
  color: #909399;
  text-align: center;
  font-size: 13px;
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
}

.switch-line {
  margin-top: 14px;
  text-align: center;
}
</style>
