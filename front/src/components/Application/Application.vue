<template>
  <n-dialog-provider>
    <n-notification-provider>
      <n-message-provider keep-alive-on-hover>
        <slot name="default"></slot>
      </n-message-provider>
    </n-notification-provider>
  </n-dialog-provider>
</template>

<script lang="ts">
  import { defineComponent } from 'vue';

  export default defineComponent({
    name: 'Application',
    setup() {
      return {};
    },
  });
</script>
