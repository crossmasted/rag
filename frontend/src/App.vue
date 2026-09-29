<template>
  <div class="app-container">
    <Login v-if="!currentUser" @logged-in="onLoggedIn" />
    <template v-else>
      <div class="top-bar">
        <span class="user-info">
          当前用户：{{ currentUser.username }}
          <el-tag size="small" type="info">{{ accessLevelText }}</el-tag>
        </span>
        <el-button size="small" @click="handleLogout">退出登录</el-button>
      </div>
      <div class="chat-wrap">
        <ChatWindow />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import ChatWindow from './components/ChatWindow.vue'
import Login from './views/Login.vue'
import { getCurrentUser, logout } from './api'

const currentUser = ref(getCurrentUser())

const accessLevelText = computed(() => {
  const map = { public: '公开级别', admin: '管理员', private: '私有级别' }
  return map[currentUser.value?.access_level] || currentUser.value?.access_level || ''
})

const onLoggedIn = (user) => {
  currentUser.value = user
  ElMessage.success(`欢迎，${user.username}`)
}

const handleLogout = () => {
  logout()
  currentUser.value = null
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.top-bar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 10px 24px;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
}

.user-info {
  font-size: 14px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-wrap {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  overflow: hidden;
}
</style>
