<template>
  <n-tooltip trigger="hover">
    <template #trigger>
      <div class="cursor-pointer table-toolbar-right-icon" style="position: relative">
        <n-popover
          trigger="click"
          :width="230"
          class="toolbar-popover"
          placement="bottom-end"
          :show-arrow="false"
          raw
          @update:show="onPopoverShow"
          :style="{ background: themeVars.baseColor }"
        >
          <template #trigger>
            <div class="popover-trigger-wrapper">
              <n-icon size="18">
                <SettingOutlined />
              </n-icon>
            </div>
          </template>
          <template #header>
            <div class="table-toolbar-inner-popover-title">
              <n-space>
                <n-checkbox v-model:checked="checkAll" @update:checked="onCheckAll"
                  >{{ t('table.columnDisplay') }}</n-checkbox
                >
                <n-button text type="info" size="small" class="mt-1" @click="resetColumns"
                  >{{ t('table.resetColumns') }}</n-button
                >
              </n-space>
            </div>
          </template>
          <div class="table-toolbar-inner" :class="{ dragging: isDragging }">
            <n-checkbox-group v-model:value="checkList" @update:value="onChange">
              <Draggable
                v-model="columnsList"
                animation="300"
                item-key="key"
                filter=".no-draggable"
                :move="onMove"
                @start="onDragStart"
                @end="draggableEnd"
                ghost-class="sortable-ghost"
                chosen-class="sortable-chosen"
                drag-class="sortable-drag"
              >
                <template #item="{ element }">
                  <div
                    class="table-toolbar-inner-checkbox"
                    :class="{
                      'table-toolbar-inner-checkbox-dark': getDarkTheme === true,
                      'no-draggable': element.draggable === false,
                    }"
                  >
                    <span
                      class="drag-icon"
                      :class="{ 'drag-icon-hidden': element.draggable === false }"
                    >
                      <n-icon size="18">
                        <DragOutlined />
                      </n-icon>
                    </span>
                    <n-checkbox :value="element.key">
                      {{ getColumnLabel(element) }}
                    </n-checkbox>
                    <div class="fixed-item">
                      <n-tooltip trigger="hover" placement="bottom">
                        <template #trigger>
                          <n-icon
                            size="18"
                            :color="element.fixed === 'left' ? '#2080f0' : undefined"
                            class="cursor-pointer"
                            @click="fixedColumn(element, 'left')"
                          >
                            <VerticalRightOutlined />
                          </n-icon>
                        </template>
                        <span>{{ t('table.fixLeft') }}</span>
                      </n-tooltip>
                      <n-divider vertical />
                      <n-tooltip trigger="hover" placement="bottom">
                        <template #trigger>
                          <n-icon
                            size="18"
                            :color="element.fixed === 'right' ? '#2080f0' : undefined"
                            class="cursor-pointer"
                            @click="fixedColumn(element, 'right')"
                          >
                            <VerticalLeftOutlined />
                          </n-icon>
                        </template>
                        <span>{{ t('table.fixRight') }}</span>
                      </n-tooltip>
                    </div>
                  </div>
                </template>
              </Draggable>
            </n-checkbox-group>
          </div>
        </n-popover>
      </div>
    </template>
    <span>{{ t('table.columnSettings') }}</span>
  </n-tooltip>
</template>

<script setup lang="ts">
  import { ref, unref, onMounted, nextTick, computed } from 'vue';
  import { useTableContext } from '../../hooks/useTableContext';
  import { cloneDeep } from 'lodash-es';
  import {
    SettingOutlined,
    DragOutlined,
    VerticalRightOutlined,
    VerticalLeftOutlined,
  } from '@vicons/antd';
  import Draggable from 'vuedraggable';
  import { useDesignSetting } from '@/hooks/setting/useDesignSetting';
  import { t } from '@/i18n';

  import { useThemeVars } from 'naive-ui';
  const themeVars = useThemeVars();
  // 👇 必须拆成顶层 computed，这是关键！
  // const baseColor = computed(() => themeVars.value.baseColor);
  const getBaseColor = computed(() => {
    return themeVars.value.textColor1;
  });
  interface FilterOptions {
    title: string;
    key: string;
    fixed?: boolean | 'left' | 'right';
    draggable?: boolean;
    type?: string;
    titleText?: string;
  }

  const { getDarkTheme } = useDesignSetting();
  const table: any = useTableContext();

  const columnsList = ref<FilterOptions[]>([]);
  const isDragging = ref(false);

  const checkAll = ref(true);
  const checkList = ref<string[]>([]);

  // 过滤不需要拖拽的列
  const isDraggableColumn = (item: any) =>
    item.key !== 'action' && item.titleText !== t('table.action') && item.type !== 'selection';

  function getColumnLabel(element: FilterOptions) {
    if (element.titleText) return element.titleText;
    if (element.title && typeof element.title === 'string') return element.title;
    return element.key;
  }

  // 初始化
  onMounted(() => {
    nextTick(() => {
      if (table.getColumns().length) init();
    });
  });

  // 弹窗打开时初始化
  function onPopoverShow(show: boolean) {
    if (show && !columnsList.value.length) {
      const tryInitWithRetry = (attempt = 0) => {
        const columns = table.getColumns();
        if (columns.length) {
          init();
        } else if (attempt < 5) {
          setTimeout(() => tryInitWithRetry(attempt + 1), 50 * (attempt + 1));
        }
      };
      nextTick(() => tryInitWithRetry());
    }
  }

  // 初始化方法
  function init() {
    const columns: any[] = getColumns();
    checkList.value = columns.filter((item) => item.key !== 'selection').map((item) => item.key);
    const newColumns = columns.filter(isDraggableColumn);
    columnsList.value = cloneDeep(newColumns);
  }

  // 切换选中
  function onChange(val: string[]) {
    const originalOrder = unref(columnsList).map((col) => col.key);
    const sortedKeys = originalOrder.filter((key) => val.includes(key));
    val.forEach((key) => {
      if (!sortedKeys.includes(key)) sortedKeys.push(key);
    });
    checkList.value = sortedKeys;
    setColumns(sortedKeys);
  }

  // 设置列
  function setColumns(cols: any[]) {
    table.setColumns(cols);
  }

  // 获取列
  function getColumns() {
    const newRet: any[] = [];
    table.getColumns().forEach((item) => {
      newRet.push({ ...item });
    });
    return newRet;
  }

  // 重置
  function resetColumns() {
    const originalKeys: any[] = table.getOriginalColumns
      ? table.getOriginalColumns(true)
      : table.getCacheColumns(true);
    const originalObjs: any[] = table.getOriginalColumns
      ? table.getOriginalColumns()
      : table.getCacheColumns();
    const resetColumns = originalObjs.map((item) => ({
      ...item,
      fixed: undefined,
      __fixedWidthAdjusted: undefined,
    }));

    checkAll.value = true;
    checkList.value = originalKeys.filter((key) => key !== 'selection');

    resetColumns.forEach((item) => {
      if (item.key) {
        table.setCacheColumnsField(item.key, {
          fixed: undefined,
          __fixedWidthAdjusted: undefined,
        });
      }
    });

    setColumns(resetColumns.filter((item) => checkList.value.includes(item.key)));
    columnsList.value = cloneDeep(resetColumns.filter(isDraggableColumn));
  }

  // 全选
  function onCheckAll(checked: boolean) {
    if (checked) {
      const allKeys = unref(columnsList).map((col) => col.key);
      checkList.value = allKeys;
      setColumns(allKeys);
    } else {
      setColumns([]);
      checkList.value = [];
    }
  }

  // 拖拽结束
  function draggableEnd() {
    const toolbarInner = document.querySelector('.table-toolbar-inner');
    if (toolbarInner) toolbarInner.classList.add('just-dropped');

    setTimeout(() => {
      isDragging.value = false;
      setTimeout(() => {
        if (toolbarInner) toolbarInner.classList.remove('just-dropped');
      }, 50);
    }, 100);

    const columnKeys = unref(columnsList).map((col) => col.key);
    setColumns(columnKeys);
  }

  // 拖拽判断
  function onMove(e: any) {
    if (e.draggedContext.element.draggable === false) return false;
    return true;
  }

  // 拖拽开始
  function onDragStart() {
    isDragging.value = true;
  }

  // 固定列
  function fixedColumn(item: FilterOptions, fixed: 'left' | 'right' | undefined) {
    if (!checkList.value.includes(item.key)) return;

    const columns = getColumns();
    const isFixed = item.fixed === fixed ? undefined : fixed;
    const index = columns.findIndex((res) => res.key === item.key);

    if (index !== -1) {
      columns[index].fixed = isFixed;
    }

    table.setCacheColumnsField(item.key, { fixed: isFixed });

    const listIndex = columnsList.value.findIndex((res) => res.key === item.key);
    if (listIndex !== -1) {
      columnsList.value[listIndex].fixed = isFixed;
    }

    setColumns(columns);
  }
</script>

<style lang="less">
  .table-toolbar {
    &-inner-popover-title {
      padding: 3px 0;
    }

    &-right {
      &-icon {
        margin-left: 12px;
        font-size: 16px;
        color: var(--text-color);
        cursor: pointer;

        :hover {
          color: #1890ff;
        }
      }
    }
  }

  .table-toolbar-inner {
    &.dragging {
      .table-toolbar-inner-checkbox {
        &:hover {
          background: transparent !important;
        }
      }
    }

    &-checkbox {
      display: flex;
      align-items: center;
      padding: 10px 14px;
      transition: all 0.2s ease;

      &:hover {
        background: rgba(100, 200, 255, 0.1);
      }

      .drag-icon {
        display: inline-flex;
        margin-right: 8px;
        cursor: move;
        &-hidden {
          visibility: hidden;
          cursor: default;
        }
      }

      .fixed-item {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        margin-left: auto;
      }

      .ant-checkbox-wrapper {
        flex: 1;

        &:hover {
          color: #1890ff !important;
        }
      }
    }

    &-checkbox-dark {
      &:hover {
        background: hsla(0, 0%, 100%, 0.08);
      }
    }
  }

  .table-toolbar-inner.just-dropped {
    .table-toolbar-inner-checkbox {
      pointer-events: none !important;
    }
  }

  .sortable-ghost {
    opacity: 0.4 !important;
    background: rgba(100, 200, 255, 0.15) !important;
    border: 1px dashed rgba(100, 200, 255, 0.5) !important;
    pointer-events: none !important;

    &:hover {
      background: rgba(100, 200, 255, 0.15) !important;
    }
  }

  .sortable-chosen {
    background: rgba(100, 200, 255, 0.08) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;

    &:hover {
      background: rgba(100, 200, 255, 0.08) !important;
    }
  }

  .sortable-drag {
    opacity: 0.9 !important;
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
    border-radius: 6px !important;
  }

  .toolbar-popover {
    .n-popover__content {
      padding: 0;
    }
  }

  .popover-trigger-wrapper {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }
</style>

<style lang="less" scoped>
  /* 只作用于当前组件的 popover，不影响全局！ */
  :global(.toolbar-popover .n-popover__content) {
    // background: v-bind(getBaseColor);
    // border-radius: var(--glass-radius-md) !important;
    max-height: 60vh !important;
    overflow-y: auto !important;
  }
  :global(.toolbar-popover.n-popover) {
    // background: v-bind(getBaseColor);
    // border-radius: var(--glass-radius-md) !important;
    // box-shadow: var(--glass-shadow-hover) !important;
    // padding: 12px !important;
    // max-width: 500px !important;
    width: auto !important;
    // min-width: 230px !important;
    // max-height: 60vh !important;
    // overflow-y: auto !important;
  }
</style>
