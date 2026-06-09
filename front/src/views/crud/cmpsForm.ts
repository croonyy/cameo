import { GetFieldDistinctValues } from '@/api/crud/models';
import { ref, markRaw, defineComponent, h } from 'vue';
import { NTimePicker, SelectOption } from 'naive-ui';
import { debounce } from 'lodash-es';
import M2m from '@/components/UdFormItem/M2m.vue';
import JsonEditor from '@/components/UdFormItem/JsonEditor.vue';
import { RelManage } from '@/api/crud/models';
import { buildChoiceOptions, getFieldUiName, hasChoices } from './tools';
import { t } from '@/i18n';

export const FormItemFieldComponentMap: Record<string, any> = {
  InputField,
  SelectField,
  NumberComponent,
  BooleanField,
  EnumField,
  CharField,
  DateField,
  DatetimeField,
  DecimalField,
  FloatField,
  IntField,
  JSONField,
  TextField,
  TimeField,
  UUIDField,
  RelationField,
  ForeignKeyField,
};

const TimePickerFieldComponent = markRaw(
  defineComponent({
    name: 'TimePickerFieldComponent',
    props: {
      value: {
        type: String,
        default: null,
      },
    },
    emits: ['update:value'],
    setup(props, { attrs, emit }) {
      return () =>
        h(NTimePicker, {
          ...attrs,
          formattedValue: props.value || null,
          'onUpdate:formattedValue': (value: string | null) => {
            emit('update:value', value);
          },
        });
    },
  })
);

async function SelectField(field: any) {
  const loadingRef = ref(false);
  const focusedRef = ref(false);
  const optionsRef = ref<SelectOption[]>([]);
  const totalPages = ref(0);
  const currentQuery = ref('');
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
    loadingRef.value = true;
    try {
      const { data } = await GetFieldDistinctValues(params);
      totalPages.value = data.paginator.page_cnt;
      const newOptions = data.values.map((value: any) => {
        // 处理布尔类型 将布尔值转换为字符串
        if (typeof value === 'boolean') {
          return { label: value ? t('common.yes') : t('common.no'), value: String(value) };
        }
        // 处理其他类型统一转换为字符串
        return { label: value, value: value };
      });
      optionsRef.value.push(...newOptions);
      console.log(
        [
          `${field.field_name.padEnd(15, '-')}`,
          `${String(data.paginator.total).padStart(10, '-')}条`,
          `${String(totalPages.value).padStart(4, '-')}页，`,
          `每页${String(params.paginator.page_size).padStart(4, '-')}条，`,
          `加载第${String(params.paginator.curr_page).padStart(8, '-')}页，`,
        ].join('')
      );
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
    optionsRef.value = [];
    params.paginator.curr_page = 1;
    loadData();
  }, 300);

  const debouncedScroll = debounce(async (e) => {
    const target = e.target as HTMLElement;
    const { scrollTop, scrollHeight, clientHeight } = target;
    const oldScrollTop = scrollTop; // 保存当前滚动位置

    const buffer = 5;
    if (scrollTop + clientHeight + buffer >= scrollHeight) {
      if (params.paginator.curr_page < totalPages.value && !loadingRef.value) {
        params.paginator.curr_page += 1;
        // await loadData(false);
        await loadData();
        // 在数据加载完成后恢复滚动位置
        requestAnimationFrame(() => {
          target.scrollTop = oldScrollTop;
        });
      }
    }
  }, 300);
  return {
    field,
    component: 'NSelect',
    loading: loadingRef,
    componentProps: {
      placeholder: t('form.selectFieldPlaceholder', { field: getFieldUiName(field) }),
      filterable: true, // 开启搜索功能
      remote: true, // 开启远程搜索
      tag: true, // 是否可以创建新的选项，需要和 filterable 一起使用
      options: optionsRef, // 设置选项
      loading: loadingRef, // 设置加载状态
      clearable: true, // 用户清除输入的内容
      // keyboard: true, // 开启键盘操作
      // clearFilterAfterSelect: false,
      showOnFocus: true,
      style: { ...{ maxWidth: '320px' }, ...field['style'] },
      // 使用防抖搜索函数
      onSearch: debouncedSearch,
      onScroll: debouncedScroll,
      onFocus: () => {
        if (!focusedRef.value) {
          // 如果是第一次聚焦，则加载第一页数据，并设置为已经聚焦过，不是第一次聚焦，通过滚动触发后续数据加载
          focusedRef.value = true;
          loadData();
        } else {
          return;
        }
      },
      onClear: () => {
        optionsRef.value = [];
        params.paginator.curr_page = 1;
        params.paginator.filters = [];
        currentQuery.value = '';
        loadData();
      },
    },
  };
}
export function EnumField(field: any) {
  const options = buildChoiceOptions(field.choices);
  return {
    field,
    component: 'NSelect',
    componentProps: {
      options: options,
      placeholder: t('form.selectFieldPlaceholder', { field: getFieldUiName(field) }),
      filterable: true,
      clearable: true,
      style: { ...{ maxWidth: '320px' }, ...field['style'] },
    },
  };
}

export function IntField(field: any) {
  if (hasChoices(field.choices)) {
    return EnumField(field);
  }
  return {
    field,
    component: 'NInputNumber',
    componentProps: {
      precision: 0, // 不允许小数
      step: 1, // 步长为1
      style: { ...{ width: '320px' }, ...field['style'] },
    },
  };
}

export function BooleanField(field: any) {
  return {
    field,
    component: 'NSwitch',
    componentProps: {
      style: { ...field['style'] },
      defaultValue: false,
      default: false,
      // value: false,
    },
  };
}

export function TextField(field: any) {
  return {
    field,
    component: 'NInput',
    componentProps: {
      type: 'textarea',
      style: { ...{ maxWidth: '600px' }, ...field['style'] },
    },
  };
}

export function UUIDField(field: any) {
  return {
    field,
    component: 'NInput',
    componentProps: {
      type: 'text',
      style: { ...{ maxWidth: '320px' }, ...field['style'] },
    },
  };
}

export function CharField(field: any) {
  if (hasChoices(field.choices)) {
    return EnumField(field);
  }
  return {
    field,
    component: 'NInput',
    componentProps: {
      type: 'text',
      style: { ...{ maxWidth: '320px' }, ...field['style'] },
    },
  };
}

export function InputField(field: any) {
  if (hasChoices(field.choices)) {
    return EnumField(field);
  }
  return {
    field,
    component: 'NInput',
    componentProps: {
      type: 'text',
      placeholder: t('form.inputFieldPlaceholder', { field: getFieldUiName(field) }),
      clearable: true,
      style: { ...{ maxWidth: '320px' }, ...field['style'] },
    },
  };
}

export function JSONField(field: any) {
  return {
    field,
    component: markRaw(JsonEditor),
    componentProps: {
      width: '600px',
      height: '400px',
    },
  };
}

export function DecimalField(field: any) {
  return {
    field,
    component: 'NInputNumber',
    componentProps: {
      style: { ...{ maxWidth: '320px' }, ...field['style'] },
      showButton: false,
      precision: field.decimal_places, // 小数位数
    },
  };
}

export function FloatField(field: any) {
  return {
    field,
    component: 'NInputNumber',
    componentProps: {
      style: { ...{ maxWidth: '320px' }, ...field['style'] },
      required: true,
      showButton: false,
      min: 0.000001, // 设置最小值为一个接近0的正数
      precision: 6, // 设置精度为6位小数
    },
    rules: [
      {
        required: true,
        message: t('form.inputFieldPlaceholder', { field: getFieldUiName(field) }),
        // trigger: ['blur', 'input'],
      },
      {
        type: 'number',
        min: 0.000001,
        message: t('form.positiveNumber'),
        // trigger: ['blur', 'input'],
      },
    ],
  };
}

export function DatetimeField(field: any) {
  return {
    field,
    component: 'NDatePicker',
    componentProps: {
      type: 'datetime',
      style: { ...{ width: '220px' }, ...field['style'] },
      // style: { maxWidth: '320px' }, //maxWidth 无效
      format: 'yyyy-MM-dd HH:mm:ss', // 控制前端显示格式
      // valueFormat: 'yyyy-MM-dd HH:mm:ss', // 控制值的格式
      clearable: true,
      // isDateDisabled: (timestamp: number) => {
      //   return timestamp > Date.now();
      // },
    },
    // rules: [
    //   {
    //     required: field.required || false,
    //     message: `请选择${field.ui_name || field.field_name}`,
    //     trigger: ['blur', 'change'],
    //   },
    // ],
  };
}

export function DateField(field: any) {
  return {
    field,
    component: 'NDatePicker',
    componentProps: {
      style: { ...{ maxWidth: '400px' }, ...field['style'] },
      type: 'date',
      // format: 'yyyy-MM-dd', // 控制前端显示格式
      valueFormat: 'yyyy-MM-dd', // 控制值的格式
      clearable: true,
    },
    // rules: [
    //   {
    //     required: field.required || false,
    //     message: `请选择${field.ui_name || field.field_name}`,
    //     trigger: ['blur', 'change'],
    //   },
    // ],
  };
}

export function TimeField(field: any) {
  return {
    field,
    component: TimePickerFieldComponent,
    componentProps: {
      valueFormat: 'HH:mm:ss',
      format: 'HH:mm:ss',
      clearable: true,
      style: { ...{ width: '160px' }, ...field['style'] },
    },
  };
}

export function NumberComponent(field: any) {
  if (hasChoices(field.choices)) {
    return EnumField(field);
  }
  return {
    field,
    component: 'NInputNumber',
    componentProps: {
      style: { ...{ maxWidth: '320px' }, ...field['style'] },
    },
  };
}

// function ManyToManyFieldGenerator(field: any) {
//   function createOptions() {
//     return Array.from({ length: 5 }).map((_, i) => ({
//       label: `Option ${i}`,
//       value: i,
//     }));
//   }
//   const tvalue = ref<Recordable[]>([]);

//   return {
//     field,
//     component: 'NTransfer',
//     componentProps: {
//       style: field['style'] || {
//         width: '800px',
//       },
//       value: tvalue,
//       'onUpdate:value': (newValue: Recordable[]) => {
//         tvalue.value = newValue;
//       },
//       options: createOptions(),
//       sourceFilterable: true,
//       targetFilterable: true,
//       // filter: (value: any, filter: any, from: any) => {
//       //   console.log(value, filter, from);
//       //   return true;
//       // },
//     },
//   };
// }

export async function RelationField(
  field: any,
  id: number,
  relation_search: Array<string>,
  saveCount
) {
  return {
    field,
    component: markRaw(M2m),
    componentProps: {
      field,
      id,
      relationSearch: relation_search,
      saveCount,
      fieldType: field.field_type,
    },
  };
}

// export async function ForeignKeyField(field: any, id: number) {
//   // const selectedValue = ref<string | number | null>(null); // 用于存储选中的值
//   // const loadingRef = ref(false);
//   // // const optionsRef = ref<SelectOption[]>([]);
//   // const optionsRef = ref<SelectOption[]>([{ label: 'aaa', value: 3 }]);

//   return {
//     field,
//     component: markRaw(ForeignKey),
//     // loading: loadingRef,
//     componentProps: {
//       field,
//       id,
//     },
//   };
// }

export async function ForeignKeyField(field: any, id: string, relation_search: Array<string>) {
  const loadingRef = ref(false);
  const focusedRef = ref(false);
  const searchStr = ref('');
  // const optionsRef = ref<SelectOption[]>([]);
  const optionsRef = ref<SelectOption[]>([]);
  const totalPages = ref(0);
  const params = ref(<Recordable>{});

  params.value = {
    action: 'list',
    label: true,
    field_name: field.field_name,
    id: id,
    paginator: {
      curr_page: 1,
      page_size: 10,
      order_by: [],
      filters: [] as FilterGroup | [],
    },
  };
  // 初始化组选项
  if (id) {
    params.value.action = 'list';
    params.value.id = id;
    const { data: default_option } = await RelManage(
      field.app_name,
      field.model_name,
      params.value
    );
    optionsRef.value =
      default_option.map((item: any) => ({
        label: item.label,
        value: item.value.id,
      })) || [];
  }
  // 创建防抖搜索函数
  const debouncedSearch = debounce(async (query: string) => {
    console.log('onSearch', query);
    const querys: FilterGroup = [
      'or',
      ...relation_search.map((item) => ({
        field: item,
        symbol: 'icontains',
        value: query,
      })),
    ];
    params.value.action = 'query';
    // @ts-ignore
    params.value.paginator.filters = querys;
    params.value.paginator.curr_page = 1;
    loadingRef.value = true;
    const { data, extra } = await RelManage(field.app_name, field.model_name, params.value);
    optionsRef.value = data.map((item: any) => ({ label: item.label, value: item.value.id }));
    totalPages.value = extra.paginator.page_cnt;
    loadingRef.value = false;
  }, 300);
  if (!id) {
    debouncedSearch(''); // 新建页默认加载候选项；编辑页已有当前值时避免重复请求
  }

  // 创建防滚动函数
  const debouncedScroll = debounce(async (e: any) => {
    const target = e.target as HTMLElement;
    const { scrollTop, scrollHeight, clientHeight } = target;
    const oldScrollTop = scrollTop; // 保存当前滚动位置

    const buffer = 5;
    if (scrollTop + clientHeight + buffer >= scrollHeight) {
      console.log('加载更多数据');
      if (params.value.paginator.curr_page < totalPages.value && !loadingRef.value) {
        params.value.paginator.curr_page += 1;
        loadingRef.value = true;
        const { data, extra } = await RelManage(field.app_name, field.model_name, params.value);
        // optionsRef.value = [
        //   ...optionsRef.value,
        //   ...data.map((item: any) => ({ label: item.label, value: item.value.id })),
        // ];
        const addOptions = data.map((item: any) => ({ label: item.label, value: item.value.id }));
        optionsRef.value.push(...addOptions);
        totalPages.value = extra.paginator.page_cnt;
        loadingRef.value = false;
        // 在数据加载完成后恢复滚动位置
        requestAnimationFrame(() => {
          target.scrollTop = oldScrollTop;
        });
      }
    }
  }, 300);

  return {
    field,
    component: 'NSelect',
    loading: loadingRef,
    componentProps: {
      // value: selectedValue,
      placeholder: t('form.selectFieldPlaceholder', { field: getFieldUiName(field) }),
      filterable: true, // 开启搜索功能
      remote: true, // 开启远程搜索
      tag: true, // 是否可以创建新的选项，需要和 filterable 一起使用
      options: optionsRef, // 设置选项
      loading: loadingRef, // 设置加载状态
      clearable: true, // 用户清除输入的内容
      // keyboard: true, // 开启键盘操作
      // clearFilterAfterSelect: false,
      showOnFocus: true,
      style: field['style'] || {
        width: '320px',
      },
      onFocus: async () => {
        if (!focusedRef.value) {
          focusedRef.value = true;
          debouncedSearch(searchStr.value);
        }
      },
      onSearch: (query: string) => {
        // 使用防抖搜索函数
        searchStr.value = query;
        debouncedSearch(query);
      },
      onScroll: debouncedScroll,
    },
  };
}
