<template>
  <div class="table-toolbar">
    <!--顶部左侧区域-->
    <div class="flex items-center table-toolbar-left">
      <template v-if="props.title">
        <div class="table-toolbar-left-title">
          {{ props.title }}
          <n-tooltip trigger="hover" v-if="props.titleTooltip">
            <template #trigger>
              <n-icon size="18" class="ml-1 text-gray-400 cursor-pointer">
                <QuestionCircleOutlined />
              </n-icon>
            </template>
            {{ props.titleTooltip }}
          </n-tooltip>
        </div>
      </template>
      <slot name="tableTitle"></slot>
    </div>

    <div class="flex items-center leading-none table-toolbar-right">
      <!--顶部右侧区域-->
      <slot name="toolbar"></slot>

      <n-button
        v-if="props.showExcelExport"
        class="table-toolbar-left-export"
        size="small"
        :loading="exporting"
        @click="downloadExcel"
      >
        <template #icon>
          <n-icon>
            <DownloadOutlined />
          </n-icon>
        </template>
        {{ t('button.downloadExcel') }}
      </n-button>

      <!--斑马纹-->
      <n-tooltip trigger="hover">
        <template #trigger>
          <div class="mr-2 table-toolbar-right-icon">
            <n-switch v-model:value="isStriped" @update:value="setStriped" />
          </div>
        </template>
        <span>{{ t('table.striped') }}</span>
      </n-tooltip>
      <n-divider vertical />

      <!--刷新-->
      <n-tooltip trigger="hover">
        <template #trigger>
          <div class="table-toolbar-right-icon" @click="reload">
            <n-icon size="18">
              <ReloadOutlined />
            </n-icon>
          </div>
        </template>
        <span>{{ t('button.refresh') }}</span>
      </n-tooltip>

      <!--密度-->
      <n-tooltip trigger="hover">
        <template #trigger>
          <div class="table-toolbar-right-icon">
            <n-dropdown
              @select="densitySelect"
              trigger="click"
              :options="densityOptions"
              v-model:value="tableSize"
            >
              <n-icon size="18">
                <ColumnHeightOutlined />
              </n-icon>
            </n-dropdown>
          </div>
        </template>
        <span>{{ t('table.density') }}</span>
      </n-tooltip>

      <!--表格设置单独抽离成组件-->
      <ColumnSetting />
    </div>
  </div>
  <div
    class="s-table"
    :class="{
      's-table--fit-content': shouldFitContentTable,
      's-table--short-data': shouldUseShortDataLayout,
    }"
    @mousedown.capture="handleTableMouseDown"
    @click.capture="handleTableClickCapture"
  >
    <n-data-table
      ref="tableElRef"
      v-bind="getBindValues"
      :striped="isStriped"
      :pagination="pagination"
      @update:page="updatePage"
      @update:page-size="updatePageSize"
      @update:sorter="(sorter) => emit('update:sorter', sorter)"
      @update:checked-row-keys="(...args) => emit('update:checked-row-keys', ...args)"
    >
      <template #[item]="data" v-for="item in Object.keys($slots)" :key="item">
        <slot :name="item" v-bind="data"></slot>
      </template>
    </n-data-table>
  </div>
</template>

<script lang="ts" setup>
  import {
    ref,
    unref,
    toRaw,
    computed,
    onMounted,
    onActivated,
    onDeactivated,
    onBeforeUnmount,
    nextTick,
    watch,
  } from 'vue';
  import {
    ReloadOutlined,
    ColumnHeightOutlined,
    QuestionCircleOutlined,
    DownloadOutlined,
  } from '@vicons/antd';
  import { createTableContext } from './hooks/useTableContext';

  import ColumnSetting from './components/settings/ColumnSetting.vue';

  import { useLoading } from './hooks/useLoading';
  import { useColumns } from './hooks/useColumns';
  import { useDataSource } from './hooks/useDataSource';
  import { usePagination } from './hooks/usePagination';

  import { basicProps } from './props';
  import { APISETTING } from './const';

  import { BasicTableProps } from './types/table';

  import { getViewportOffset } from '@/utils/domUtils';
  import { useWindowSizeFn } from '@/hooks/event/useWindowSizeFn';
  import { isBoolean, isFunction } from '@/utils/is';
  import { t } from '@/i18n';

  const densityOptions = [
    {
      type: 'menu',
      label: t('table.densityCompact'),
      key: 'small',
    },
    {
      type: 'menu',
      label: t('table.densityDefault'),
      key: 'medium',
    },
    {
      type: 'menu',
      label: t('table.densityLoose'),
      key: 'large',
    },
  ];

  const emit = defineEmits([
    'fetch-success',
    'fetch-error',
    'update:checked-row-keys',
    'edit-end',
    'edit-cancel',
    'edit-row-end',
    'edit-change',
    'update:sorter',
  ]);

  const props = defineProps({ ...basicProps });
  const deviceHeight = ref(150);
  const tableElRef = ref<ComponentRef>(null);
  const wrapRef = ref<Nullable<HTMLDivElement>>(null);
  let paginationEl: HTMLElement | null;
  const isStriped = ref(props.striped || false);
  const exporting = ref(false);
  const tableData = ref<Recordable[]>([]);
  const innerPropsRef = ref<Partial<BasicTableProps>>();
  const tableScrollPosition = ref({ top: 0, left: 0 });
  const resizedColumnWidthMap = ref<Record<string, number>>({});
  const shortDataBodyHeight = ref(0);
  let removeTableScrollListeners: (() => void) | null = null;
  const MAX_DATA_COLUMN_WIDTH = 300;
  const MAX_LONG_TEXT_COLUMN_WIDTH = 240;
  const SHORT_DATA_ROW_LIMIT = 10;
  const MEASURABLE_ROW_LIMIT = 100;
  const FALLBACK_ROW_HEIGHT_BY_SIZE = {
    small: 42,
    medium: 54,
    large: 64,
  };
  const RESIZE_DRAG_THRESHOLD = 2;
  const RESIZE_CLICK_SUPPRESS_MS = 180;
  let resizeDragStartX = 0;
  let resizeDragMoved = false;
  let resizeClickSuppressTimer: number | null = null;
  let layoutSyncTimer: number | null = null;
  const layoutSyncRafIds: number[] = [];

  const getProps = computed(() => {
    return { ...props, ...unref(innerPropsRef) } as BasicTableProps;
  });

  const tableSize = ref(unref(getProps as any).size || 'medium');

  const { getLoading, setLoading } = useLoading(getProps);

  const { getPaginationInfo, setPagination, getPagination } = usePagination(getProps);

  const { getDataSourceRef, getDataSource, getRowKey, reload } = useDataSource(
    getProps,
    {
      getPaginationInfo,
      setPagination,
      tableData,
      setLoading,
    },
    emit
  );

  const {
    getPageColumns,
    setColumns,
    getColumns,
    getCacheColumns,
    getOriginalColumns,
    setCacheColumnsField,
    getColumnsScrollX,
  } = useColumns(getProps);

  //页码切换
  function updatePage(page) {
    setPagination({ page: page });
    reload();
  }

  //分页数量切换
  function updatePageSize(size) {
    setPagination({ page: 1, pageSize: size });
    reload();
  }

  //密度切换
  function densitySelect(e) {
    tableSize.value = e;
  }

  //获取表格大小
  const getTableSize = computed(() => tableSize.value);

  function getFallbackRowHeight() {
    return (
      FALLBACK_ROW_HEIGHT_BY_SIZE[
        unref(getTableSize) as keyof typeof FALLBACK_ROW_HEIGHT_BY_SIZE
      ] || FALLBACK_ROW_HEIGHT_BY_SIZE.medium
    );
  }

  function getViewportBodyHeight() {
    return Math.max(150, unref(deviceHeight));
  }

  function getCurrentPageBodyHeight(rowCount: number) {
    if (rowCount <= 0) return 0;
    const measuredHeight = unref(shortDataBodyHeight);
    const estimatedHeight = rowCount * getFallbackRowHeight();
    return Math.max(measuredHeight || estimatedHeight, estimatedHeight);
  }

  function shouldConstrainBodyHeight(rowCount: number) {
    if (rowCount <= 0) return false;
    return getCurrentPageBodyHeight(rowCount) > getViewportBodyHeight();
  }

  function getBodyMaxHeight(rowCount: number) {
    const viewportBodyHeight = Math.max(150, unref(deviceHeight));
    if (rowCount <= 0 || shouldConstrainBodyHeight(rowCount)) {
      return viewportBodyHeight;
    }
    return getCurrentPageBodyHeight(rowCount);
  }

  function measureShortDataBodyHeight(tableEl: HTMLElement, rowCount: number) {
    if (rowCount <= 0 || rowCount > MEASURABLE_ROW_LIMIT) {
      shortDataBodyHeight.value = 0;
      return;
    }
    const rows = Array.from(
      tableEl.querySelectorAll<HTMLElement>(
        '.n-data-table-base-table-body .n-data-table-tbody .n-data-table-tr'
      )
    ).filter((row) => row.offsetParent !== null);
    if (!rows.length) return;
    const visibleRows = rows.slice(0, rowCount);
    const measuredHeight = visibleRows.reduce((height, row) => height + row.offsetHeight, 0);
    if (measuredHeight > 0) {
      shortDataBodyHeight.value = measuredHeight;
    }
  }

  function isResizeHandle(target: EventTarget | null) {
    return target instanceof HTMLElement && !!target.closest('.n-data-table-resize-button');
  }

  function clearResizeDragListeners() {
    window.removeEventListener('mousemove', handleResizeDragMouseMove, true);
    window.removeEventListener('mouseup', handleResizeDragMouseUp, true);
  }

  function suppressNextResizeClick() {
    if (resizeClickSuppressTimer) {
      window.clearTimeout(resizeClickSuppressTimer);
    }
    resizeClickSuppressTimer = window.setTimeout(() => {
      resizeClickSuppressTimer = null;
    }, RESIZE_CLICK_SUPPRESS_MS);
  }

  function handleResizeDragMouseMove(event: MouseEvent) {
    if (Math.abs(event.clientX - resizeDragStartX) > RESIZE_DRAG_THRESHOLD) {
      resizeDragMoved = true;
    }
  }

  function handleResizeDragMouseUp() {
    clearResizeDragListeners();
    if (resizeDragMoved) {
      suppressNextResizeClick();
    }
    resizeDragMoved = false;
  }

  function handleTableMouseDown(event: MouseEvent) {
    if (!isResizeHandle(event.target)) return;
    resizeDragStartX = event.clientX;
    resizeDragMoved = false;
    clearResizeDragListeners();
    window.addEventListener('mousemove', handleResizeDragMouseMove, true);
    window.addEventListener('mouseup', handleResizeDragMouseUp, true);
  }

  function handleTableClickCapture(event: MouseEvent) {
    if (!resizeClickSuppressTimer) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
  }

  function getCellTextWidth(text: string) {
    return Array.from(text).reduce((width, char) => {
      return width + (/[\u4e00-\u9fa5]/.test(char) ? 16 : 9);
    }, 0);
  }

  function getCellValueText(value: any) {
    if (value === null || typeof value === 'undefined') return '';
    return typeof value === 'object' ? JSON.stringify(value) : String(value);
  }

  function isLongStructuredText(text: string) {
    const trimmedText = text.trim();
    return (
      trimmedText.length > 60 ||
      trimmedText.startsWith('{') ||
      trimmedText.startsWith('[') ||
      trimmedText.includes('":')
    );
  }

  function getColumnContentWidthLimit(column: any, rows: Recordable[]) {
    const hasLongStructuredText = rows
      .slice(0, 20)
      .some((row) => isLongStructuredText(getCellValueText(row?.[column.key])));
    return hasLongStructuredText ? MAX_LONG_TEXT_COLUMN_WIDTH : MAX_DATA_COLUMN_WIDTH;
  }

  function withContentColumnWidths(columns: any[], rows: Recordable[]) {
    if (!rows.length) return columns;
    return columns.map((column) => {
      if (!column?.key || column.type === 'selection' || column.key === 'action') {
        return column;
      }
      const contentWidth = Math.max(
        0,
        ...rows.slice(0, 20).map((row) => getCellTextWidth(getCellValueText(row?.[column.key])))
      );
      const widthLimit = getColumnContentWidthLimit(column, rows);
      const nextWidth = Math.min(
        Math.max(Number(column.width || 0), contentWidth + 48),
        widthLimit
      );
      return {
        ...column,
        width: nextWidth,
        minWidth: nextWidth,
      };
    });
  }

  //组装表格信息
  function getColumnKey(column: any) {
    return column?.key == null ? '' : String(column.key);
  }

  function withResizableColumnWidths(columns: any[]) {
    const resizedWidths = resizedColumnWidthMap.value;
    return columns.map((column) => {
      const key = getColumnKey(column);
      const resizedWidth = key ? resizedWidths[key] : undefined;
      if (typeof resizedWidth !== 'number') return column;
      return {
        ...column,
        width: resizedWidth,
        minWidth:
          typeof column.minWidth === 'number'
            ? Math.min(column.minWidth, resizedWidth)
            : column.minWidth,
      };
    });
  }

  function handleColumnResize(
    _resizedWidth: number,
    limitedWidth: number,
    column: any,
    _getColumnWidth: (key: string | number) => number | undefined
  ) {
    const key = getColumnKey(column);
    if (!key) return;
    const nextWidth = Math.max(1, Math.round(limitedWidth));
    resizedColumnWidthMap.value = {
      ...resizedColumnWidthMap.value,
      [key]: nextWidth,
    };
    setCacheColumnsField(key, { width: nextWidth });
    scheduleTableLayoutSync();
  }

  const getBindValues = computed(() => {
    const tableData = unref(getDataSourceRef);
    const shouldUseVirtualScroll =
      Boolean((unref(getProps) as any).virtualScroll) &&
      shouldConstrainBodyHeight(tableData.length);
    const maxHeight =
      (unref(getProps) as any).canResize && shouldUseVirtualScroll
        ? `${getBodyMaxHeight(tableData.length)}px`
        : (unref(getProps) as any).maxHeight;
    const columns = withResizableColumnWidths(
      withContentColumnWidths(toRaw(unref(getPageColumns)), tableData)
    );
    const selectionWidth = props.showRowSelection ? 42 : 0;
    const internalScrollX = getColumnsScrollX(columns) + selectionWidth;
    const propScrollX = Number((unref(getProps) as any).scrollX || 0);
    return {
      ...unref(getProps),
      loading: unref(getLoading),
      columns: props.showRowSelection
        ? [{ type: 'selection', key: 'selection', width: 42, fixed: 'left' }, ...columns]
        : columns,
      rowKey: unref(getRowKey),
      data: tableData,
      size: unref(getTableSize),
      remote: true,
      virtualScroll: shouldUseVirtualScroll,
      scrollX: Math.max(propScrollX, internalScrollX),
      onUnstableColumnResize: handleColumnResize,
      'max-height': maxHeight,
      title: '', // 重置为空 避免绑定到 table 上面
    };
  });

  const shouldFitContentTable = computed(() => {
    return !unref(getBindValues).virtualScroll;
  });

  const shouldUseShortDataLayout = computed(() => {
    const rowCount = unref(getDataSourceRef).length;
    return rowCount > 0 && rowCount <= SHORT_DATA_ROW_LIMIT && !shouldConstrainBodyHeight(rowCount);
  });

  //获取分页信息
  const pagination = computed(() => toRaw(unref(getPaginationInfo)));

  function setProps(props: Partial<BasicTableProps>) {
    innerPropsRef.value = { ...unref(innerPropsRef), ...props };
  }

  function scrollTo(arg0: ScrollToOptions | number, arg1?: number) {
    const table = unref(tableElRef) as any;
    table?.scrollTo?.(arg0 as any, arg1 as any);
  }

  function syncTableScrollbar() {
    const table = unref(tableElRef) as any;
    const { horizontal, vertical } = getTableAxisScrollElements();
    const currentTop = Math.max(0, vertical?.scrollTop || tableScrollPosition.value.top || 0);
    const currentLeft = Math.max(0, horizontal?.scrollLeft || tableScrollPosition.value.left || 0);

    table?.scrollTo?.({
      top: currentTop,
      left: currentLeft,
    });

    if (horizontal) {
      horizontal.scrollLeft = currentLeft;
      horizontal.dispatchEvent(new Event('scroll'));
    }
    if (vertical) {
      vertical.scrollTop = currentTop;
      vertical.dispatchEvent(new Event('scroll'));
    }
  }

  async function syncTableLayout() {
    await computeTableHeight();
    await nextTick();
    syncTableScrollbar();
    await bindTableScrollListeners();
  }

  function scheduleTableLayoutSync() {
    if (layoutSyncTimer) {
      window.clearTimeout(layoutSyncTimer);
      layoutSyncTimer = null;
    }
    layoutSyncRafIds.splice(0).forEach((rafId) => window.cancelAnimationFrame(rafId));

    layoutSyncRafIds.push(
      window.requestAnimationFrame(() => {
        syncTableLayout();
        layoutSyncRafIds.push(window.requestAnimationFrame(syncTableLayout));
      })
    );

    layoutSyncTimer = window.setTimeout(() => {
      layoutSyncTimer = null;
      syncTableLayout();
    }, 120);
  }

  function getTableScrollElements() {
    const table = unref(tableElRef) as any;
    const root = table?.$el as HTMLElement | undefined;
    if (!root) return [];
    return Array.from(
      root.querySelectorAll<HTMLElement>(
        [
          '.n-data-table-base-table',
          '.n-data-table-base-table-body',
          '.n-scrollbar-container',
          '.v-vl',
          '.v-vl-items',
          '.n-data-table-table',
          '.n-data-table-wrapper',
        ].join(',')
      )
    ).filter((el) => el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth);
  }

  function canScrollVertical(el: HTMLElement) {
    return el.scrollHeight > el.clientHeight + 1;
  }

  function canScrollHorizontal(el: HTMLElement) {
    return el.scrollWidth > el.clientWidth + 1;
  }

  function getPreferredScrollableElement(
    root: HTMLElement,
    selectors: string[],
    canScroll: (el: HTMLElement) => boolean
  ) {
    for (const selector of selectors) {
      const matched = Array.from(root.querySelectorAll<HTMLElement>(selector)).find(canScroll);
      if (matched) return matched;
    }
    return null;
  }

  function getTableAxisScrollElements() {
    const table = unref(tableElRef) as any;
    const root = table?.$el as HTMLElement | undefined;
    if (!root) {
      return {
        horizontal: null,
        vertical: null,
        all: [],
      };
    }
    const scrollElements = getTableScrollElements();
    const horizontal =
      getPreferredScrollableElement(
        root,
        [
          '.n-data-table-base-table-body .n-scrollbar-container',
          '.n-data-table-base-table-body .v-vl',
          '.v-vl',
          '.n-data-table-base-table-body',
          '.n-data-table-wrapper',
        ],
        canScrollHorizontal
      ) || scrollElements.find(canScrollHorizontal);
    const vertical =
      getPreferredScrollableElement(
        root,
        [
          '.n-data-table-base-table-body .n-scrollbar-container',
          '.n-data-table-base-table-body .v-vl',
          '.v-vl',
          '.n-data-table-base-table-body',
        ],
        canScrollVertical
      ) || scrollElements.find(canScrollVertical);

    return {
      horizontal: horizontal || null,
      vertical: vertical || null,
      all: scrollElements,
    };
  }

  function saveTableScrollPosition() {
    const { horizontal, vertical } = getTableAxisScrollElements();
    if (!horizontal && !vertical) return;
    tableScrollPosition.value = {
      top: vertical ? Math.max(0, vertical.scrollTop) : tableScrollPosition.value.top,
      left: horizontal ? Math.max(0, horizontal.scrollLeft) : tableScrollPosition.value.left,
    };
  }

  async function bindTableScrollListeners() {
    removeTableScrollListeners?.();
    await nextTick();
    const scrollElements = getTableScrollElements();
    scrollElements.forEach((el) => el.addEventListener('scroll', saveTableScrollPosition, true));
    removeTableScrollListeners = () => {
      scrollElements.forEach((el) =>
        el.removeEventListener('scroll', saveTableScrollPosition, true)
      );
      removeTableScrollListeners = null;
    };
  }

  const setStriped = (value: boolean) => (isStriped.value = value);

  function getColumnTitleText(title: any, fallback: any): string {
    if (typeof title === 'string' || typeof title === 'number') {
      return String(title);
    }
    if (typeof title === 'function') {
      return getColumnTitleText(title(), fallback);
    }
    if (Array.isArray(title)) {
      return title.map((item) => getColumnTitleText(item, '')).join('');
    }
    if (title && typeof title === 'object') {
      return getColumnTitleText(title.children, fallback);
    }
    return fallback != null ? String(fallback) : '';
  }

  function stringifyExcelValue(value: any): string {
    if (value === null || typeof value === 'undefined') {
      return '';
    }
    return typeof value === 'object' ? JSON.stringify(value) : String(value);
  }

  function escapeXml(value: any): string {
    const text = stringifyExcelValue(value);
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function getExportColumns() {
    return toRaw(unref(getPageColumns))
      .filter((column: any) => {
        return column && column.key !== 'action' && column.type !== 'selection' && column.key;
      })
      .map((column: any) => {
        return {
          key: column.key,
          title: getColumnTitleText(column.title, column.key),
        };
      });
  }

  function getColumnName(index: number): string {
    let name = '';
    let current = index + 1;
    while (current > 0) {
      const remainder = (current - 1) % 26;
      name = String.fromCharCode(65 + remainder) + name;
      current = Math.floor((current - 1) / 26);
    }
    return name;
  }

  function getCrc32(data: Uint8Array): number {
    const table = new Uint32Array(256);
    for (let i = 0; i < 256; i++) {
      let value = i;
      for (let j = 0; j < 8; j++) {
        value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
      }
      table[i] = value >>> 0;
    }

    let crc = 0xffffffff;
    for (let i = 0; i < data.length; i++) {
      crc = table[(crc ^ data[i]) & 0xff] ^ (crc >>> 8);
    }
    return (crc ^ 0xffffffff) >>> 0;
  }

  function concatBytes(parts: Uint8Array[]): Uint8Array {
    const length = parts.reduce((total, part) => total + part.length, 0);
    const result = new Uint8Array(length);
    let offset = 0;
    parts.forEach((part) => {
      result.set(part, offset);
      offset += part.length;
    });
    return result;
  }

  function getDosDateTime(date = new Date()) {
    const time =
      (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2);
    const dosDate =
      ((date.getFullYear() - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate();
    return { time, date: dosDate };
  }

  function createZip(files: { name: string; content: string }[]): Uint8Array {
    const encoder = new TextEncoder();
    const localParts: Uint8Array[] = [];
    const centralParts: Uint8Array[] = [];
    const { time, date } = getDosDateTime();
    let offset = 0;

    files.forEach((file) => {
      const nameBytes = encoder.encode(file.name);
      const dataBytes = encoder.encode(file.content);
      const crc = getCrc32(dataBytes);

      const localHeader = new Uint8Array(30 + nameBytes.length);
      const localView = new DataView(localHeader.buffer);
      localView.setUint32(0, 0x04034b50, true);
      localView.setUint16(4, 20, true);
      localView.setUint16(6, 0, true);
      localView.setUint16(8, 0, true);
      localView.setUint16(10, time, true);
      localView.setUint16(12, date, true);
      localView.setUint32(14, crc, true);
      localView.setUint32(18, dataBytes.length, true);
      localView.setUint32(22, dataBytes.length, true);
      localView.setUint16(26, nameBytes.length, true);
      localView.setUint16(28, 0, true);
      localHeader.set(nameBytes, 30);
      localParts.push(localHeader, dataBytes);

      const centralHeader = new Uint8Array(46 + nameBytes.length);
      const centralView = new DataView(centralHeader.buffer);
      centralView.setUint32(0, 0x02014b50, true);
      centralView.setUint16(4, 20, true);
      centralView.setUint16(6, 20, true);
      centralView.setUint16(8, 0, true);
      centralView.setUint16(10, 0, true);
      centralView.setUint16(12, time, true);
      centralView.setUint16(14, date, true);
      centralView.setUint32(16, crc, true);
      centralView.setUint32(20, dataBytes.length, true);
      centralView.setUint32(24, dataBytes.length, true);
      centralView.setUint16(28, nameBytes.length, true);
      centralView.setUint16(30, 0, true);
      centralView.setUint16(32, 0, true);
      centralView.setUint16(34, 0, true);
      centralView.setUint16(36, 0, true);
      centralView.setUint32(38, 0, true);
      centralView.setUint32(42, offset, true);
      centralHeader.set(nameBytes, 46);
      centralParts.push(centralHeader);

      offset += localHeader.length + dataBytes.length;
    });

    const centralDirectory = concatBytes(centralParts);
    const endRecord = new Uint8Array(22);
    const endView = new DataView(endRecord.buffer);
    endView.setUint32(0, 0x06054b50, true);
    endView.setUint16(8, files.length, true);
    endView.setUint16(10, files.length, true);
    endView.setUint32(12, centralDirectory.length, true);
    endView.setUint32(16, offset, true);
    endView.setUint16(20, 0, true);

    return concatBytes([...localParts, centralDirectory, endRecord]);
  }

  function createWorksheetXml(rows: any[][]): string {
    const sheetRows = rows
      .map((row, rowIndex) => {
        const rowNumber = rowIndex + 1;
        const cells = row
          .map((value, columnIndex) => {
            const ref = `${getColumnName(columnIndex)}${rowNumber}`;
            return `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${escapeXml(
              value
            )}</t></is></c>`;
          })
          .join('');
        return `<row r="${rowNumber}">${cells}</row>`;
      })
      .join('');
    return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${sheetRows}</sheetData></worksheet>`;
  }

  function createXlsxBlob(rows: any[][]): Blob {
    const worksheetXml = createWorksheetXml(rows);
    const zip = createZip([
      {
        name: '[Content_Types].xml',
        content:
          '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
      },
      {
        name: '_rels/.rels',
        content:
          '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
      },
      {
        name: 'xl/workbook.xml',
        content:
          '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>',
      },
      {
        name: 'xl/_rels/workbook.xml.rels',
        content:
          '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
      },
      {
        name: 'xl/worksheets/sheet1.xml',
        content: worksheetXml,
      },
    ]);
    return new Blob([zip.buffer as ArrayBuffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
  }

  function saveRowsAsExcel(rows: Recordable[]) {
    const columns = getExportColumns();
    const xlsxRows = [
      columns.map((column) => column.title),
      ...rows.map((row) => columns.map((column) => stringifyExcelValue(row[column.key]))),
    ];
    const blob = createXlsxBlob(xlsxRows);
    const fileName = `${props.exportFileName || props.title || 'table'}-${Date.now()}.xlsx`;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  async function getExportData(params: Recordable) {
    const { request, beforeRequest, afterRequest }: any = unref(getProps);
    const listField = APISETTING.listField;
    let requestParams = params;
    if (beforeRequest && isFunction(beforeRequest)) {
      requestParams = (await beforeRequest(requestParams)) || requestParams;
    }
    const res = await request(requestParams);
    let rows = res[listField] ? res[listField] : [];
    if (afterRequest && isFunction(afterRequest)) {
      rows = (await afterRequest(rows)) || rows;
    }
    return { res, rows };
  }

  async function downloadExcel() {
    const { request, pagination }: any = unref(getProps);
    if (!request || exporting.value) return;
    exporting.value = true;
    try {
      const pageField = APISETTING.pageField;
      const sizeField = APISETTING.sizeField;
      const totalField = APISETTING.totalField;
      const itemCount = APISETTING.countField;
      const currentPagination = unref(getPaginationInfo);
      const currentRows = unref(getDataSourceRef);
      const total =
        !isBoolean(currentPagination) && currentPagination[itemCount]
          ? currentPagination[itemCount]
          : currentRows.length;
      const pageSize = total > 0 ? total : 100000;
      const firstParams =
        (isBoolean(pagination) && !pagination) || isBoolean(currentPagination)
          ? {}
          : { [pageField]: 1, [sizeField]: pageSize };
      const { res, rows } = await getExportData(firstParams);
      const pageCount = Number(res[totalField] || 1);
      const responsePageSize = Number(res[sizeField] || rows.length || pageSize);
      let allRows = rows;

      if (pageCount > 1 && responsePageSize > 0) {
        for (let page = 2; page <= pageCount; page++) {
          const { rows: nextRows } = await getExportData({
            [pageField]: page,
            [sizeField]: responsePageSize,
          });
          allRows = allRows.concat(nextRows);
        }
      }
      saveRowsAsExcel(allRows);
    } catch (error) {
      console.error(error);
      window['$message']?.error?.(t('table.excelDownloadFailed'));
    } finally {
      exporting.value = false;
    }
  }

  const tableAction = {
    reload,
    setPagination,
    getPagination,
    setColumns,
    setLoading,
    setProps,
    getColumns,
    getDataSource,
    getPageColumns,
    getCacheColumns,
    getOriginalColumns,
    setCacheColumnsField,
    scrollTo,
    emit,
  };

  const getCanResize = computed(() => {
    const { canResize } = unref(getProps);
    return canResize;
  });

  async function computeTableHeight() {
    const table = unref(tableElRef);
    if (!table) return;
    if (!unref(getCanResize)) return;
    const tableEl: any = table?.$el;
    const tableWrapEl = tableEl.closest('.s-table') as HTMLElement | null;
    const tableContainerEl = tableWrapEl?.parentElement as HTMLElement | null;
    const toolbarEl = tableContainerEl?.querySelector(
      ':scope > .table-toolbar'
    ) as HTMLElement | null;
    const headEl = tableEl.querySelector('.n-data-table-thead ') as HTMLElement | null;
    const headH = headEl?.offsetHeight || 0;
    let paginationH = 2;
    let marginH = 12;
    if (!isBoolean(unref(pagination))) {
      paginationEl = tableEl.querySelector('.n-data-table__pagination') as HTMLElement;
      if (paginationEl) {
        const offsetHeight = paginationEl.offsetHeight;
        paginationH += offsetHeight || 0;
      } else {
        paginationH += 28;
      }
    }
    const viewportAnchorEl = headEl || (tableEl as HTMLElement);
    const parentAvailableHeight = tableContainerEl?.clientHeight
      ? tableContainerEl.clientHeight - (toolbarEl?.offsetHeight || 0)
      : 0;
    const viewportAvailableHeight = getViewportOffset(viewportAnchorEl).bottomIncludeBody;
    const availableHeight =
      parentAvailableHeight || tableWrapEl?.clientHeight || viewportAvailableHeight;
    let height =
      availableHeight - (headH + paginationH + marginH + (props.resizeHeightOffset || 0));
    const maxHeight = props.maxHeight;
    height = maxHeight && maxHeight < height ? maxHeight : height;
    deviceHeight.value = Math.max(150, height);
    measureShortDataBodyHeight(tableEl, unref(getDataSourceRef).length);
  }

  useWindowSizeFn(scheduleTableLayoutSync, 280);

  onMounted(() => {
    nextTick(() => {
      scheduleTableLayoutSync();
    });
  });

  onActivated(() => {
    scheduleTableLayoutSync();
  });

  onDeactivated(() => {
    saveTableScrollPosition();
    removeTableScrollListeners?.();
  });

  watch(
    () => [
      (unref(getProps) as any).columns,
      unref(getDataSourceRef).length,
      unref(getBindValues).scrollX,
      unref(pagination),
    ],
    () => scheduleTableLayoutSync(),
    { deep: true, flush: 'post' }
  );

  onBeforeUnmount(() => {
    clearResizeDragListeners();
    if (layoutSyncTimer) {
      window.clearTimeout(layoutSyncTimer);
      layoutSyncTimer = null;
    }
    layoutSyncRafIds.splice(0).forEach((rafId) => window.cancelAnimationFrame(rafId));
    removeTableScrollListeners?.();
    if (resizeClickSuppressTimer) {
      window.clearTimeout(resizeClickSuppressTimer);
      resizeClickSuppressTimer = null;
    }
  });

  createTableContext({ ...tableAction, wrapRef, getBindValues });

  defineExpose(tableAction);
</script>
<style lang="less" scoped>
  .table-toolbar {
    display: flex;
    justify-content: space-between;
    padding: 0 0 16px 0;

    &-left {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      flex: 1;

      &-title {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        font-size: 16px;
        font-weight: 600;
      }

      &-export {
        margin: 0 8px;
      }
    }

    &-right {
      display: flex;
      justify-content: flex-end;
      flex: 1;

      &-icon {
        margin-left: 12px;
        font-size: 16px;
        cursor: pointer;
        color: var(--text-color);

        :hover {
          color: #1890ff;
        }
      }
    }
  }

  .table-toolbar-inner-popover-title {
    padding: 2px 0;
  }

  .s-table {
    &--fit-content {
      flex: 0 0 auto !important;

      :deep(.n-data-table) {
        flex: 0 0 auto !important;
      }

      :deep(.n-data-table-base-table) {
        flex: 0 0 auto !important;
      }

      :deep(.n-data-table-base-table-body) {
        flex: 0 0 auto !important;
      }

      :deep(.n-data-table-wrapper) {
        min-height: 0 !important;
      }
    }

    &--short-data {
      flex: 0 0 auto !important;

      :deep(.n-data-table) {
        flex: 0 0 auto !important;
      }

      :deep(.n-data-table-base-table) {
        flex: 0 0 auto !important;
      }
    }

    :deep(.n-data-table-th) {
      background-color: color-mix(
        in srgb,
        var(--app-primary-color, #18a058) 24%,
        var(--n-merged-th-color, var(--n-th-color, #fafafc))
      ) !important;
      border-bottom-color: color-mix(
        in srgb,
        var(--app-primary-color, #18a058) 38%,
        var(--n-border-color, transparent)
      ) !important;
      color: var(--n-th-text-color, var(--n-text-color, inherit)) !important;
      font-weight: 600;
    }

    :deep(.n-data-table-resize-button) {
      width: 10px;
    }

    :deep(.n-data-table-resize-button::after) {
      background-color: color-mix(in srgb, var(--app-primary-color, #18a058) 40%, transparent);
      width: 2px;
    }

    :deep(.n-data-table-resize-button:hover::after) {
      background-color: color-mix(
        in srgb,
        var(--app-primary-color, #18a058) 78%,
        var(--n-text-color, #000)
      );
    }

    :deep(.n-data-table-sorter .n-base-icon svg path) {
      paint-order: stroke fill;
      stroke: currentColor;
      stroke-linejoin: round;
      stroke-width: 1.4px;
    }

    :deep(.n-data-table-th--fixed-left),
    :deep(.n-data-table-th--fixed-right) {
      background-color: color-mix(
        in srgb,
        var(--app-primary-color, #18a058) 24%,
        var(--n-merged-th-color, var(--n-th-color, #fafafc))
      ) !important;
      z-index: 3;
    }

    :deep(.n-data-table-td--fixed-left),
    :deep(.n-data-table-td--fixed-right) {
      background-color: var(--n-merged-td-color, var(--n-td-color, #fff)) !important;
      z-index: 2;
    }

    :deep(.basic-table-fixed-left-boundary::after),
    :deep(.basic-table-fixed-right-boundary::before) {
      display: none !important;
    }

    :deep(.basic-table-fixed-left-boundary) {
      filter: drop-shadow(4px 0 4px rgba(0, 0, 0, 0.12));
    }

    :deep(.basic-table-fixed-right-boundary) {
      filter: drop-shadow(-4px 0 4px rgba(0, 0, 0, 0.12));
    }

    :deep(.n-data-table-tr--striped .n-data-table-td--fixed-left),
    :deep(.n-data-table-tr--striped .n-data-table-td--fixed-right) {
      background-color: var(
        --n-merged-td-color-striped,
        var(--n-td-color-striped, var(--n-td-color, #fff))
      ) !important;
    }

    :deep(.n-data-table-tr:hover .n-data-table-td) {
      background-color: color-mix(
        in srgb,
        var(--app-primary-color, #18a058) 12%,
        var(--n-td-color, #fff)
      ) !important;
    }

    :deep(.n-data-table-tr:hover .n-data-table-td--fixed-left),
    :deep(.n-data-table-tr:hover .n-data-table-td--fixed-right) {
      background-color: color-mix(
        in srgb,
        var(--app-primary-color, #18a058) 12%,
        var(--n-merged-td-color, var(--n-td-color, #fff))
      ) !important;
    }
  }
  :global(.n-dropdown-menu .n-dropdown-option .n-dropdown-option-body::before) {
    top: 2px !important;
    bottom: 2px !important;
  }
</style>
