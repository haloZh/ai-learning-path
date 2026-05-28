<template>
  <div class="explain-card">
    <div class="explain-header" @click="expanded = !expanded">
      <el-icon color="#409eff"><InfoFilled /></el-icon>
      <span class="explain-label">推荐理由</span>
      <el-icon class="arrow" :class="{ rotated: expanded }"><ArrowRight /></el-icon>
    </div>
    <transition name="slide">
      <div v-if="expanded" class="explain-body">
        <div v-for="(reason, i) in reasons" :key="i" class="reason-item">
          ✅ {{ reason }}
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { InfoFilled, ArrowRight } from '@element-plus/icons-vue'

defineProps<{
  reasons: string[]
}>()

const expanded = ref(false)
</script>

<style scoped>
.explain-card {
  background: #ecf5ff;
  border-radius: 8px;
  border: 1px solid #d9ecff;
  overflow: hidden;
  margin-top: 8px;
}
.explain-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
}
.explain-label {
  font-size: 13px;
  color: #409eff;
  font-weight: 500;
  flex: 1;
}
.arrow {
  transition: transform 0.3s;
  color: #409eff;
}
.arrow.rotated {
  transform: rotate(90deg);
}
.explain-body {
  padding: 0 12px 12px;
}
.reason-item {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}
</style>
