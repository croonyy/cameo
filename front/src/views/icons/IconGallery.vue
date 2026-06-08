<template>
  <n-card
    :segmented="{ content: true }"
    content-style="padding: 0;"
    :bordered="false"
    size="small"
    :title="config.title"
  >
    <template #header-extra>
      <n-input
        v-model:value="searchText"
        clearable
        size="small"
        class="icon-search"
        placeholder="搜索图标"
      />
    </template>

    <div class="icon-meta">
      <span>{{ filteredEntries.length }} icons</span>
      <span v-if="searchText">matching "{{ searchText }}"</span>
    </div>

    <n-spin :show="loading">
      <n-empty v-if="!loading && visibleEntries.length === 0" description="暂无图标" />

      <div v-else class="icon-gallery">
        <n-card
          v-for="[iconName, IconComponent] in visibleEntries"
          :key="iconName"
          size="small"
          class="cursor-pointer icon-gallery-item"
          hoverable
        >
          <div class="icon-item">
            <n-icon size="60" :color="config.color">
              <component :is="IconComponent" />
            </n-icon>
            <div class="icon-name-row">
              <span class="icon-name">{{ iconName }}</span>
              <n-button
                text
                size="tiny"
                class="copy-button"
                title="复制图标名"
                @click.stop="copyIconName(iconName)"
              >
                <template #icon>
                  <n-icon size="14">
                    <CopyOutlined />
                  </n-icon>
                </template>
              </n-button>
            </div>
          </div>
        </n-card>
      </div>

      <div
        v-if="!loading && visibleCount < filteredEntries.length"
        ref="loadMoreRef"
        class="load-more"
      >
        加载更多...
      </div>
    </n-spin>
  </n-card>
</template>

<script lang="ts" setup>
  import { computed, nextTick, onBeforeUnmount, ref, shallowRef, watch } from 'vue';
  import { useMessage } from 'naive-ui';
  import { CopyOutlined } from '@vicons/antd';

  type IconLibrary = 'antd' | 'ionicons5';
  type IconComponent = unknown;
  type IconEntry = [string, IconComponent];
  type IconMap = Record<string, IconComponent>;

  const BATCH_SIZE = 80;

  const props = defineProps<{
    library: IconLibrary;
  }>();

  const libraryConfigs: Record<
    IconLibrary,
    {
      title: string;
      color: string;
      copyPrefix: string;
      loader: () => Promise<IconMap>;
    }
  > = {
    antd: {
      title: 'icons of @vicons/antd',
      color: '#24bf2b',
      copyPrefix: 'antd',
      loader: () => import('@vicons/antd') as Promise<IconMap>,
    },
    ionicons5: {
      title: 'icons of @vicons/ionicons5',
      color: '#61affe',
      copyPrefix: 'ionicons5',
      loader: () => import('@vicons/ionicons5') as Promise<IconMap>,
    },
  };

  const message = useMessage();
  const icons = shallowRef<IconMap>({});
  const loading = ref(false);
  const searchText = ref('');
  const visibleCount = ref(BATCH_SIZE);
  const loadMoreRef = ref<HTMLElement | null>(null);
  let observer: IntersectionObserver | null = null;

  const config = computed(() => libraryConfigs[props.library] || libraryConfigs.antd);

  const filteredEntries = computed<IconEntry[]>(() => {
    const keyword = searchText.value.trim().toLowerCase();
    const entries = Object.entries(icons.value) as IconEntry[];
    if (!keyword) return entries;
    return entries.filter(([iconName]) => iconName.toLowerCase().includes(keyword));
  });

  const visibleEntries = computed(() => filteredEntries.value.slice(0, visibleCount.value));

  watch(
    () => props.library,
    async () => {
      await loadIcons();
    },
    { immediate: true }
  );

  watch(searchText, () => {
    visibleCount.value = BATCH_SIZE;
    setupObserver();
  });

  async function loadIcons() {
    loading.value = true;
    searchText.value = '';
    visibleCount.value = BATCH_SIZE;
    icons.value = {};
    try {
      icons.value = await config.value.loader();
    } finally {
      loading.value = false;
      setupObserver();
    }
  }

  function loadMore() {
    if (visibleCount.value >= filteredEntries.value.length) return;
    visibleCount.value += BATCH_SIZE;
    setupObserver();
  }

  async function setupObserver() {
    observer?.disconnect();
    observer = null;

    await nextTick();
    if (!loadMoreRef.value || visibleCount.value >= filteredEntries.value.length) return;

    observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        loadMore();
      }
    });
    observer.observe(loadMoreRef.value);
  }

  async function copyIconName(iconName: string) {
    const fullIconName = `${config.value.copyPrefix}:${iconName}`;
    try {
      await navigator.clipboard.writeText(fullIconName);
      message.success(`已复制 ${fullIconName}`);
    } catch {
      message.error('复制失败');
    }
  }

  onBeforeUnmount(() => {
    observer?.disconnect();
  });
</script>

<style lang="less" scoped>
  .icon-search {
    width: 260px;
  }

  .icon-meta {
    display: flex;
    gap: 8px;
    padding: 8px 12px;
    color: #6b7280;
    font-size: 12px;
  }

  .icon-gallery {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 4px;

    &-item {
      width: 150px;
    }
  }

  .icon-item {
    display: flex;
    min-height: 112px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #6b7280;
    text-align: center;
  }

  .icon-name-row {
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: center;
    gap: 4px;
  }

  .icon-name {
    min-width: 0;
    overflow-wrap: anywhere;
    line-height: 20px;
  }

  .copy-button {
    flex: 0 0 auto;
  }

  .load-more {
    height: 40px;
    color: #9ca3af;
    line-height: 40px;
    text-align: center;
  }
</style>
