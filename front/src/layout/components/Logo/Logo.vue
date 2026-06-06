<template>
  <div class="logo" :class="{ 'logo-collapsed': collapsed }">
    <img :src="websiteConfig.logo" alt="" />
    <h2 class="title">{{ websiteConfig.title }}</h2>
  </div>
</template>

<script lang="ts">
  import { websiteConfig } from '@/config/website.config';
  export default {
    name: 'Index',
    props: {
      collapsed: {
        type: Boolean,
      },
    },
    data() {
      return {
        websiteConfig,
      };
    },
  };
</script>

<style lang="less" scoped>
  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 64px;
    line-height: 64px;
    overflow: hidden;
    white-space: nowrap;

    img {
      flex: 0 0 auto;
      width: auto;
      height: 32px;
    }

    .title {
      max-width: 140px;
      margin: 0;
      margin-left: 8px;
      overflow: hidden;
      opacity: 1;
      transform: translateX(0);
      transition: max-width 0.22s ease, margin-left 0.22s ease, opacity 0.16s ease,
        transform 0.18s ease;
      will-change: max-width, opacity, transform;
    }

    &.logo-collapsed {
      .title {
        max-width: 0;
        margin-left: 0;
        opacity: 0;
        transform: translateX(-6px);
        pointer-events: none;
      }
    }
  }
</style>
