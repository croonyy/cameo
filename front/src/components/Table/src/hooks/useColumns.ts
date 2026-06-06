import { ref, Ref, ComputedRef, unref, computed, watch, toRaw, h } from 'vue';
import type { BasicColumn, BasicTableProps } from '../types/table';
import { cloneDeep } from 'lodash-es';
import { isArray, isString, isBoolean, isFunction } from '@/utils/is';
import { usePermission } from '@/hooks/web/usePermission';
import { ActionItem } from '@/components/Table';
import { renderEditCell } from '../components/editable';
import { NTooltip, NIcon } from 'naive-ui';
import { FormOutlined } from '@vicons/antd';

const FIXED_RESIZABLE_HANDLE_WIDTH = 8;
const MAX_COLUMN_WIDTH = 800;
const MIN_RESIZABLE_COLUMN_WIDTH = 48;
const ACTION_COLUMN_WIDTH = 148;
const FIXED_ORDER = {
  left: 0,
  normal: 1,
  right: 2,
};
const FIXED_LEFT_BOUNDARY_CLASS = 'basic-table-fixed-left-boundary';
const FIXED_RIGHT_BOUNDARY_CLASS = 'basic-table-fixed-right-boundary';

export function useColumns(propsRef: ComputedRef<BasicTableProps>) {
  const columnsRef = ref(unref(propsRef).columns) as unknown as Ref<BasicColumn[]>;
  let cacheColumns = cloneDeep(unref(propsRef).columns);
  let originalColumns = cloneDeep(unref(propsRef).columns);

  const getColumnsRef = computed(() => {
    const columns = cloneDeep(unref(columnsRef));

    handleActionColumn(propsRef, columns);
    if (!columns) return [];
    return columns;
  });

  const { hasPermission } = usePermission();

  function isIfShow(action: ActionItem): boolean {
    const ifShow = action.ifShow;

    let isIfShow = true;

    if (isBoolean(ifShow)) {
      isIfShow = ifShow;
    }
    if (isFunction(ifShow)) {
      isIfShow = ifShow(action);
    }
    return isIfShow;
  }

  const renderTooltip = (trigger, content) => {
    return h(NTooltip, null, {
      trigger: () => trigger,
      default: () => content,
    });
  };

  function getTitleText(title: any, fallback: any): string {
    if (typeof title === 'string' || typeof title === 'number') {
      return String(title);
    }
    if (typeof title === 'function') {
      return getTitleText(title(), fallback);
    }
    if (Array.isArray(title)) {
      return title.map((item) => getTitleText(item, '')).join('');
    }
    if (title && typeof title === 'object') {
      return getTitleText(title.children, fallback);
    }
    return fallback != null ? String(fallback) : '';
  }

  function getTextWidth(text: string) {
    return Array.from(text).reduce((width, char) => {
      return width + (/[\u4e00-\u9fa5]/.test(char) ? 16 : 9);
    }, 0);
  }

  function getContentWidth(column: BasicColumn) {
    const title = getTitleText(column.title, column.key);
    const keyText = column.key != null ? String(column.key) : '';
    const textWidth = Math.max(getTextWidth(title), getTextWidth(keyText));
    const headerControlsWidth =
      30 + (column.sorter ? 26 : 0) + (column.resizable ? 16 : 0) + (column.edit ? 20 : 0);
    return Math.min(Math.max(textWidth + headerControlsWidth, 112), MAX_COLUMN_WIDTH);
  }

  function getColumnWidth(column: BasicColumn) {
    if ((column as any).type === 'selection') return Number(column.width || 42);
    if (typeof column.width === 'number') return Math.min(column.width, MAX_COLUMN_WIDTH);
    if (column.key === 'action') return Number(column.width || ACTION_COLUMN_WIDTH);
    return getContentWidth(column);
  }

  function normalizeColumnFixed(column: BasicColumn) {
    if ((column as any).fixed === true) {
      column.fixed = 'left';
      return;
    }
    if (column.fixed !== 'left' && column.fixed !== 'right') {
      column.fixed = undefined;
    }
  }

  function normalizeColumnWidth(column: BasicColumn) {
    const baseWidth = getColumnWidth(column);
    const fixedWidthAdjusted = (column as any).__fixedWidthAdjusted;
    const shouldAdjustFixedWidth = column.fixed && column.resizable && !fixedWidthAdjusted;
    const width = shouldAdjustFixedWidth
      ? Math.min(baseWidth + FIXED_RESIZABLE_HANDLE_WIDTH, MAX_COLUMN_WIDTH)
      : baseWidth;
    column.width = width;
    if (column.resizable) {
      const minWidth = typeof column.minWidth === 'number' ? column.minWidth : undefined;
      column.minWidth =
        typeof minWidth === 'number' && minWidth < width ? minWidth : MIN_RESIZABLE_COLUMN_WIDTH;
    } else {
      column.minWidth = typeof column.minWidth === 'number' ? Math.min(column.minWidth, width) : width;
    }
    if (column.fixed) {
      (column as any).__fixedWidthAdjusted = true;
    } else {
      delete (column as any).__fixedWidthAdjusted;
    }
  }

  function normalizeFixedColumnsOrder(columns: BasicColumn[]) {
    return columns
      .map((column, index) => ({ column, index }))
      .sort((a, b) => {
        const aOrder = a.column.fixed ? FIXED_ORDER[a.column.fixed] : FIXED_ORDER.normal;
        const bOrder = b.column.fixed ? FIXED_ORDER[b.column.fixed] : FIXED_ORDER.normal;
        return aOrder === bOrder ? a.index - b.index : aOrder - bOrder;
      })
      .map(({ column }) => column);
  }

  function mergeColumnClassName(column: BasicColumn, className: string) {
    const currentClassName = column.className;
    if (typeof currentClassName === 'string') {
      column.className = currentClassName.includes(className)
        ? currentClassName
        : `${currentClassName} ${className}`;
      return;
    }
    if (Array.isArray(currentClassName)) {
      column.className = currentClassName.includes(className)
        ? currentClassName
        : [...currentClassName, className];
      return;
    }
    column.className = className;
  }

  function markFixedBoundaryColumns(columns: BasicColumn[]) {
    const orderedColumns = normalizeFixedColumnsOrder(columns);
    const lastLeftFixedColumn = [...orderedColumns]
      .reverse()
      .find((column) => column.fixed === 'left');
    const firstRightFixedColumn = orderedColumns.find((column) => column.fixed === 'right');

    if (lastLeftFixedColumn) {
      mergeColumnClassName(lastLeftFixedColumn, FIXED_LEFT_BOUNDARY_CLASS);
    }
    if (firstRightFixedColumn) {
      mergeColumnClassName(firstRightFixedColumn, FIXED_RIGHT_BOUNDARY_CLASS);
    }
    return orderedColumns;
  }

  function getColumnsScrollX(columns: BasicColumn[]) {
    return columns.reduce((total, column) => total + getColumnWidth(column), 0);
  }

  function getTitleMinWidth(column: BasicColumn) {
    const title = getTitleText(column.title, column.key);
    const keyText = column.key != null ? String(column.key) : '';
    return `${Math.min(Math.max(Math.max(getTextWidth(title), getTextWidth(keyText)), 48), 220)}px`;
  }

  function centerTitle(title: any, column: BasicColumn) {
    const minWidth = getTitleMinWidth(column);
    return () =>
      h(
        'div',
        {
          style: {
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            minWidth,
            maxWidth: '100%',
            overflow: 'visible',
            whiteSpace: 'nowrap',
          },
        },
        [isFunction(title) ? title() : title]
      );
  }

  function applyColumnLayout(column: BasicColumn) {
    if ((column as any).type === 'selection') return;
    normalizeColumnFixed(column);
    column.titleAlign = column.titleAlign || 'center';
    column.maxWidth = column.maxWidth || MAX_COLUMN_WIDTH;
    normalizeColumnWidth(column);
    column.title = centerTitle(column.title, column);
  }

  const getPageColumns = computed(() => {
    const pageColumns = unref(getColumnsRef);
    const columns = cloneDeep(pageColumns);
    const visibleColumns = columns
      .filter((column) => {
        return hasPermission(column.auth as string[]) && isIfShow(column);
      })
      .map((column) => {
        column.ellipsis = typeof column.ellipsis === 'undefined' ? { tooltip: true } : false;
        const { edit } = column;
        if (edit) {
          column.render = renderEditCell(column);
          const title: any = column.title;
          column.title = () => {
            return renderTooltip(
              h('div', { class: 'flex items-center' }, [
                h('span', { style: { 'margin-right': '5px' } }, title),
                h(
                  NIcon,
                  {
                    size: 14,
                  },
                  {
                    default: () => h(FormOutlined),
                  }
                ),
              ]),
              '该列可编辑'
            );
          };
        }
        applyColumnLayout(column);
        return column;
      });
    return markFixedBoundaryColumns(visibleColumns);
  });

  watch(
    () => unref(propsRef).columns,
    (columns) => {
      columnsRef.value = columns;
      cacheColumns = cloneDeep(columns);
      originalColumns = cloneDeep(columns);
    }
  );

  function handleActionColumn(propsRef: ComputedRef<BasicTableProps>, columns: BasicColumn[]) {
    const { actionColumn } = unref(propsRef);
    if (!actionColumn) return;
    !columns.find((col) => col.key === 'action') &&
      columns.push({
        ...(actionColumn as any),
      });
  }

  function setColumns(columnList: string[] | any[]) {
    const columns: any[] = cloneDeep(columnList);
    if (!isArray(columns)) return;

    if (!columns.length) {
      columnsRef.value = [];
      return;
    }

    if (isString(columns[0])) {
      const columnKeys = columns as string[];
      const newColumns: any[] = [];
      columnKeys.forEach((key) => {
        if (key === 'selection') {
          newColumns.push({ type: 'selection', key: 'selection' });
          return;
        }
        const cacheItem = cacheColumns.find((item) => item.key === key);
        if (cacheItem) {
          newColumns.push({ ...cacheItem });
        }
      });
      columnsRef.value = newColumns;
    } else {
      const newColumns = columns.map((col) => {
        if (col.type === 'selection') {
          return { ...col };
        }
        normalizeColumnFixed(col);
        const cacheItem = cacheColumns.find((item) => item.key === col.key);
        if (cacheItem) {
          return { ...cacheItem, ...col };
        }
        return { ...col };
      });
      columnsRef.value = newColumns;
      newColumns.forEach((col) => {
        if (col.type === 'selection') return;
        const cacheIdx = cacheColumns.findIndex((item) => item.key === col.key);
        if (cacheIdx !== -1) {
          cacheColumns[cacheIdx] = { ...col };
        }
      });
    }
  }

  function getColumns(): BasicColumn[] {
    const columns = toRaw(unref(getColumnsRef));
    return columns.map((item) => {
      const column = { ...item, fixed: item.fixed || undefined };
      normalizeColumnFixed(column);
      normalizeColumnWidth(column);
      return column;
    });
  }

  function getCacheColumns(isKey?: boolean): any[] {
    return isKey ? cacheColumns.map((item) => item.key) : cacheColumns.map((item) => ({ ...item }));
  }

  function getOriginalColumns(isKey?: boolean): any[] {
    return isKey
      ? originalColumns.map((item) => item.key)
      : originalColumns.map((item) => ({ ...item }));
  }

  function setCacheColumnsField(key: string | undefined, value: Partial<BasicColumn>) {
    if (!key || !value) {
      return;
    }
    cacheColumns.forEach((item) => {
      if (item.key === key) {
        Object.assign(item, value);
        normalizeColumnFixed(item);
        return;
      }
    });
  }

  return {
    getColumnsRef,
    getCacheColumns,
    getOriginalColumns,
    setCacheColumnsField,
    setColumns,
    getColumns,
    getPageColumns,
    getColumnsScrollX,
  };
}
