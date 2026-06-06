<template>
  <div v-if="content" class="field-description" v-html="html"></div>
</template>

<script setup lang="ts">
  import { computed } from 'vue';

  const props = defineProps<{
    content?: string;
  }>();

  function escapeHtml(value: string) {
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function sanitizeUrl(value: string) {
    const trimmed = value.trim();
    return /^(https?:|mailto:)/i.test(trimmed) ? trimmed : '';
  }

  function renderInline(value: string) {
    return escapeHtml(value)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label, url) => {
        const safeUrl = sanitizeUrl(url);
        return safeUrl
          ? `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${label}</a>`
          : label;
      });
  }

  function renderMarkdown(value: string) {
    const lines = value.replace(/\r\n/g, '\n').split('\n');
    const blocks: string[] = [];
    let listItems: string[] = [];

    function flushList() {
      if (listItems.length) {
        blocks.push(`<ul>${listItems.join('')}</ul>`);
        listItems = [];
      }
    }

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        flushList();
        return;
      }

      const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
      if (heading) {
        flushList();
        const level = heading[1].length;
        blocks.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
        return;
      }

      const listItem = trimmed.match(/^[-*]\s+(.+)$/);
      if (listItem) {
        listItems.push(`<li>${renderInline(listItem[1])}</li>`);
        return;
      }

      flushList();
      blocks.push(`<p>${renderInline(trimmed)}</p>`);
    });

    flushList();
    return blocks.join('');
  }

  const html = computed(() => renderMarkdown(props.content || ''));
</script>

<style scoped>
  .field-description {
    margin-top: 4px;
    color: #999;
    font-size: 12px;
    line-height: 1.6;
  }

  .field-description :deep(p) {
    margin: 0;
  }

  .field-description :deep(p + p),
  .field-description :deep(ul),
  .field-description :deep(h1),
  .field-description :deep(h2),
  .field-description :deep(h3),
  .field-description :deep(h4),
  .field-description :deep(h5),
  .field-description :deep(h6) {
    margin: 4px 0 0;
  }

  .field-description :deep(ul) {
    padding-left: 18px;
  }

  .field-description :deep(code) {
    padding: 1px 4px;
    border-radius: 3px;
    background-color: rgba(128, 128, 128, 0.14);
  }

  .field-description :deep(a) {
    color: #2080f0;
    text-decoration: none;
  }
</style>
