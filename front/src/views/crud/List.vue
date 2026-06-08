<template>
  <div ref="listRootRef" class="crud-list-wrapper" @scroll.capture="handleListScroll">
    <n-card v-if="conditionCardVisible" :bordered="false" class="condition-card">
      <BasicForm @register="register" @submit="handleSubmit" @reset="handleReset">
        <template #statusSlot="{ model, field }">
          <n-input v-model:value="model[field]" />
        </template>
      </BasicForm>
    </n-card>

    <!-- <TextOutline /> -->

    <!-- <n-card :bordered="false" class="mt-3"> -->
    <n-card :bordered="false" class="table-card">
      <!-- v-if="pk" -->
      <!-- title="表格列表" 被插槽覆盖了-->
      <!-- :request="loadDataTable" -->
      <BasicTable
        v-if="pk"
        :columns="columns"
        :request="loadDataTable"
        :row-key="getRowKeyValue"
        ref="actionRef"
        :actionColumn="actionColumn"
        :show-row-selection="rowSelectionEnabled"
        :checked-row-keys="selectedRowKeys"
        @update:checked-row-keys="onCheckedRow"
        @update:sorter="handleSorterChange"
        @fetch-success="handleTableFetchSuccess"
        :striped="true"
        :virtual-scroll="true"
        :pagination="tablePagination"
      >
        <template #tableTitle>
          <n-space align="center">
            <!-- 判断‘${appName}:${modelName}:create’权限，有则显示新建按钮，没有则不显示’ -->
            <template
              v-if="perms.includes(`${appName}:${modelName}:create`) || userInfo.is_superuser"
            >
              <n-button type="primary" @click="handleCreate">
                <template #icon>
                  <n-icon>
                    <PlusOutlined />
                  </n-icon>
                </template>
                {{ t('button.create') }}
              </n-button>
            </template>
            <n-checkbox
              v-if="canDeleteRows"
              v-model:checked="rowSelectionEnabled"
              @update:checked="handleRowSelectionChecked"
            >
              {{ t('button.selectRows') }}
            </n-checkbox>
            <n-button
              v-if="selectedRowKeys.length && canDeleteRows"
              type="error"
              secondary
              @click="handleBatchDelete"
            >
              <template #icon>
                <n-icon>
                  <DeleteOutlined />
                </n-icon>
              </template>
              {{ t('button.deleteSelected') }} ({{ selectedRowKeys.length }})
            </n-button>
            <n-button v-if="selectedRowKeys.length" text type="info" @click="clearSelectedRows">
              {{ t('button.clearSelection') }}
            </n-button>
            <!-- 保存全部按钮 -->
            <n-button v-if="hasAnyUnsavedEdits" type="success" @click="saveAllInlineEdits">
              <template #icon>
                <n-icon>
                  <SaveOutlined />
                </n-icon>
              </template>
              {{ t('button.saveAll') }} ({{ unsavedEditsCount }})
            </n-button>
            <!-- 重置修改按钮 -->
            <n-button v-if="hasAnyUnsavedEdits" type="warning" @click="resetAllEdits">
              <template #icon>
                <n-icon>
                  <ReloadOutlined />
                </n-icon>
              </template>
              {{ t('button.resetChanges') }}
            </n-button>
            <n-button
              v-for="action in customToolbarActions"
              :key="action.key"
              :type="action.type || 'default'"
              :disabled="isCustomActionDisabled(action)"
              @click="handleCustomAction(action)"
            >
              <template #icon v-if="resolveCustomActionIcon(action.icon)">
                <n-icon>
                  <component :is="resolveCustomActionIcon(action.icon)" />
                </n-icon>
              </template>
              {{ getCustomActionLabel(action) }}
            </n-button>
          </n-space>
        </template>
      </BasicTable>
    </n-card>
  </div>
</template>

<script setup lang="ts">
  import {
    ref,
    computed,
    onMounted,
    h,
    defineComponent,
    nextTick,
    watch,
    onActivated, // 当组件缓存的时候，激活组件触发的钩子函数
    onDeactivated,
    onUnmounted, // 当组件缓存的时候，离开组件触发的钩子函数
  } from 'vue';
  import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, FormSchema, useForm } from '@/components/Form/index';
  import {
    PlusOutlined,
    SaveOutlined,
    EditOutlined,
    ReloadOutlined,
    DeleteOutlined,
  } from '@vicons/antd';
  import { executeCustomAction } from './customActions';
  import type { CustomActionConfig, CustomActionCondition } from './customActions';
  import {
    GetAllowModelInfo,
    DeleteModelItem,
    GetModelItemList,
    UpdateModelItem,
  } from '@/api/crud/models';
  import { FilterFieldComponentMap } from './cmpsFilter';
  import { GenerateFilter } from './filterData';
  import { SearchFieldComponent } from './cmpsSearch';
  import {
    columnRenderMap,
    formatListDisplayValue,
    getFieldAlign,
    translateKnownDataText,
  } from './columnRender';
  import {
    buildChoiceOptions,
    formatChoiceValue,
    getTextWidth,
    hasChoices,
    normalizeChoiceValue,
  } from './tools';
  import { CRUD_LIST, CRUD_EDIT, CRUD_CREATE } from '@/store/consts';
  import { useCrudRefresh } from '@/store/modules/crudListRefresh';
  import { UserInfoType, useUserStore } from '@/store/modules/user';
  import { isEqual } from 'lodash-es';
  import { storage } from '@/utils/Storage';
  import { t } from '@/i18n';
  import componentSetting from '@/settings/componentSetting';
  import {
    BOOLEAN_LIKE_FIELD_TYPES,
    DATE_LIKE_FIELD_TYPES,
    DATETIME_LIKE_FIELD_TYPES,
    JSON_LIKE_FIELD_TYPES,
    MANY_RELATION_FIELD_TYPES,
    NUMBER_LIKE_FIELD_TYPES,
    SINGLE_RELATION_FIELD_TYPES,
    TEXT_LIKE_FIELD_TYPES,
    TIME_LIKE_FIELD_TYPES,
  } from './types';

  const userStore = useUserStore();
  const userInfo: UserInfoType = userStore.getUserInfo || {};

  import {
    useMessage,
    NIcon,
    NCheckbox,
    NSelect,
    NDatePicker,
    NTimePicker,
    NInputNumber,
    NInput,
  } from 'naive-ui';

  const message = useMessage();
  const currentRoute = useRoute();
  const router = useRouter();
  const tabFullPath = currentRoute.fullPath;
  const tabAppName = currentRoute.params.app_name as string;
  const tabModelName = currentRoute.params.model_name as string;
  // const route = useRoute();
  const crudRefresh = useCrudRefresh();
  const appName = computed(() => currentRoute.params.app_name as string);
  const modelName = computed(() => currentRoute.params.model_name as string);
  const modelInfo = ref();
  // const perms = modelInfo.value?.perms || [];
  const columns = ref<any[]>([]);
  const listRootRef = ref<HTMLElement | null>(null);
  const rowSelectionEnabled = ref(false);
  const selectedRowKeys = ref<Array<string | number>>([]);
  const selectedRowMap = ref<Record<string, Recordable>>({});
  const schemas = ref<FormSchema[]>([]);
  const actionRef = ref();
  const g_filters = ref<any[]>([]);
  const g_sorter = ref<any>(null);
  const tableData = ref<any[]>([]);
  const notifyNoDataAfterSearch = ref(false);

  type ListScrollType = 'table-y' | 'table-x' | 'list';

  function getListScrollStorageKey(type: ListScrollType) {
    return `crud:${tabAppName}:${tabModelName}:${type}:scroll`;
  }

  function getStoredScrollPosition(type: ListScrollType) {
    const key = getListScrollStorageKey(type);
    const rawValue = sessionStorage.getItem(key);
    if (!rawValue) return null;
    try {
      return JSON.parse(rawValue);
    } catch {
      sessionStorage.removeItem(key);
      return null;
    }
  }

  function clearListScrollPosition() {
    (['table-y', 'table-x', 'list'] as ListScrollType[]).forEach((type) => {
      sessionStorage.removeItem(getListScrollStorageKey(type));
    });
    sessionStorage.removeItem(`crud:${tabAppName}:${tabModelName}:table:scroll`);
  }
  const ACTION_BUTTON_WIDTH = 52;
  const ACTION_BUTTON_GAP = 4;
  const ACTION_CELL_PADDING = 32;
  const ACTION_COLUMN_TITLE_WIDTH = 76;
  const ACTION_COLUMN_MIN_WIDTH = 100;
  const ACTION_COLUMN_MAX_WIDTH = 200;

  function getActionButtonWidth(label: string) {
    return Math.max(ACTION_BUTTON_WIDTH, getTextWidth(label) + 24);
  }

  function getActionButtonsWidth(labels: string[]) {
    if (!labels.length) return 0;
    return (
      labels.reduce((total, label) => total + getActionButtonWidth(label), 0) +
      Math.max(0, labels.length - 1) * ACTION_BUTTON_GAP +
      ACTION_CELL_PADDING
    );
  }

  const actionColumnWidth = computed(() => {
    if (!canShowActionColumn.value) return 0;

    const normalActionLabels = [
      ...(canUpdateRows.value ? [t('button.edit')] : []),
      ...(canDeleteRows.value ? [t('button.delete')] : []),
      ...customRowActions.value.map((action) => getCustomActionLabel(action)),
    ];
    const rowActionLabels = hasAnyUnsavedEdits.value
      ? [t('button.save'), ...normalActionLabels]
      : normalActionLabels;
    const buttonsWidth = getActionButtonsWidth(rowActionLabels);
    const idealWidth = Math.max(ACTION_COLUMN_TITLE_WIDTH, buttonsWidth, ACTION_COLUMN_MIN_WIDTH);

    return Math.min(idealWidth, ACTION_COLUMN_MAX_WIDTH);
  });

  const paginationStorageKey = `crud_list_pagination_${currentRoute.params.app_name}_${currentRoute.params.model_name}`;
  const savedPagination =
    crudRefresh.getPaginationState(
      currentRoute.params.app_name as string,
      currentRoute.params.model_name as string
    ) || storage.get(paginationStorageKey, null);
  const validPageSizes = componentSetting.table.pageSizes;
  const defaultPageSize = componentSetting.table.defaultPageSize;
  function normalizePageSize(pageSize: any) {
    const numericPageSize = Number(pageSize);
    return validPageSizes.includes(numericPageSize) ? numericPageSize : defaultPageSize;
  }
  // Track current pagination state - will be properly initialized in onMounted
  const currentPage = ref(
    Number.isFinite(savedPagination?.page) && savedPagination.page > 0 ? savedPagination.page : 1
  );
  const currentPageSize = ref(normalizePageSize(savedPagination?.pageSize));
  const tablePagination = computed(() => ({
    page: currentPage.value,
    pageSize: currentPageSize.value,
  }));
  const pendingRestoreTableScroll = ref(false);
  // Track if this is the first activation (to avoid double loading)
  const isFirstActivation = ref(true);
  const tableVerticalScrollPosition = ref({ top: 0 });
  const tableHorizontalScrollPosition = ref({ left: 0 });
  const pageScrollPosition = ref({ top: 0, left: 0 });
  let removeTableScrollListeners: (() => void) | null = null;
  let finishRestoreTimer: number | null = null;
  const tableRestoreTimers: number[] = [];
  const tableRestoreRafIds: number[] = [];
  let tableRestoreToken = 0;
  let isApplyingTableScrollRestore = false;
  let isTabClosed = false;
  const handleSavedTableScroll = () => {
    if (isTabClosed || currentRoute.fullPath !== tabFullPath || isApplyingTableScrollRestore)
      return;
    if (pendingRestoreTableScroll.value) {
      return;
    }
    saveTableScrollPosition();
  };
  const handleListScroll = () => {
    if (isTabClosed) return;
    saveTableScrollPosition();
  };
  const handleTabsCardBeforeSwitch = (event: Event) => {
    if (isTabClosed) return;
    const detail = (event as CustomEvent).detail;
    if (detail?.fromFullPath === tabFullPath) {
      clearPendingTableScrollRestore();
      saveTableScrollPosition(true);
    }
  };
  const handleTabsCardClosed = (event: Event) => {
    const detail = (event as CustomEvent).detail;
    if (!Array.isArray(detail?.fullPaths) || !detail.fullPaths.includes(tabFullPath)) return;
    isTabClosed = true;
    clearPendingTableScrollRestore();
    clearListScrollPosition();
  };
  // 本地数据副本，用于局部更新
  const conditionCardVisible = computed<boolean>(() => {
    if (!modelInfo.value?.ui) return false;
    return modelInfo.value.ui.search_fields.length > 0 || modelInfo.value.ui.list_filter.length > 0;
  });
  const pk = ref<string>('');
  const editableFields = ref<string[]>([]);
  // Track inline edits: { rowId: { fieldName: newValue } }
  const inlineEdits = ref<Record<string, Record<string, any>>>({});

  // EditableCell component — manages its own isEditing state so Vue reactivity works
  // independently of the DataTable's render cache
  // Renders different edit components based on field type:
  //   Boolean → NCheckbox (no double-click, just toggle)
  //   Enum types (choices) → NSelect (no double-click, click to open)
  //   Date/DateTime → NDatePicker
  //   Number types → NInputNumber
  //   String/Text/others → input (double-click to edit)
  defineOptions({
    name: CRUD_LIST,
  });

  const EditableCell = defineComponent({
    props: {
      value: { type: null, default: undefined },
      rowId: { type: [String, Number], required: true },
      fieldName: { type: String, required: true },
      fieldType: { type: String, default: 'String' },
      canEdit: { type: Boolean, default: false },
      choices: { type: [Array, Object], default: null },
      align: { type: String, default: 'right' },
    },
    emits: ['change'],
    setup(props, { emit }) {
      const isEditing = ref(false);
      const editValue = ref<any>(undefined);
      const inputEl = ref<any>(null);
      const hasChanged = ref(false);

      function startEdit() {
        if (!props.canEdit) return;
        // For object values (JSON), stringify for display in input
        editValue.value =
          props.value != null && typeof props.value === 'object'
            ? JSON.stringify(props.value, null, 2)
            : props.value;
        hasChanged.value = false;
        isEditing.value = true;
        nextTick(() => {
          inputEl.value?.focus();
        });
      }

      function stopEdit() {
        isEditing.value = false;
        hasChanged.value = false;
      }

      function isInNaiveOverlay(target: EventTarget | null) {
        if (!(target instanceof HTMLElement)) return false;
        return !!target.closest(
          [
            '.v-binder-follower-container',
            '.n-base-select-menu',
            '.n-date-panel',
            '.n-time-panel',
            '.n-popover',
          ].join(',')
        );
      }

      function onDocMouseDown(e: MouseEvent) {
        if (!isEditing.value) return;
        const el = inputEl.value?.$el || inputEl.value;
        if (isInNaiveOverlay(e.target)) return;
        if (el && !el.contains(e.target as Node)) {
          stopEdit();
        }
      }

      function emitChange(val: any) {
        editValue.value = val;
        hasChanged.value = true;
        emit('change', props.rowId, props.fieldName, val);
      }

      onMounted(() => document.addEventListener('mousedown', onDocMouseDown, true));
      onUnmounted(() => document.removeEventListener('mousedown', onDocMouseDown, true));

      function getJustifyContent() {
        if (props.align === 'center') return 'center';
        if (props.align === 'right') return 'flex-end';
        return 'flex-start';
      }

      function getAlignedControlStyle(width = 'auto') {
        const margin =
          props.align === 'center'
            ? '0 auto'
            : props.align === 'right'
            ? '0 0 0 auto'
            : '0 auto 0 0';
        return `display:block;width:${width};margin:${margin};box-sizing:border-box;text-align:${props.align};`;
      }

      function renderAlignedContent(content: any) {
        return h(
          'div',
          {
            class: 'inline-edit-aligned-content',
            style: `display:flex;width:100%;min-width:0;justify-content:${getJustifyContent()};text-align:${
              props.align
            };`,
          },
          [content]
        );
      }

      const fullWidthEditWrapperStyle =
        'display:block;width:100%;min-width:0;max-width:100%;box-sizing:border-box;text-align:left;';
      const fullWidthTextareaStyle =
        'display:block;width:100%;min-width:0;max-width:100%;box-sizing:border-box;text-align:left;';
      const displayTextStyle =
        'cursor:pointer;border-bottom:1px dashed #999;padding:0 1px;min-width:0;min-height:20px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-block;vertical-align:middle;line-height:1.4;';

      function getDisplayText(value: any) {
        return formatListDisplayValue(value);
      }

      function getJsonDisplayText(value: any) {
        return value === null || value === undefined
          ? formatListDisplayValue(value)
          : JSON.stringify(translateKnownDataText(value));
      }

      function renderFullWidthEditor(editor: any) {
        return h('div', { class: 'inline-edit-editor-shell', style: fullWidthEditWrapperStyle }, [
          editor,
        ]);
      }

      function padDatePart(value: number) {
        return String(value).padStart(2, '0');
      }

      function formatLocalDate(value: Date) {
        return `${value.getFullYear()}-${padDatePart(value.getMonth() + 1)}-${padDatePart(
          value.getDate()
        )}`;
      }

      function formatLocalTime(value: Date) {
        return `${padDatePart(value.getHours())}:${padDatePart(value.getMinutes())}:${padDatePart(
          value.getSeconds()
        )}`;
      }

      function normalizeDatePickerValue(value: any, isDateTime: boolean): string | null {
        if (value == null || value === '') return null;
        if (value instanceof Date) {
          if (Number.isNaN(value.getTime())) return null;
          return isDateTime
            ? `${formatLocalDate(value)} ${formatLocalTime(value)}`
            : formatLocalDate(value);
        }
        if (typeof value === 'number') {
          const date = new Date(value);
          if (Number.isNaN(date.getTime())) return null;
          return isDateTime
            ? `${formatLocalDate(date)} ${formatLocalTime(date)}`
            : formatLocalDate(date);
        }

        const rawValue = String(value).trim();
        if (!rawValue) return null;
        const dateMatch = rawValue.match(/^(\d{4}-\d{2}-\d{2})/);
        if (!dateMatch) return null;
        if (!isDateTime) return dateMatch[1];

        const timeMatch = rawValue.match(/[T\s](\d{2}:\d{2})(?::(\d{2}))?/);
        if (!timeMatch) return `${dateMatch[1]} 00:00:00`;
        return `${dateMatch[1]} ${timeMatch[1]}:${timeMatch[2] ?? '00'}`;
      }

      function formatDateDisplayValue(value: any, isDateTime: boolean) {
        const normalizedValue = normalizeDatePickerValue(value, isDateTime);
        if (normalizedValue !== null) return normalizedValue;
        if (value === null || value === undefined || value === '') return value;
        return String(value);
      }

      function normalizeTimePickerValue(value: any): string | null {
        if (value == null || value === '') return null;
        if (value instanceof Date) {
          if (Number.isNaN(value.getTime())) return null;
          return formatLocalTime(value);
        }
        if (typeof value === 'number') {
          const date = new Date(value);
          if (Number.isNaN(date.getTime())) return null;
          return formatLocalTime(date);
        }
        const rawValue = String(value).trim();
        const timeMatch = rawValue.match(/(?:^|[T\s])(\d{2}:\d{2})(?::(\d{2}))?/);
        if (!timeMatch) return null;
        return `${timeMatch[1]}:${timeMatch[2] ?? '00'}`;
      }

      // ---- Boolean: direct checkbox toggle ----
      if (BOOLEAN_LIKE_FIELD_TYPES.has(props.fieldType)) {
        const currentValue = computed(() => !!(editValue.value ?? props.value));
        return () => {
          if (!props.canEdit) {
            return renderAlignedContent(
              h(
                'span',
                {},
                props.value === null || props.value === undefined
                  ? getDisplayText(props.value)
                  : props.value
                  ? t('common.yes')
                  : t('common.no')
              )
            );
          }
          return renderAlignedContent(
            h(NCheckbox, {
              checked: currentValue.value,
              onUpdateChecked: (val: boolean) => emitChange(val),
              style: 'transform: scale(0.85);',
            })
          );
        };
      }

      // ---- Enum types: direct select dropdown ----
      if (hasChoices(props.choices)) {
        const selectOptions = buildChoiceOptions(props.choices);
        return () => {
          const currentValue = normalizeChoiceValue(editValue.value ?? props.value, props.choices);
          if (!props.canEdit) {
            return renderAlignedContent(
              h('span', {}, formatChoiceValue(currentValue, props.choices))
            );
          }
          return renderAlignedContent(
            h(NSelect, {
              value: currentValue,
              options: selectOptions,
              size: 'tiny',
              style: `${getAlignedControlStyle('70%')}min-width:80px;max-width:300px;`,
              consistentMenuWidth: false,
              onUpdateValue: (val: any) => emitChange(val),
            })
          );
        };
      }

      // ---- Date/DateTime: date picker ----
      if (
        DATE_LIKE_FIELD_TYPES.has(props.fieldType) ||
        DATETIME_LIKE_FIELD_TYPES.has(props.fieldType)
      ) {
        const isDateTime = DATETIME_LIKE_FIELD_TYPES.has(props.fieldType);
        const valueFormat = isDateTime ? 'yyyy-MM-dd HH:mm:ss' : 'yyyy-MM-dd';
        return () => {
          if (!props.canEdit) {
            return renderAlignedContent(
              h('span', {}, getDisplayText(formatDateDisplayValue(props.value, isDateTime)))
            );
          }
          // In editing mode, show date picker
          if (isEditing.value) {
            return h(NDatePicker, {
              ref: inputEl,
              formattedValue: normalizeDatePickerValue(editValue.value ?? props.value, isDateTime),
              valueFormat,
              type: isDateTime ? 'datetime' : 'date',
              format: valueFormat,
              size: 'small',
              style: getAlignedControlStyle('100%'),
              onUpdateFormattedValue: (val: string | null) => emitChange(val),
            });
          }
          // Display mode: double-click to edit
          const displayVal = getDisplayText(formatDateDisplayValue(props.value, isDateTime));
          return h(
            'span',
            {
              style: `${displayTextStyle}text-align:${props.align};`,
              onDblclick: startEdit,
            },
            displayVal
          );
        };
      }

      // ---- Time: time picker ----
      if (TIME_LIKE_FIELD_TYPES.has(props.fieldType)) {
        return () => {
          if (!props.canEdit) {
            return renderAlignedContent(h('span', {}, getDisplayText(props.value)));
          }
          if (isEditing.value) {
            return h(NTimePicker, {
              ref: inputEl,
              formattedValue: normalizeTimePickerValue(editValue.value ?? props.value),
              valueFormat: 'HH:mm:ss',
              format: 'HH:mm:ss',
              size: 'small',
              style: getAlignedControlStyle('100%'),
              onUpdateFormattedValue: (val: string | null) => emitChange(val),
            });
          }
          const displayVal = getDisplayText(props.value);
          return h(
            'span',
            {
              style: `${displayTextStyle}text-align:${props.align};`,
              onDblclick: startEdit,
            },
            displayVal
          );
        };
      }

      // ---- Number types: input number ----
      if (NUMBER_LIKE_FIELD_TYPES.has(props.fieldType)) {
        return () => {
          if (!props.canEdit) {
            return h('span', {}, getDisplayText(props.value));
          }
          if (isEditing.value) {
            return h(NInputNumber, {
              ref: inputEl,
              value: editValue.value ?? props.value,
              size: 'tiny',
              style: getAlignedControlStyle('100%'),
              showButton: false,
              onUpdateValue: (val: number | null) => emitChange(val),
            });
          }
          const displayVal = getDisplayText(props.value);
          return h(
            'span',
            {
              style: `${displayTextStyle}text-align:${props.align};`,
              onDblclick: startEdit,
            },
            displayVal
          );
        };
      }

      // ---- JSON types: textarea ----
      if (JSON_LIKE_FIELD_TYPES.has(props.fieldType)) {
        return () => {
          if (!props.canEdit) {
            return h('span', {}, getJsonDisplayText(props.value));
          }
          if (isEditing.value) {
            return renderFullWidthEditor(
              h(NInput, {
                ref: inputEl,
                value:
                  editValue.value != null
                    ? typeof editValue.value === 'object'
                      ? JSON.stringify(editValue.value, null, 2)
                      : String(editValue.value)
                    : '',
                type: 'textarea',
                size: 'tiny',
                rows: 2,
                class: 'inline-textarea-editor',
                style: fullWidthTextareaStyle,
                onUpdateValue: (val: string) => {
                  editValue.value = val;
                  // Try to parse as JSON
                  try {
                    const parsed = JSON.parse(val);
                    emit('change', props.rowId, props.fieldName, parsed);
                  } catch {
                    // Keep as string if not valid JSON
                    emit('change', props.rowId, props.fieldName, val);
                  }
                },
              })
            );
          }
          const displayVal = getJsonDisplayText(props.value);
          return h(
            'span',
            {
              style: `${displayTextStyle}font-size:12px;`,
              onDblclick: startEdit,
            },
            displayVal
          );
        };
      }

      // ---- Text types: textarea ----
      if (TEXT_LIKE_FIELD_TYPES.has(props.fieldType)) {
        return () => {
          if (!props.canEdit) {
            return h('span', {}, getDisplayText(props.value));
          }
          if (isEditing.value) {
            return renderFullWidthEditor(
              h(NInput, {
                ref: inputEl,
                value: editValue.value ?? props.value ?? '',
                type: 'textarea',
                size: 'tiny',
                rows: 2,
                class: 'inline-textarea-editor',
                style: fullWidthTextareaStyle,
                onUpdateValue: (val: string) => emitChange(val),
              })
            );
          }
          const displayVal = getDisplayText(props.value);
          return h(
            'span',
            {
              style: displayTextStyle,
              onDblclick: startEdit,
            },
            displayVal
          );
        };
      }

      // ---- Default: string input, double-click to edit ----
      return () => {
        if (isEditing.value && props.canEdit) {
          return h(NInput, {
            ref: inputEl,
            value: editValue.value ?? props.value ?? '',
            size: 'tiny',
            style: 'width:100%;',
            onUpdateValue: (val: string) => emitChange(val),
          });
        }
        const displayVal = getDisplayText(props.value);
        return h(
          'span',
          {
            style: props.canEdit ? `${displayTextStyle}text-align:${props.align};` : '',
            onDblclick: startEdit,
          },
          displayVal
        );
      };
    },
  });
  // 查询表单，getFieldsValue作用是获取表单的值
  const [register, { getFieldsValue }] = useForm({
    gridProps: {
      cols: '1 s:2 m:3 l:3 xl:4 2xl:4',
      xGap: 16,
      yGap: 10,
      collapsedRows: 1,
    },
    size: 'small',
    collapsedRows: 1,
    labelWidth: 'auto',
    labelPlacement: 'top',
    // @ts-ignore
    labelAlign: 'left',
    schemas,
  });

  // 查询表单提交
  async function handleSubmit(values: Recordable) {
    console.log('@@@getSearchFormValues', getFieldsValue());
    const filters = GenerateFilter(values, modelInfo);
    g_filters.value = filters;
    notifyNoDataAfterSearch.value = true;
    currentPage.value = 1;
    actionRef.value?.setPagination({
      page: currentPage.value,
      pageSize: currentPageSize.value,
    });
    // 直接调用表格的reload方法刷新数据
    reloadTable();
  }
  // 表单重置
  function handleReset() {
    g_filters.value = [];
    notifyNoDataAfterSearch.value = false;
    currentPage.value = 1;
    actionRef.value?.setPagination({
      page: currentPage.value,
      pageSize: currentPageSize.value,
    });
    reloadTable();
  }

  const loadDataTable = async (res) => {
    // res 里面有查询的页码和每页条数
    const ui = modelInfo.value?.ui;
    const defaultOrdering = ui?.ordering?.length > 0 ? ui.ordering : [`-${pk.value}`];
    // Use sorter from column header click, otherwise use default ordering from ui config
    const currentOrderBy = g_sorter.value
      ? [
          g_sorter.value.order === 'descend'
            ? `-${g_sorter.value.columnKey}`
            : String(g_sorter.value.columnKey),
        ]
      : defaultOrdering;
    const params = {
      curr_page: res.page || currentPage.value,
      page_size: res.pageSize || currentPageSize.value,
      order_by: currentOrderBy,
      filters: g_filters.value,
    };
    // Update local refs (but don't sync to store - only sync on user interaction)
    currentPage.value = params.curr_page;
    currentPageSize.value = params.page_size;
    persistPaginationState();

    const { data, extra } = await GetModelItemList(appName.value, modelName.value, params);
    // 保存数据副本用于局部更新
    tableData.value = data;
    const result = {
      itemCount: extra.paginator.total,
      list: data,
      page: extra.paginator.curr_page,
      pageCount: extra.paginator.page_cnt,
      pageSize: extra.paginator.page_size,
    };
    if (notifyNoDataAfterSearch.value) {
      notifyNoDataAfterSearch.value = false;
      if (result.itemCount === 0) {
        message.warning(t('common.noData'));
      }
    }
    return result;
  };

  // 监听刷新标志变化
  // watch(
  //   () => crudRefresh.getRefreshFlag(appName.value, modelName.value),
  //   (needsRefresh) => {
  //     if (needsRefresh) {
  //       reloadTable();
  //       crudRefresh.clearRefreshFlag(appName.value, modelName.value);
  //     }
  //   }
  // );
  const perms = computed(() => {
    return modelInfo.value?.perms || [];
  });
  const canDeleteRows = computed(() => {
    return (
      perms.value.includes(`${appName.value}:${modelName.value}:delete`) || userInfo.is_superuser
    );
  });
  const canUpdateRows = computed(() => {
    return (
      perms.value.includes(`${appName.value}:${modelName.value}:update`) || userInfo.is_superuser
    );
  });
  const customActions = computed<CustomActionConfig[]>(() => {
    return modelInfo.value?.ui?.custom_actions || [];
  });
  const customRowActions = computed(() => {
    return customActions.value.filter(
      (action) => (action.placement || 'row') === 'row' && hasCustomActionPermission(action)
    );
  });
  const customToolbarActions = computed(() => {
    return customActions.value.filter(
      (action) =>
        action.placement === 'toolbar' &&
        hasCustomActionPermission(action) &&
        isCustomActionVisible(action)
    );
  });
  const customActionIconMap: Record<string, any> = {
    PlusOutlined,
    SaveOutlined,
    EditOutlined,
    ReloadOutlined,
    DeleteOutlined,
  };

  function resolveCustomActionIcon(icon?: string) {
    return icon ? customActionIconMap[icon] : null;
  }

  function getCustomActionLabel(action: CustomActionConfig) {
    const labelKeyMap: Record<string, string> = {
      detail_row_preview: 'crud.rowId',
      detail_row_record: 'crud.rowObject',
      detail_toolbar_summary: 'crud.selectedId',
      detail_toolbar_records: 'crud.selectedRows',
    };
    const key = labelKeyMap[action.key];
    return key ? t(key) : action.label;
  }

  function hasCustomActionPermission(action: CustomActionConfig) {
    if (userInfo.is_superuser || !action.permission) return true;
    const permission = action.permission.includes(':')
      ? action.permission
      : `${appName.value}:${modelName.value}:${action.permission}`;
    return perms.value.includes(permission);
  }

  function normalizeCustomActionConditions(
    conditions?: CustomActionCondition | CustomActionCondition[]
  ) {
    if (!conditions) return [];
    return Array.isArray(conditions) ? conditions : [conditions];
  }

  function isEmptyValue(value: any) {
    return value === null || typeof value === 'undefined' || value === '';
  }

  function matchCustomActionCondition(
    record: Recordable | undefined,
    condition: CustomActionCondition
  ) {
    const value = record?.[condition.field];
    const op = condition.op || 'eq';
    if (op === 'empty') return isEmptyValue(value);
    if (op === 'not_empty') return !isEmptyValue(value);
    if (op === 'truthy') return !!value;
    if (op === 'falsy') return !value;
    if (op === 'ne') return value !== condition.value;
    if (op === 'in') return Array.isArray(condition.value) && condition.value.includes(value);
    if (op === 'not_in') return Array.isArray(condition.value) && !condition.value.includes(value);
    return value === condition.value;
  }

  function isCustomActionVisible(action: CustomActionConfig, record?: Recordable) {
    const conditions = normalizeCustomActionConditions(action.show_if);
    return conditions.every((condition) => matchCustomActionCondition(record, condition));
  }

  function isCustomActionDisabled(action: CustomActionConfig, record?: Recordable) {
    const conditions = normalizeCustomActionConditions(action.disabled_if);
    return conditions.some((condition) => matchCustomActionCondition(record, condition));
  }

  async function runCustomAction(action: CustomActionConfig, record?: Recordable) {
    await executeCustomAction({
      action,
      appName: appName.value,
      modelName: modelName.value,
      record,
      selectedRowKeys: selectedRowKeys.value,
      selectedRows: Object.values(selectedRowMap.value),
      rows: tableData.value,
      filters: g_filters.value,
      sorter: g_sorter.value,
      pagination: {
        page: currentPage.value,
        pageSize: currentPageSize.value,
      },
      modelInfo: modelInfo.value,
      route: currentRoute,
      router,
      message,
      reload: reloadTable,
    });
  }

  function handleCustomAction(action: CustomActionConfig, record?: Recordable) {
    const confirm = action.confirm;
    if (!confirm) {
      return runCustomAction(action, record);
    }
    const confirmOptions = typeof confirm === 'object' ? confirm : {};
    window['$dialog'].warning({
      title: confirmOptions.title || '确认操作',
      content: confirmOptions.content || `确定要执行「${action.label}」吗？`,
      positiveText: '确定',
      negativeText: '取消',
      onPositiveClick: () => runCustomAction(action, record),
    });
  }

  function isScrollableElement(el: HTMLElement) {
    return el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth;
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

  function getTableScrollElements() {
    const root = listRootRef.value;
    if (!root) return [];
    return Array.from(
      new Set([
        ...Array.from(
          root.querySelectorAll<HTMLElement>(
            [
              '.n-data-table-base-table',
              '.n-data-table-base-table-header',
              '.n-data-table-base-table-body',
              '.n-scrollbar-container',
              '.n-scrollbar-content',
              '.v-vl',
              '.v-vl-items',
              '.n-data-table-table',
              '.n-data-table-wrapper',
            ].join(',')
          )
        ),
      ])
    );
  }

  function getTableAxisScrollElements() {
    const root = listRootRef.value;
    if (!root) {
      return {
        horizontal: null,
        vertical: null,
        horizontalAll: [],
        all: [],
      };
    }

    const scrollElements = getTableScrollElements().filter(isScrollableElement);
    const horizontalAll = scrollElements.filter(canScrollHorizontal);
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
      ) || horizontalAll[0];
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
      horizontalAll,
      all: scrollElements,
    };
  }

  function getPageScrollElement() {
    const root = listRootRef.value;
    const layoutScrollCandidates = Array.from(
      document.querySelectorAll<HTMLElement>('.layout-scroll-container .n-scrollbar-container')
    )
      .filter((el) => (!root || el.contains(root)) && isScrollableElement(el))
      .sort(
        (a, b) =>
          b.scrollHeight -
          b.clientHeight +
          (b.scrollWidth - b.clientWidth) -
          (a.scrollHeight - a.clientHeight + (a.scrollWidth - a.clientWidth))
      );
    if (layoutScrollCandidates[0]) {
      return layoutScrollCandidates[0];
    }

    let el = listRootRef.value?.parentElement || null;
    while (el) {
      if (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth) {
        return el;
      }
      el = el.parentElement;
    }
    return document.scrollingElement as HTMLElement | null;
  }

  function saveTableScrollPosition(force = false) {
    if (isTabClosed) return;
    if (pendingRestoreTableScroll.value && !force) return;

    const { horizontal, horizontalAll, vertical } = getTableAxisScrollElements();
    if (vertical) {
      tableVerticalScrollPosition.value = {
        top: Math.max(0, vertical.scrollTop),
      };
    }

    if (horizontal || horizontalAll.length) {
      const leftValues = (horizontalAll.length ? horizontalAll : [horizontal])
        .filter((el): el is HTMLElement => !!el)
        .map((el) => el.scrollLeft);
      tableHorizontalScrollPosition.value = {
        left: Math.max(0, ...leftValues),
      };
    }

    const pageScrollEl = getPageScrollElement();
    if (pageScrollEl) {
      pageScrollPosition.value = {
        top: pageScrollEl.scrollTop,
        left: pageScrollEl.scrollLeft,
      };
    }
    const previousTableY = getStoredScrollPosition('table-y');
    const nextTableYHasPosition = tableVerticalScrollPosition.value.top;
    const previousTableYHasPosition = previousTableY?.top;
    if (!previousTableYHasPosition || nextTableYHasPosition) {
      sessionStorage.setItem(
        getListScrollStorageKey('table-y'),
        JSON.stringify(tableVerticalScrollPosition.value)
      );
    }

    const previousTableX = getStoredScrollPosition('table-x');
    const nextTableXHasPosition = tableHorizontalScrollPosition.value.left;
    const previousTableXHasPosition = previousTableX?.left;
    if (!previousTableXHasPosition || nextTableXHasPosition) {
      sessionStorage.setItem(
        getListScrollStorageKey('table-x'),
        JSON.stringify(tableHorizontalScrollPosition.value)
      );
    }

    const previousPage = getStoredScrollPosition('list');
    const nextPageHasPosition = pageScrollPosition.value.top || pageScrollPosition.value.left;
    const previousPageHasPosition = previousPage?.top || previousPage?.left;
    if (!previousPageHasPosition || nextPageHasPosition) {
      sessionStorage.setItem(
        getListScrollStorageKey('list'),
        JSON.stringify(pageScrollPosition.value)
      );
    }
  }

  function loadTableScrollPosition() {
    const savedTableY = getStoredScrollPosition('table-y');
    const savedTableX = getStoredScrollPosition('table-x');
    const legacyTableRawValue = sessionStorage.getItem(
      `crud:${tabAppName}:${tabModelName}:table:scroll`
    );
    const savedPage = getStoredScrollPosition('list');
    let legacyTable: any = null;
    if (legacyTableRawValue) {
      try {
        legacyTable = JSON.parse(legacyTableRawValue);
      } catch {
        legacyTable = null;
      }
    }
    if (savedTableY || legacyTable?.top) {
      tableVerticalScrollPosition.value = {
        top: Math.max(0, Number(savedTableY?.top ?? legacyTable?.top ?? 0)),
      };
    }
    if (savedTableX || legacyTable?.left) {
      tableHorizontalScrollPosition.value = {
        left: Math.max(0, Number(savedTableX?.left ?? legacyTable?.left ?? 0)),
      };
    }
    if (savedPage) pageScrollPosition.value = savedPage;
  }

  function clearPendingTableScrollRestore() {
    tableRestoreToken++;
    if (finishRestoreTimer) {
      window.clearTimeout(finishRestoreTimer);
      finishRestoreTimer = null;
    }
    tableRestoreTimers.splice(0).forEach((timer) => window.clearTimeout(timer));
    tableRestoreRafIds.splice(0).forEach((rafId) => window.cancelAnimationFrame(rafId));
    pendingRestoreTableScroll.value = false;
    isApplyingTableScrollRestore = false;
  }

  async function bindTableScrollListeners() {
    removeTableScrollListeners?.();
    await nextTick();
    const scrollElements = getTableAxisScrollElements().all;
    scrollElements.forEach((el) => el.addEventListener('scroll', handleSavedTableScroll, true));
    removeTableScrollListeners = () => {
      scrollElements.forEach((el) =>
        el.removeEventListener('scroll', handleSavedTableScroll, true)
      );
      removeTableScrollListeners = null;
    };
  }

  async function restoreTableScrollPosition(restorePage = true, force = false) {
    if (pendingRestoreTableScroll.value && !force) return;
    clearPendingTableScrollRestore();
    loadTableScrollPosition();
    tableRestoreToken++;
    const restoreToken = tableRestoreToken;
    pendingRestoreTableScroll.value = true;
    await nextTick();
    const restore = () => {
      if (!pendingRestoreTableScroll.value || restoreToken !== tableRestoreToken) return;
      isApplyingTableScrollRestore = true;
      const pageScrollEl = restorePage ? getPageScrollElement() : null;
      if (pageScrollEl) {
        pageScrollEl.scrollTop = pageScrollPosition.value.top;
        pageScrollEl.scrollLeft = pageScrollPosition.value.left;
      }

      actionRef.value?.scrollTo?.({
        top: tableVerticalScrollPosition.value.top,
        left: tableHorizontalScrollPosition.value.left,
      });

      const { horizontal, horizontalAll, vertical } = getTableAxisScrollElements();
      if (vertical) {
        vertical.scrollTop = tableVerticalScrollPosition.value.top;
      }
      const horizontalTargets = horizontalAll.length
        ? horizontalAll
        : horizontal
        ? [horizontal]
        : [];
      horizontalTargets.forEach((el) => {
        el.scrollLeft = tableHorizontalScrollPosition.value.left;
      });
      if (horizontal && !horizontalTargets.includes(horizontal)) {
        horizontal.scrollLeft = tableHorizontalScrollPosition.value.left;
      }
      horizontalTargets.forEach((el) => el.dispatchEvent(new Event('scroll')));
      tableRestoreRafIds.push(
        window.requestAnimationFrame(() => {
          if (restoreToken === tableRestoreToken) {
            isApplyingTableScrollRestore = false;
          }
        })
      );
    };

    const scheduleRestore = (delay: number) => {
      tableRestoreTimers.push(window.setTimeout(restore, delay));
    };

    tableRestoreRafIds.push(
      window.requestAnimationFrame(() => {
        restore();
        tableRestoreRafIds.push(window.requestAnimationFrame(restore));
      })
    );
    [50, 120, 240, 480, 800].forEach(scheduleRestore);
    finishRestoreTimer = window.setTimeout(() => {
      if (restoreToken !== tableRestoreToken) return;
      pendingRestoreTableScroll.value = false;
      isApplyingTableScrollRestore = false;
      finishRestoreTimer = null;
      saveTableScrollPosition(true);
    }, 900);
  }

  async function handleTableFetchSuccess() {
    await bindTableScrollListeners();
    if (
      pendingRestoreTableScroll.value ||
      tableHorizontalScrollPosition.value.left ||
      tableVerticalScrollPosition.value.top
    ) {
      restoreTableScrollPosition(false, true);
    }
  }

  watch(
    () => currentRoute.fullPath,
    (newFullPath, oldFullPath) => {
      if (oldFullPath === tabFullPath && newFullPath !== oldFullPath) {
        clearPendingTableScrollRestore();
        saveTableScrollPosition(true);
      }
    },
    { flush: 'sync' }
  );

  watch(
    () => currentRoute.fullPath,
    async (newFullPath) => {
      if (newFullPath !== tabFullPath) return;
      await bindTableScrollListeners();
      await restoreTableScrollPosition();
    },
    { flush: 'post' }
  );

  // 计算是否有任何未保存的编辑
  const hasAnyUnsavedEdits = computed(() => {
    return Object.keys(inlineEdits.value).some((id) => {
      const edits = inlineEdits.value[id];
      return edits && Object.keys(edits).length > 0;
    });
  });

  // 计算未保存的编辑数量
  const unsavedEditsCount = computed(() => {
    return Object.keys(inlineEdits.value).filter(
      (id) => inlineEdits.value[id] && Object.keys(inlineEdits.value[id]).length > 0
    ).length;
  });

  const canShowActionColumn = computed(() => {
    return (
      canUpdateRows.value ||
      canDeleteRows.value ||
      hasAnyUnsavedEdits.value ||
      customRowActions.value.length > 0
    );
  });

  const actionColumn = computed(() => {
    if (!canShowActionColumn.value) return null;
    return {
      width: actionColumnWidth.value,
      minWidth: ACTION_COLUMN_MIN_WIDTH,
      maxWidth: ACTION_COLUMN_MAX_WIDTH,
      title: t('table.action'),
      key: 'action',
      fixed: 'right',
      align: 'center',
      render(record) {
        const actions: any[] = [];
        // Inline save button (shown when there are unsaved edits)
        if (hasInlineEdits(record[pk.value])) {
          actions.push({
            label: t('button.save'),
            icon: SaveOutlined,
            onClick: saveInlineEdit.bind(null, record),
            ifShow: () => true,
            type: 'success',
            size: 'tiny',
          });
        }
        if (canUpdateRows.value) {
          actions.push({
            label: t('button.edit'),
            icon: EditOutlined,
            onClick: handleEdit.bind(null, record),
            ifShow: () => true,
            type: 'warning',
            size: 'tiny',
          });
        }
        if (canDeleteRows.value) {
          actions.push({
            label: t('button.delete'),
            icon: DeleteOutlined,
            onClick: handleDelete.bind(null, record),
            ifShow: () => true,
            type: 'error',
            size: 'tiny',
            // auth: ['basic_list'],
          });
        }
        customRowActions.value
          .filter((action) => isCustomActionVisible(action, record))
          .forEach((action) => {
            const icon = resolveCustomActionIcon(action.icon);
            const actionItem: any = {
              label: getCustomActionLabel(action),
              onClick: handleCustomAction.bind(null, action, record),
              ifShow: () => true,
              type: action.type || 'default',
              size: 'tiny',
              disabled: isCustomActionDisabled(action, record),
            };
            if (icon) actionItem.icon = icon;
            actions.push(actionItem);
          });
        return h(TableAction as any, {
          style: 'button',
          actions,
        });
      },
    };
  });

  // 新建记录
  async function handleCreate() {
    console.log(modelInfo.value?.perms.includes(`${appName.value}:${modelName.value}:create`));
    console.log('handleCreate');
    router.push({
      name: CRUD_CREATE,
      params: {
        app_name: appName.value,
        model_name: modelName.value,
      },
      // query: {
      //   is_edit: 'false',
      // },
    });
  }

  async function handleEdit(record) {
    console.log('handleEdit');
    router.push({
      name: CRUD_EDIT,
      params: {
        app_name: appName.value,
        model_name: modelName.value,
        id: record.id,
      },
      // query: {
      //   is_edit: 'true',
      // },
      replace: true,
    });
    return;
  }

  function getRowKeyValue(row: Recordable) {
    return row?.[pk.value] ?? row?.id;
  }

  function syncSelectedRows(rowKeys: Array<string | number>) {
    const currentPageKeys = tableData.value.map(getRowKeyValue);
    const nextMap = { ...selectedRowMap.value };
    const nextKeys = new Set(selectedRowKeys.value);
    const checkedKeys = new Set(rowKeys);

    currentPageKeys.forEach((key) => {
      const mapKey = String(key);
      if (checkedKeys.has(key)) {
        const row = tableData.value.find((item) => getRowKeyValue(item) === key);
        if (row) {
          nextMap[mapKey] = row;
          nextKeys.add(key);
        }
      } else {
        delete nextMap[mapKey];
        nextKeys.delete(key);
      }
    });

    rowKeys.forEach((key) => {
      const row = tableData.value.find((item) => getRowKeyValue(item) === key);
      if (row) {
        nextMap[String(key)] = row;
      }
      nextKeys.add(key);
    });

    selectedRowMap.value = nextMap;
    selectedRowKeys.value = Array.from(nextKeys);
  }

  function onCheckedRow(rowKeys: Array<string | number>) {
    syncSelectedRows(rowKeys);
  }

  function handleRowSelectionChecked(checked: boolean) {
    if (!checked) {
      clearSelectedRows();
    }
  }

  function clearSelectedRows() {
    selectedRowKeys.value = [];
    selectedRowMap.value = {};
  }

  async function handleBatchDelete() {
    const keys = [...selectedRowKeys.value];
    if (!keys.length) return;

    window['$dialog'].warning({
      title: t('common.warning'),
      content: t('crud.deleteSelectedConfirm', { count: keys.length }),
      positiveText: t('common.confirm'),
      negativeText: t('common.cancel'),
      autoFocus: false,
      positiveButtonProps: {
        autofocus: true,
        udFocus: true,
      },
      onAfterEnter: () => {
        const btn = document.querySelector('button[udfocus="true"]') as HTMLElement;
        if (btn) {
          btn.focus();
        }
      },
      onPositiveClick: async () => {
        let successCount = 0;
        const errors: string[] = [];
        for (const key of keys) {
          try {
            await DeleteModelItem(appName.value, modelName.value, key);
            successCount += 1;
          } catch (error: any) {
            errors.push(`${key}: ${error.message || error}`);
          }
        }

        if (successCount > 0) {
          message.success(t('crud.deleteSuccess', { count: successCount }));
        }
        if (errors.length > 0) {
          message.error(
            t('crud.deleteFailed', { count: errors.length, errors: errors.join('; ') })
          );
        }

        clearSelectedRows();
        reloadTable();
      },
    });
  }

  async function reloadTable() {
    saveTableScrollPosition(true);
    // Sync current pagination state from table component
    syncPaginationFromTable();

    // 不再清空所有编辑状态，只清空当前页的数据
    // inlineEdits.value = {};
    // Update the table's internal pagination state
    actionRef.value?.setPagination({
      page: currentPage.value,
      pageSize: currentPageSize.value,
    });
    // Then reload with the same pagination
    await actionRef.value?.reload({
      page: currentPage.value,
      pageSize: currentPageSize.value,
    });
    await bindTableScrollListeners();
    restoreTableScrollPosition(false, true);
  }

  // Sync pagination state from table component to local refs
  function syncPaginationFromTable() {
    if (!actionRef.value) {
      return;
    }
    const tablePagination = actionRef.value.getPagination();
    if (tablePagination && typeof tablePagination === 'object') {
      currentPage.value = tablePagination.page || currentPage.value;
      currentPageSize.value = normalizePageSize(tablePagination.pageSize || currentPageSize.value);
    }
  }

  function persistPaginationState() {
    crudRefresh.setPaginationState(
      appName.value,
      modelName.value,
      currentPage.value,
      currentPageSize.value
    );
    storage.set(
      paginationStorageKey,
      {
        page: currentPage.value,
        pageSize: currentPageSize.value,
      },
      null
    );
  }

  // Inline editing helpers
  function onInlineEdit(rowId: string | number, fieldName: string, value: any, choices?: any) {
    const id = String(rowId);
    const record = tableData.value.find((row) => row[pk.value] == rowId);
    const originalValue =
      record && hasChoices(choices)
        ? normalizeChoiceValue(record[fieldName], choices)
        : record?.[fieldName];
    const nextValue = hasChoices(choices) ? normalizeChoiceValue(value, choices) : value;
    if (record && isEqual(originalValue, nextValue)) {
      if (inlineEdits.value[id]) {
        delete inlineEdits.value[id][fieldName];
        if (Object.keys(inlineEdits.value[id]).length === 0) {
          delete inlineEdits.value[id];
        }
      }
      return;
    }
    if (!inlineEdits.value[id]) {
      inlineEdits.value[id] = {};
    }
    inlineEdits.value[id][fieldName] = nextValue;
  }

  function hasInlineEdits(rowId: string | number): boolean {
    const id = String(rowId);
    const edits = inlineEdits.value[id];
    if (!edits) return false;
    return Object.keys(edits).length > 0;
  }

  function applyInlineChanges(rowId: string | number, changes: Record<string, any>) {
    const record = tableData.value.find((row) => row[pk.value] == rowId);
    if (record) {
      Object.assign(record, changes);
    }
  }

  async function saveInlineEdit(record: Recordable) {
    const id = String(record[pk.value]);
    const changes = { ...(inlineEdits.value[id] || {}) };
    if (!changes || Object.keys(changes).length === 0) {
      message.warning(t('crud.noChanges'));
      return;
    }
    try {
      await UpdateModelItem(appName.value, modelName.value, record[pk.value], changes);
      applyInlineChanges(id, changes);
      message.success(t('crud.saveSuccess'));
      // 只删除已保存行的编辑状态，不影响其他行
      delete inlineEdits.value[id];
    } catch (error: any) {
      delete inlineEdits.value[id];
      message.error(t('crud.saveFailed', { error: error.message || t('common.unknownError') }));
    }
  }

  // 保存所有未保存的编辑
  async function saveAllInlineEdits() {
    const unsavedIds = Object.keys(inlineEdits.value).filter((id) => {
      const edits = inlineEdits.value[id];
      return edits && Object.keys(edits).length > 0;
    });

    if (unsavedIds.length === 0) {
      message.warning(t('crud.noUnsavedChanges'));
      return;
    }

    let successCount = 0;
    let failCount = 0;
    const errors: string[] = [];

    for (const id of unsavedIds) {
      const changes = { ...(inlineEdits.value[id] || {}) };
      try {
        const record = tableData.value.find((row) => row[pk.value] == id);
        if (record) {
          await UpdateModelItem(appName.value, modelName.value, record[pk.value], changes);
          applyInlineChanges(id, changes);
          successCount++;
          delete inlineEdits.value[id];
        }
      } catch (error: any) {
        failCount++;
        delete inlineEdits.value[id];
        errors.push(`ID ${id}: ${error.message || t('common.unknownError')}`);
      }
    }

    if (successCount > 0) {
      message.success(t('crud.batchSaveSuccess', { count: successCount }));
    }
    if (failCount > 0) {
      message.error(t('crud.batchSaveFailed', { count: failCount, errors: errors.join('; ') }));
    }
  }

  // 重置所有修改
  async function resetAllEdits() {
    // 清空所有编辑状态
    inlineEdits.value = {};
    // 重新加载表格数据，恢复原始值
    await reloadTable();
    message.info(t('crud.resetChangesDone'));
  }

  function handleSorterChange(sorter: any) {
    // sorter: { columnKey, order: 'ascend'|'descend'|false }
    if (sorter && sorter.order) {
      g_sorter.value = sorter;
    } else {
      g_sorter.value = null;
    }
    reloadTable();
  }

  async function handleDelete(record) {
    try {
      window['$dialog'].warning({
        title: t('common.warning'),
        content: t('crud.deleteRecordConfirm'),
        positiveText: t('common.confirm'),
        negativeText: t('common.cancel'),
        autoFocus: false,
        positiveButtonProps: {
          autofocus: true,
          udFocus: true,
          // type: 'primary',
          onclick: (e) => {
            console.log(e);
          },
        },
        onAfterEnter: () => {
          const btn = document.querySelector('button[udfocus="true"]') as HTMLElement;
          if (btn) {
            btn.focus();
          }
        },
        onPositiveClick: async () => {
          await DeleteModelItem(appName.value, modelName.value, getRowKeyValue(record));
          window['$message'].success(t('crud.deleteDone'));
          const rowKey = getRowKeyValue(record);
          delete selectedRowMap.value[String(rowKey)];
          selectedRowKeys.value = selectedRowKeys.value.filter((key) => key !== rowKey);
          reloadTable();
        },
      });
    } catch (error: any) {
      window['$message'].error(
        t('crud.deleteError', { error: error.message || t('common.unknownError') })
      );
    }
  }

  onMounted(async () => {
    console.log(`@@@crud_list:${appName.value}:${modelName.value} onMounted`);
    window.addEventListener('tabs-card:before-switch', handleTabsCardBeforeSwitch);
    window.addEventListener('tabs-card:closed', handleTabsCardClosed);
    const { data: model_info_data } = await GetAllowModelInfo({
      model_name: `${appName.value}:${modelName.value}`,
    });
    console.log('@@@model_info', model_info_data);
    modelInfo.value = model_info_data;
    const { fields_info, ui } = modelInfo.value;

    const pkField = Object.values(fields_info).find((field: any) => field.is_pk) as Recordable;
    pk.value = pkField.field_name || '';
    editableFields.value = ui.editable_fields || [];

    // 加载搜索组件
    if (ui.search_fields.length > 0) {
      const search_fields: any = ui.search_fields.map((item: string) => {
        return fields_info[item];
      });
      const component: any = await SearchFieldComponent(search_fields);
      schemas.value.push(component);
    }
    // 加载过滤组件
    // for Each  处理异步会导致顺序不一致
    for (const item of ui.list_filter) {
      const field = fields_info[item];
      const filterComponentName = field?.filter_cmp;
      if (filterComponentName && filterComponentName in FilterFieldComponentMap) {
        const component = await FilterFieldComponentMap[filterComponentName](field);
        schemas.value.push(component);
      } else {
        console.log(`数据库类型 ${field.field_type} 不支持filter组件化。`);
      }
    }
    // 根据 display_fields 加载表格列配置
    const display_fields = (ui?.list_display || []).includes('*')
      ? Object.keys(fields_info)
      : ui?.list_display || [];
    columns.value = display_fields
      .map((field_name: string) => {
        const field = fields_info[field_name];
        // M2M/BackwardFK fields render as count column
        if (MANY_RELATION_FIELD_TYPES.has(field.field_type)) {
          return columnRenderMap[field.field_type](field);
        }
        if (field.source_field && !SINGLE_RELATION_FIELD_TYPES.has(field.field_type)) {
          console.log(
            `[${field.field_type}:${field.field_name}] FK field id need not to be rendered.`
          );
          return null;
        }
        // Check if this field is editable (double-click to edit, requires update permission)
        if (editableFields.value.includes(field_name)) {
          const canEdit =
            perms.value.includes(`${appName.value}:${modelName.value}:update`) ||
            userInfo.is_superuser;
          const baseCol =
            field.field_type in columnRenderMap
              ? columnRenderMap[field.field_type](field)
              : columnRenderMap.default(field);
          // Add edit indicator to column header
          const editableTitle = h('div', { style: 'display: flex; align-items: center;' }, [
            baseCol.title,
            canEdit
              ? h(
                  NIcon,
                  {
                    size: 14,
                    style: 'margin-left: 4px; color: #1890ff;',
                    title: t('crud.doubleClickEdit'),
                  },
                  {
                    default: () => h(EditOutlined),
                  }
                )
              : null,
          ]);
          return {
            ...baseCol,
            title: editableTitle,
            ellipsis: false,
            className: [baseCol.className, 'inline-edit-column'].filter(Boolean).join(' '),
            render: (row) => {
              // 检查是否有未保存的编辑值，如果有则显示编辑后的值
              const rowId = String(row[pk.value]);
              const editedValue = inlineEdits.value[rowId]?.[field_name];
              const displayValue = editedValue !== undefined ? editedValue : row[field_name];

              return h('div', { class: 'inline-edit-cell' }, [
                h(EditableCell, {
                  value: displayValue,
                  rowId: row[pk.value],
                  fieldName: field_name,
                  fieldType: field.field_type,
                  canEdit: canEdit,
                  choices: field.choices || null,
                  align: getFieldAlign(field),
                  onChange: (_rowId: any, _fieldName: string, val: any) => {
                    onInlineEdit(_rowId, _fieldName, val, field.choices || undefined);
                  },
                }),
              ]);
            },
          };
        }
        if (hasChoices(field.choices)) {
          const baseCol =
            field.field_type in columnRenderMap
              ? columnRenderMap[field.field_type](field)
              : columnRenderMap.default(field);
          return {
            ...baseCol,
            render: (row) => formatChoiceValue(row[field_name], field.choices),
          };
        }
        if (field.field_type in columnRenderMap) {
          return columnRenderMap[field.field_type](field);
        } else {
          return columnRenderMap.default(field);
        }
      })
      .filter((item) => item !== null);

    // After table is initialized, sync pagination state from table
    await nextTick();
    syncPaginationFromTable();
    await bindTableScrollListeners();
    restoreTableScrollPosition();
  });

  // 离开组件的钩子函数
  onUnmounted(() => {
    // console.log(`@@@crud_edit:${appName.value}:${modelName.value} onUnmounted`);
  });

  // 激活组件的钩子函数
  onActivated(() => {
    if (isFirstActivation.value) {
      // First activation: just reset the flag, let onMounted handle initialization
      isFirstActivation.value = false;
      bindTableScrollListeners();
      restoreTableScrollPosition();
      return;
    }

    if (crudRefresh.getRefreshFlag(appName.value, modelName.value)) {
      crudRefresh.clearRefreshFlag(appName.value, modelName.value);
      nextTick(async () => {
        await reloadTable();
        await bindTableScrollListeners();
      });
      return;
    }

    bindTableScrollListeners();
    restoreTableScrollPosition();
  });

  // 离开组件的钩子函数
  onDeactivated(() => {
    // Save current pagination state to store
    saveTableScrollPosition(true);
    removeTableScrollListeners?.();
    persistPaginationState();
  });

  onBeforeRouteLeave(() => {
    saveTableScrollPosition(true);
  });

  onUnmounted(() => {
    removeTableScrollListeners?.();
    window.removeEventListener('tabs-card:before-switch', handleTabsCardBeforeSwitch);
    window.removeEventListener('tabs-card:closed', handleTabsCardClosed);
  });
</script>

<style lang="less" scoped>
  .crud-list-wrapper {
    display: flex;
    flex-direction: column;
    height: calc(100dvh - 104px);
    max-height: calc(100dvh - 104px);
    min-height: 0;
    overflow: hidden;
  }

  .condition-card {
    margin-bottom: 10px;
    flex-shrink: 0;
    border: 1px solid var(--n-border-color);
    border-radius: 8px;
    background: var(--n-color);
    overflow: hidden;

    :deep(.n-card__content) {
      padding: 12px 16px 14px;
      background: var(--n-color);
      border-radius: 8px;
    }

    // Hide validation feedback area in search/filter forms
    :deep(.n-form-item-feedback-wrapper) {
      display: none;
    }

    // Form item spacing
    :deep(.n-form-item) {
      margin-bottom: 0;

      .n-form-item-label {
        padding-bottom: 4px;
        font-size: 12px;
        height: auto;
        line-height: 1.25;
        color: var(--n-text-color-2);
        font-weight: 500;
      }
    }

    :deep(.n-grid) {
      align-items: end;
    }

    :deep(.n-input),
    :deep(.n-input-number),
    :deep(.n-base-selection),
    :deep(.n-date-picker),
    :deep(.n-time-picker) {
      width: 100%;
    }

    :deep(.n-input__input-el),
    :deep(.n-base-selection-input),
    :deep(.n-input__placeholder),
    :deep(.n-base-selection-placeholder) {
      font-size: 12px;
    }

    :deep(.n-auto-complete .n-input__suffix) {
      margin-left: auto;
    }

    :deep(.n-auto-complete .n-base-clear) {
      margin-left: auto;
    }

    :deep(.form-action-gi) {
      align-items: end;
      min-height: 54px;
    }

    :deep(.form-action-space) {
      width: 100%;
      justify-content: flex-end !important;
      gap: 8px !important;
      flex-wrap: nowrap;
    }

    :deep(.form-action-space .n-button) {
      min-width: 58px;
      height: 28px;
      border-radius: 999px;
    }
  }

  .table-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;

    :deep(.n-card__content) {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      padding: 0 !important;
    }

    :deep(.table-toolbar) {
      flex-shrink: 0;
      padding-bottom: 10px;
    }

    :deep(.s-table) {
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    :deep(.n-data-table) {
      flex: 1;
      min-height: 0;
    }

    :deep(.n-data-table-base-table-body::-webkit-scrollbar) {
      width: 8px !important;
      height: 8px !important;
    }

    :deep(.n-scrollbar-rail--vertical) {
      width: 8px !important;
    }

    :deep(.n-scrollbar-rail--vertical .n-scrollbar-rail__scrollbar) {
      width: 8px !important;
    }

    :deep(.n-scrollbar-rail--horizontal) {
      height: 8px !important;
      border-radius: 999px;
    }

    :deep(.n-scrollbar-rail--horizontal .n-scrollbar-rail__scrollbar) {
      height: 8px !important;
      border-radius: 999px;
    }

    :deep(.inline-edit-cell) {
      display: block;
      width: 100%;
      min-width: 0;
      max-width: 100%;
      box-sizing: border-box;
    }

    :deep(.inline-edit-column),
    :deep(.inline-edit-column .n-data-table-td__ellipsis) {
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
      box-sizing: border-box;
    }

    :deep(.inline-edit-column .n-data-table-td__ellipsis) {
      display: block !important;
    }

    :deep(.inline-edit-editor-shell) {
      display: block;
      width: 100%;
      min-width: 0;
      max-width: 100%;
      box-sizing: border-box;
    }

    :deep(.inline-textarea-editor) {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      display: flex;
      box-sizing: border-box;
      text-align: left;
    }

    :deep(.inline-textarea-editor .n-input-wrapper),
    :deep(.inline-textarea-editor .n-input__textarea),
    :deep(.inline-textarea-editor textarea) {
      width: 100% !important;
      min-width: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box;
      text-align: left;
    }
  }

  // 添加模态框样式
  :deep(.custom-modal) {
    .n-modal {
      width: 600px;
    }

    .n-dialog__content {
      padding: 0;
      background-color: #fff;
    }
  }

  .modal-content {
    max-height: 60vh;
    overflow-y: auto;
    padding: 16px 24px;
  }
</style>
