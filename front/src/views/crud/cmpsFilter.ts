import { GetFieldDistinctValues } from '@/api/crud/models';
import { defineComponent, h, markRaw, nextTick, ref } from 'vue';
import { NTimePicker, NTooltip } from 'naive-ui';
import { debounce } from 'lodash-es';
import { getFieldUiName } from './tools';
import {
  EMPTY_STRING_FILTER_VALUE,
  isEmptyValueFilterOption,
  NULL_FILTER_LABEL,
  NULL_FILTER_VALUE,
  selectorFilterSymbols,
} from './filterData';
import { BOOLEAN_LIKE_FIELD_TYPES } from './types';
import { t } from '@/i18n';

export const FilterFieldComponentMap: Record<string, any> = {
  SelectFilter,
  DatetimeFilter,
  DateFilter,
  TimeFilter,
  JsonFilter,
};

const TimeRangeFilterComponent = markRaw(
  defineComponent({
    name: 'TimeRangeFilterComponent',
    props: {
      value: {
        type: Array,
        default: null,
      },
      startPlaceholder: {
        type: String,
        default: () => t('form.startTime'),
      },
      endPlaceholder: {
        type: String,
        default: () => t('form.endTime'),
      },
    },
    emits: ['update:value'],
    setup(props, { emit }) {
      const updateValue = (index: number, value: string | null) => {
        const nextValue = Array.isArray(props.value) ? [...props.value] : [null, null];
        nextValue[index] = value;
        emit('update:value', nextValue[0] || nextValue[1] ? nextValue : null);
      };

      return () =>
        h(
          'div',
          {
            style: {
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              width: '100%',
            },
          },
          [
            h(NTimePicker, {
              formattedValue: Array.isArray(props.value)
                ? (props.value[0] as string) || null
                : null,
              valueFormat: 'HH:mm:ss',
              format: 'HH:mm:ss',
              clearable: true,
              placeholder: props.startPlaceholder,
              style: { flex: 1, minWidth: '120px' },
              'onUpdate:formattedValue': (value: string | null) => updateValue(0, value),
            }),
            h('span', { style: { color: 'var(--n-text-color-3)' } }, '-'),
            h(NTimePicker, {
              formattedValue: Array.isArray(props.value)
                ? (props.value[1] as string) || null
                : null,
              valueFormat: 'HH:mm:ss',
              format: 'HH:mm:ss',
              clearable: true,
              placeholder: props.endPlaceholder,
              style: { flex: 1, minWidth: '120px' },
              'onUpdate:formattedValue': (value: string | null) => updateValue(1, value),
            }),
          ]
        );
    },
  })
);

const EMPTY_VALUE_FILTER_OPTIONS = [
  EMPTY_STRING_FILTER_VALUE,
  { label: NULL_FILTER_LABEL, value: NULL_FILTER_VALUE },
];

function getFilterFieldLabel(field: any) {
  return `${getFieldUiName(field)}\uff1a`;
}

function getOptionValue(option: any) {
  return typeof option === 'object' && option !== null ? option.value : option;
}

function appendUniqueOptions(options: any[], values: any[]) {
  const existingValues = new Set(options.map((option) => String(getOptionValue(option))));
  values.forEach((value) => {
    const optionValue =
      value === null ? NULL_FILTER_VALUE : value === '' ? EMPTY_STRING_FILTER_VALUE : String(value);
    if (existingValues.has(optionValue)) return;
    existingValues.add(optionValue);
    options.push(optionValue);
  });
}

const OverflowTooltipOption = defineComponent({
  name: 'OverflowTooltipOption',
  props: {
    text: {
      type: String,
      default: '',
    },
  },
  setup(props, { slots }) {
    const optionWrapEl = ref<HTMLElement | null>(null);
    const isOverflow = ref(false);
    const updateOverflow = async () => {
      await nextTick();
      requestAnimationFrame(() => {
        const el = optionWrapEl.value?.querySelector(
          '.n-base-select-option__content'
        ) as HTMLElement | null;
        if (!el) return;
        isOverflow.value = el.scrollWidth > el.clientWidth + 1;
      });
    };

    return () =>
      h(
        NTooltip,
        {
          trigger: 'hover',
          placement: 'right',
          disabled: !isOverflow.value,
        },
        {
          trigger: () =>
            h(
              'div',
              {
                ref: optionWrapEl,
                onVnodeMounted: updateOverflow,
                onVnodeUpdated: updateOverflow,
              },
              slots.default?.()
            ),
          default: () => props.text,
        }
      );
  },
});

export async function SelectFilter(field: any) {
  const loadingRef = ref(false);
  const focusedRef = ref(false);
  const optionsRef = ref<any[]>([...EMPTY_VALUE_FILTER_OPTIONS]);
  const totalPages = ref(0);
  const currentQuery = ref('');
  const selectedOptionValue = ref('');
  const isBooleanField = BOOLEAN_LIKE_FIELD_TYPES.has(field.field_type);
  let loadMoreObserver: IntersectionObserver | null = null;
  let optionScrollEl: HTMLElement | null = null;
  let removeOptionScrollListener: (() => void) | null = null;
  const params = {
    app_model_name: `${field.app_name}:${field.model_name}`,
    field_names: field.field_name,
    paginator: {
      curr_page: 1,
      page_size: 20,
      order_by: [],
      filters: [],
    },
  };

  const loadData = async () => {
    if (!focusedRef.value) return;
    if (isBooleanField) {
      optionsRef.value = [...EMPTY_VALUE_FILTER_OPTIONS, 'false', 'true'];
      totalPages.value = 1;
      return;
    }
    loadingRef.value = true;
    // console.log(params);
    try {
      const { data } = await GetFieldDistinctValues(params);
      totalPages.value = data.paginator.page_cnt;
      const values = data.values;
      appendUniqueOptions(optionsRef.value, values);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      loadingRef.value = false;
    }
  };

  // 创建防抖搜索函数
  const debouncedSearch = debounce((query: string) => {
    // 如果当前查询与新查询相同，则不进行任何操作
    if (currentQuery.value === query && query != '') return;
    currentQuery.value = query;
    params.paginator.filters = query
      ? ([{ field: field.field_name, symbol: 'icontains', value: query }] as any)
      : [];
    optionsRef.value = [...EMPTY_VALUE_FILTER_OPTIONS];
    params.paginator.curr_page = 1;
    loadData();
  }, 300);

  const findScrollParent = (el: Element | null): HTMLElement | null => {
    let current = el?.parentElement || null;
    while (current) {
      const { overflowY } = window.getComputedStyle(current);
      if (
        (overflowY === 'auto' || overflowY === 'scroll') &&
        current.scrollHeight > current.clientHeight
      ) {
        return current;
      }
      current = current.parentElement;
    }
    return null;
  };

  const loadNextPage = async () => {
    if (loadingRef.value || params.paginator.curr_page >= totalPages.value) return;
    const scrollEl = optionScrollEl;
    const scrollTop = scrollEl?.scrollTop || 0;
    params.paginator.curr_page += 1;
    await loadData();
    if (scrollEl) {
      requestAnimationFrame(() => {
        scrollEl.scrollTop = scrollTop;
      });
    }
  };

  const isNearScrollBottom = (el: HTMLElement) => {
    return el.scrollTop + el.clientHeight >= el.scrollHeight - 24;
  };

  const bindOptionScroll = (el: HTMLElement | null) => {
    if (!el || optionScrollEl === el) return;
    removeOptionScrollListener?.();
    optionScrollEl = el;
    const handleScroll = () => {
      if (isNearScrollBottom(el)) {
        loadNextPage();
      }
    };
    el.addEventListener('scroll', handleScroll, { passive: true });
    removeOptionScrollListener = () => {
      el.removeEventListener('scroll', handleScroll);
      removeOptionScrollListener = null;
    };
  };

  const observeLastOption = (el: Element | null) => {
    if (!el) return;
    const scrollParent = findScrollParent(el);
    bindOptionScroll(scrollParent);
    loadMoreObserver?.disconnect();
    loadMoreObserver = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry?.isIntersecting) {
          loadNextPage();
        }
      },
      {
        root: scrollParent,
        rootMargin: '0px 0px 32px 0px',
      }
    );
    loadMoreObserver.observe(el);
  };

  const renderOptionContent = (node, option) => {
    return h(
      OverflowTooltipOption,
      {
        text: String(option.label ?? option.value ?? ''),
      },
      {
        default: () => node,
      }
    );
  };

  return {
    field: field.field_name,
    component: 'NAutoComplete',
    label: getFilterFieldLabel(field),
    loading: loadingRef,
    componentProps: ({ formModel }) => ({
      placeholder: t('form.selectFieldPlaceholder', { field: getFieldUiName(field) }),
      options: optionsRef.value, // 设置选项
      clearable: true, // 用户清除输入的值
      showEmpty: true,
      getShow: () => true,
      renderOption: ({ node, option }) => {
        const optionNode = renderOptionContent(node, option);
        if (option.value !== getOptionValue(optionsRef.value[optionsRef.value.length - 1])) {
          return optionNode;
        }
        return h(
          'div',
          {
            onVnodeMounted: (vnode) => observeLastOption(vnode.el as Element),
            onVnodeUnmounted: () => {
              loadMoreObserver?.disconnect();
              removeOptionScrollListener?.();
              optionScrollEl = null;
            },
          },
          [optionNode]
        );
      },
      // keyboard: true, // 开启键盘操作
      // clearFilterAfterSelect: false,
      'onUpdate:value': (value: any) => {
        if (!value) {
          optionsRef.value = [...EMPTY_VALUE_FILTER_OPTIONS];
          params.paginator.curr_page = 1;
          params.paginator.filters = [];
          currentQuery.value = '';
          selectedOptionValue.value = '';
          selectorFilterSymbols.delete(field.field_name);
          loadData();
          return;
        }
        // 使用防抖搜索函数
        if (isEmptyValueFilterOption(value)) {
          selectorFilterSymbols.set(field.field_name, 'eq');
          return;
        }
        selectorFilterSymbols.set(
          field.field_name,
          selectedOptionValue.value === value ? 'eq' : 'icontains'
        );
        debouncedSearch(value);
      },
      onFocus: () => {
        if (!focusedRef.value) {
          // 如果是第一次聚焦，则加载第一页数据，并设置为已经聚焦过，不是第一次聚焦，通过滚动触发后续数据加载
          focusedRef.value = true;
          loadData();
          // } else if (currentQuery.value == '') {
          //   // 如果当前查询为空，则清空选项，并加载第一页数据，处理清空输入框的情况不保留上次查询结果
          //   optionsRef.value = [];
          // loadData();
        } else {
          return;
        }
      },
      onSelect: (value: string) => {
        selectedOptionValue.value = value;
        formModel[field.field_name] = value;
        selectorFilterSymbols.set(field.field_name, 'eq');
      },
      // onUpdated: (value: string) => {
      //   console.log(value);
      // },
    }),
  };
}

export function DatetimeFilter(field: any) {
  return {
    field: field.field_name,
    component: 'NDatePicker',
    label: getFilterFieldLabel(field),
    componentProps: {
      type: 'datetimerange',
      format: 'yyyy-MM-dd HH:mm:ss', // 控制前端显示格式
    },
  };
}

export function DateFilter(field: any) {
  return {
    field: field.field_name,
    component: 'NDatePicker',
    label: getFilterFieldLabel(field),
    componentProps: {
      type: 'daterange',
      format: 'yyyy-MM-dd', // 控制前端显示格式
    },
  };
}

export function TimeFilter(field: any) {
  return {
    field: field.field_name,
    component: TimeRangeFilterComponent,
    label: getFilterFieldLabel(field),
    componentProps: {
      startPlaceholder: t('form.startTime'),
      endPlaceholder: t('form.endTime'),
    },
  };
}

export function JsonFilter(field: any) {
  return {
    field: field.field_name,
    component: 'NInput',
    label: getFilterFieldLabel(field),
    componentProps: {
      placeholder: t('form.inputFieldPlaceholder', { field: getFieldUiName(field) }),
      title: t('form.inputFieldPlaceholder', { field: getFieldUiName(field) }),
    },
  };
}
