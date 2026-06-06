<template>
  <div class="json-editor-wrapper" :style="{ width: width, height: height }">
    <codemirror
      v-model="localValue"
      :style="{ height: '100%', width: '100%' }"
      :extensions="extensions"
      :tab-size="2"
      @change="handleChange"
    />
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import { Codemirror } from 'vue-codemirror';
  import { json, jsonParseLinter } from '@codemirror/lang-json';
  import { oneDark } from '@codemirror/theme-one-dark';
  import { linter } from '@codemirror/lint';

  const props = defineProps({
    value: { type: [String, Object, Array, null], default: null },
    width: { type: String, default: '600px' },
    height: { type: String, default: '400px' },
  });

  const emit = defineEmits(['update:value']);

  // Convert any value to formatted JSON string for the editor
  function toString(val: any): string {
    if (val == null) return '';
    if (typeof val === 'string') {
      // Try to pretty-print existing JSON string
      try {
        return JSON.stringify(JSON.parse(val), null, 2);
      } catch {
        return val;
      }
    }
    return JSON.stringify(val, null, 2);
  }

  const localValue = ref(toString(props.value));

  watch(
    () => props.value,
    (newVal) => {
      localValue.value = toString(newVal);
    }
  );

  const extensions = computed(() => {
    const exts: any[] = [json(), linter(jsonParseLinter()), oneDark];
    return exts;
  });

  function handleChange(val: string) {
    try {
      const parsed = val.trim() === '' ? null : JSON.parse(val);
      emit('update:value', parsed);
    } catch {
      // Not valid JSON yet — emit as string, let form validation handle it
      emit('update:value', val);
    }
  }
</script>

<style scoped>
  .json-editor-wrapper {
    border: 1px solid #444;
    border-radius: 4px;
    overflow: hidden;
    /* Allow manual resize from bottom-right corner */
    resize: both;
    min-width: 300px;
    min-height: 200px;
  }
  .json-editor-wrapper :deep(.cm-editor) {
    font-size: 13px;
    font-family: Consolas, 'Courier New', monospace;
    height: 100% !important;
  }
  .json-editor-wrapper :deep(.cm-scroller) {
    font-family: Consolas, 'Courier New', monospace;
    overflow: auto;
  }
</style>
