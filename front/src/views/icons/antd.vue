<template>
  <n-card
    :segmented="{ content: true }"
    content-style="padding: 0;"
    :bordered="false"
    size="small"
    title="icons of @vicons/antd"
  >
    <div class="flex flex-wrap project-card">
      <n-card
        v-for="(IconComponent, iconName) in allicons"
        :key="iconName"
        size="small"
        class="cursor-pointer project-card-item"
        hoverable
      >
        <div class="flex flex-col justify-center text-gray-500">
          <span class="text-center">
            <!-- <n-icon size="60" color="#68c755"> -->
            <n-icon size="60" color="#24bf2b">
              <component :is="IconComponent" />
            </n-icon>
          </span>
          <span class="text-center">{{ iconName }}</span>
        </div>
      </n-card>
    </div>
  </n-card>
</template>
<script lang="ts" setup>
  import * as allicons from '@vicons/antd';
</script>
<style lang="less" scoped>
  .project-card {
    margin-right: -6px;

    &-item {
      margin: -1px;
      // width: (100 / 7) * 1%;
      width: 150px;
    }
  }
</style>
