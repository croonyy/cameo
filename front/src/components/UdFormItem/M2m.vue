<template>
  <div class="transfer-list-container" :value="[...addList, ...delList]">
    <div class="list-box">
      <div class="title">{{ leftTitle }}
        <n-popover trigger="hover" placement="right-end">
          <template #trigger>
            <span class="help help-tooltip help-icon">
              <QuestionCircleFilled style="display: inline; height: 16px" />
            </span>
          </template>
          {{ leftHelp }}
        </n-popover>
        <n-button v-if="relatedApp && relatedModel" size="tiny" type="primary" quaternary
          style="margin-left: auto; margin-right: 2px" @click="handleCreateRelated">
          <template #icon>
            <n-icon size="14">
              <PlusOutlined />
            </n-icon>
          </template>
          {{ t('button.create') }}
        </n-button>
      </div>
      <div class="list-header">
        <n-input v-model:value="leftSearch" :placeholder="t('transfer.searchPlaceholder')" clearable @update:value="debouncedLeftSearch" />
      </div>
      <div class="list-content">
        <!-- <n-scrollbar @scroll="handleLeftScroll"> -->
        <n-scrollbar @scroll="debouncedLeLeftScroll">
          <n-spin :show="leftLoading">
            <!-- 当filteredLeftList为空的时候显示一个没有数据的图标 -->
            <!-- <div v-if="filteredLeftList.length === 0" class="no-data">暂无数据</div> -->
            <div v-if="filteredLeftList.length === 0" class="no-data">
              <n-flex vertical align="center" justify="center" style="height: 200px">
                <n-icon size="48">
                  <DropboxOutlined />
                </n-icon>
                <span style="margin-top: 8px">{{ t('common.noData') }}</span>
              </n-flex>
            </div>
            <div v-for="item in filteredLeftList" :key="item.value" class="list-item">
              <option value="{{ item.value }}" :title="item.label" @click="addItem(item)">
                {{ item.label }}
              </option>
              <!-- <span @click="addItem(item)">{{ item.label }}</span> -->
            </div>
          </n-spin>
        </n-scrollbar>
      </div>
    </div>
    <div class="list-box">
      <div class="title">{{ rightTitle }}
        <n-popover trigger="hover" placement="right-end">
          <template #trigger>
            <span class="help help-tooltip help-icon">
              <QuestionCircleFilled style="display: inline; height: 16px" />
            </span>
          </template>
          {{ rightHelp }}
        </n-popover>
      </div>
      <div class="list-header">
        <n-input v-model:value="rightSearch" :placeholder="t('transfer.searchPlaceholder')" clearable @update:value="debouncedRightSearch" />
      </div>
      <div class="list-content">
        <n-scrollbar @scroll="debouncedLeRightScroll">
          <n-spin :show="rightLoading">
            <div v-if="filteredRightList.length === 0" class="no-data">
              <n-flex vertical align="center" justify="center" style="height: 200px">
                <n-icon size="48">
                  <DropboxOutlined />
                </n-icon>
                <span style="margin-top: 8px">{{ t('common.noData') }}</span>
              </n-flex>
            </div>
            <div v-for="item in filteredRightList" :key="item.value" class="list-item">
              <span @click="delItem(item)">{{ item.label }}</span>
            </div>
          </n-spin>
        </n-scrollbar>
      </div>
    </div>
    <div class="list-box">
      <div class="title">
        {{ midTitle }}
        <n-popover trigger="hover" placement="right-end">
          <template #trigger>
            <span class="help help-tooltip help-icon">
              <QuestionCircleFilled style="display: inline; height: 16px" />
            </span>
          </template>
          {{ midHelp }}
        </n-popover>
      </div>
      <div class="list-content">
        <n-scrollbar>
          <div v-for="item in [...addList, ...delList]" :key="item.value" class="list-item" :style="{
            backgroundColor: item.isDel
              ? themeVarsComputed.errorColor
              : themeVarsComputed.successColor,
          }">
            <!-- :style="{ backgroundColor: item.isDel ? '#f4b4b4' : '#b4f4b4' }" -->
            <!-- <n-checkbox :value="item.value" :label="item.label" @click="test" /> -->
            <span @click="clearItem(item)">{{ item.label }}</span>
          </div>
        </n-scrollbar>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watchEffect, onMounted, toRaw, watch } from 'vue';
import { QuestionCircleFilled, PlusOutlined } from '@vicons/antd';
import { debounce } from 'lodash-es';
import { useMessage, useThemeVars } from 'naive-ui';
import { RelManage } from '@/api/crud/models';
import { DropboxOutlined } from '@vicons/antd';
import { useRouter } from 'vue-router';
import { CRUD_CREATE } from '@/store/consts';
import { t } from '@/i18n';

const message = useMessage();

const props = withDefaults(
  defineProps<{
    // value: ModelValue;
    field: Recordable;
    id?: string;
    relationSearch: Array<string>;
    saveCount;
    fieldType?: string;
  }>(),
  {
    fieldType: 'ManyToManyField',
  }
);

const isBackwardFK = computed(() => props.fieldType === 'BackwardFKRelation');
const leftTitle = computed(() =>
  isBackwardFK.value ? t('transfer.optionalRecords') : t('transfer.optionalRelations')
);
const rightTitle = computed(() =>
  isBackwardFK.value ? t('transfer.existingRecords') : t('transfer.existingRelations')
);
const midTitle = computed(() =>
  isBackwardFK.value ? t('transfer.pendingRecords') : t('transfer.pendingRelations')
);
const leftHelp = computed(() =>
  isBackwardFK.value ? t('transfer.leftRecordHelp') : t('transfer.leftRelationHelp')
);
const rightHelp = computed(() =>
  isBackwardFK.value ? t('transfer.rightRecordHelp') : t('transfer.rightRelationHelp')
);
const midHelp = computed(() =>
  isBackwardFK.value ? t('transfer.midRecordHelp') : t('transfer.midRelationHelp')
);

const emit = defineEmits<{
  (e: 'update:value', value: ModelValue): void;
}>();

const leftList = ref<TransferItem[]>([]);
const rightList = ref<TransferItem[]>([]);
const leftSearch = ref('');
const rightSearch = ref('');
const leftLoading = ref(false);
const rightLoading = ref(false);
const paramsLeft = ref(getFetchManageParams('list'));
const paramsRight = ref(getFetchManageParams('query'));
const leftPaginator = ref<Record<string, any>>({});
const rightPaginator = ref<Record<string, any>>({});
const relatedApp = ref('');
const relatedModel = ref('');
const addList = ref<TransferItem[]>([]);
const delList = ref<TransferItem[]>([]);
const relationSearch: Array<string> =
  props.relationSearch.length > 0 ? props.relationSearch : ['id'];

const router = useRouter();
function handleCreateRelated() {
  router.push({
    name: CRUD_CREATE,
    params: {
      app_name: relatedApp.value,
      model_name: relatedModel.value,
    },
  });
}

const themeVars = useThemeVars();
const themeVarsComputed = computed(() => themeVars.value);
function getPageSize() {
  const pageSize = Number(props.field?.info?.ui_page_size);
  return Number.isInteger(pageSize) && pageSize > 0 ? pageSize : 20;
}

function getFetchManageParams(action: string): FatchManageParams {
  return {
    action,
    field_name: props.field.field_name,
    label: true,
    id: props.id,
    paginator: {
      curr_page: 1,
      page_size: getPageSize(),
      order_by: [],
      filters: [],
    },
    m2m_ids: {},
  };
}

function logPageLoad(side: string, paginator: Record<string, any>) {
  console.log(
    [
      `[M2m:${props.field.field_name}:${side}] `,
      `共${String(paginator.total ?? 0)} 条，`,
      `每页 ${String(paginator.page_size ?? getPageSize())} 条，`,
      `加载第${String(paginator.curr_page ?? 1)} / ${String(paginator.page_cnt ?? 1)} 页`,
    ].join('')
  );
}

function clearItem(item: any) {
  console.log('clearItem', item);
  if (item.isDel) {
    delList.value = delList.value.filter((i) => i.value !== item.value);
  } else {
    addList.value = addList.value.filter((i) => i.value !== item.value);
  }
}

function addItem(item: any) {
  console.log('addItem', item);
  if (addList.value.filter((i) => i.value == item.value).length == 0) {
    addList.value.push({ ...item, isDel: false });
  } else {
    message.info(t('common.selected'), {});
  }
}
function delItem(item: any) {
  console.log('delItem', item);
  if (delList.value.filter((i) => i.value == item.value).length == 0) {
    delList.value.push({ ...item, isDel: true });
  } else {
    message.info(t('common.selected'));
  }
}

watchEffect(() => {
  const newValue = {
    add: toRaw(addList.value),
    del: toRaw(delList.value),
  };
  emit('update:value', newValue);
});

function getFieldSaveCount() {
  const saveCountSource = props.saveCount as any;
  const saveCountValue = saveCountSource?.value ?? saveCountSource ?? {};
  return Number(saveCountValue?.[props.field.field_name] || 0);
}

watch(getFieldSaveCount, async (newVal) => {
  console.log(`[M2m:${props.field.field_name}] saveCount`, newVal);
  if (newVal) {
    // 保存之后 更新数据,并清空tmp�?
    await reloadRightData();
  }
});

const reloadRightData = debounce(async () => {
  await fetchRightData();
  addList.value = [];
  delList.value = [];
}, 300);

async function fetchLeftData() {
  const { data, extra } = await RelManage(
    props.field.app_name,
    props.field.model_name,
    paramsLeft.value
  );
  const results = data.map((item: any) => ({ label: item.label, value: item.value.id }));
  // const results = await props.onLeftSearch(value);
  leftList.value = results;
  leftPaginator.value = extra.paginator;
  logPageLoad('left', extra.paginator);
  // Store related model info for the create button
  if (extra.related_model) relatedModel.value = extra.related_model;
  if (extra.app_name) relatedApp.value = extra.app_name;
}
async function fetchRightData() {
  const { data, extra } = await RelManage(
    props.field.app_name,
    props.field.model_name,
    paramsRight.value
  );
  const results = data.map((item: any) => ({ label: item.label, value: item.value.id }));
  // const results = await props.onLeftSearch(value);
  rightList.value = results;
  rightPaginator.value = extra.paginator;
  logPageLoad('right', extra.paginator);
  // Store related model info for the create button
  if (extra.related_model) relatedModel.value = extra.related_model;
  if (extra.app_name) relatedApp.value = extra.app_name;
}

// 搜索处理函数
const handleLeftSearch = async (value: string) => {
  leftLoading.value = true;
  try {
    const querys: FilterGroup = [
      'or',
      ...relationSearch.map((item) => ({
        field: item,
        symbol: 'icontains',
        value,
      })),
    ];
    paramsLeft.value.field_name = props.field.field_name;
    paramsLeft.value.action = 'query';
    paramsLeft.value.paginator.curr_page = 1;
    paramsLeft.value.paginator.filters = querys;
    await fetchLeftData();
  } catch (error) {
    console.error('左侧搜索失败:', error);
  } finally {
    leftLoading.value = false;
  }
};

const handleRightSearch = async (value: string) => {
  console.log('handleRightSearch', Boolean(props.id));
  // 没有id的情况下直接返回
  if (!Boolean(props.id)) {
    return;
  }
  rightLoading.value = true;
  try {
    const querys: FilterGroup = [
      'or',
      ...relationSearch.map((item) => ({
        field: item,
        symbol: 'icontains',
        value,
      })),
    ];
    paramsRight.value.field_name = props.field.field_name;
    paramsRight.value.action = 'list';
    paramsRight.value.paginator.curr_page = 1;
    paramsRight.value.paginator.filters = querys;
    await fetchRightData();
  } catch (error) {
    console.error('右侧搜索失败:', error);
  } finally {
    rightLoading.value = false;
  }
};

// 处理滚动事件
const handleLeftScroll = async (e: Event) => {
  const target = e.target as HTMLElement;
  const { scrollTop, scrollHeight, clientHeight } = target;
  const oldScrollTop = scrollTop; // 保存当前滚动位置
  const buffer = 5;
  if (scrollTop + clientHeight + buffer >= scrollHeight) {
    if (leftPaginator.value.curr_page < leftPaginator.value.page_cnt && !leftLoading.value) {
      leftLoading.value = true;
      try {
        paramsLeft.value.paginator.curr_page += 1;
        const { data, extra } = await RelManage(
          props.field.app_name,
          props.field.model_name,
          paramsLeft.value
        );
        const results = data.map((item: any) => ({ label: item.label, value: item.value.id }));
        leftList.value.push(...results);
        leftPaginator.value = extra.paginator;
        logPageLoad('left-scroll', extra.paginator);
        requestAnimationFrame(() => {
          target.scrollTop = oldScrollTop;
        });
        leftLoading.value = false;
      } catch (error) {
        console.error('加载更多失败:', error);
        leftLoading.value = false;
      }
    }
  }
};
const handleRightScroll = async (e: Event) => {
  const target = e.target as HTMLElement;
  const { scrollTop, scrollHeight, clientHeight } = target;
  const oldScrollTop = scrollTop; // 保存当前滚动位置
  const buffer = 5;
  if (scrollTop + clientHeight + buffer >= scrollHeight) {
    if (rightPaginator.value.curr_page < rightPaginator.value.page_cnt && !rightLoading.value) {
      rightLoading.value = true;
      try {
        paramsRight.value.paginator.curr_page += 1;
        const { data, extra } = await RelManage(
          props.field.app_name,
          props.field.model_name,
          paramsRight.value
        );
        const results = data.map((item: any) => ({ label: item.label, value: item.value.id }));
        rightList.value.push(...results);
        rightPaginator.value = extra.paginator;
        logPageLoad('right-scroll', extra.paginator);
        requestAnimationFrame(() => {
          target.scrollTop = oldScrollTop;
        });
        rightLoading.value = false;
      } catch (error) {
        console.error('加载更多失败:', error);
        rightLoading.value = false;
      }
    }
  }
};

// 防抖处理搜索
const debouncedLeftSearch = debounce(handleLeftSearch, 300);
const debouncedRightSearch = debounce(handleRightSearch, 300);
const debouncedLeLeftScroll = debounce(handleLeftScroll, 300);
const debouncedLeRightScroll = debounce(handleRightScroll, 300);

// 过滤后的列表（现在主要用于本地过滤）
const filteredLeftList = computed(() => {
  return leftList.value;
});

const filteredRightList = computed(() => {
  return rightList.value;
});

onMounted(() => {
  debouncedLeftSearch('');
  debouncedRightSearch('');
});
</script>

<style scoped>
.transfer-list-container {
  width: 100%;
  max-width: 1000px;
  display: flex;
  align-items: stretch;
  gap: 4px;
  min-height: 300px;
}

.list-box {
  /* min-width: 300px; */
  /* width: 400px; */
  width: 100%;
  border: 1px solid v-bind('themeVarsComputed.borderColor');
  border-radius: var(--radius-sm);
  display: flex;
  height: 400px;
  flex-direction: column;
  overflow: hidden;
  /* background-color: #ffffff; */
  /* background-color: v-bind('themeVarsComputed.baseColor'); */
}

.list-header {
  padding: 4px;
  border-bottom: 1px solid v-bind('themeVarsComputed.borderColor');
}

.list-header :deep(.n-input),
.list-header :deep(.n-input__border),
.list-header :deep(.n-input__state-border) {
  border-radius: var(--radius-sm) !important;
}

.title {
  display: flex;
  align-items: center;
  padding: 8px;
  border-bottom: 1px solid v-bind('themeVarsComputed.borderColor');
  /* font-weight: bold; */
  color: #666;
}

.list-content {
  /* flex: 1; */
  /* min-height: 300px; */
  /* max-height: 300px; */
  /* height: 300px; */
  padding: 8px;
  overflow: hidden;
}

.list-footer {
  padding: 8px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f9fafb;
}

.list-item {
  /* padding: 0px; */
  padding-left: 4px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  margin-bottom: 0px;
}

.list-item>.span {
  display: inline-block !important;
  width: 100%;
  /* 确保 span 元素填满容器 */
  white-space: nowrap !important;
  /* 防止文本换行 */
  overflow: hidden;
  /* 隐藏超出部分 */
  text-overflow: ellipsis;
  /* 显示省略�?*/
  cursor: default;
  /* 鼠标悬停时显示默认光�?*/
}

.list-item:hover {
  background-color: v-bind('themeVarsComputed.hoverColor');
}

.transfer-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

/* :deep(.n-checkbox) {
    width: 100%;
  } */

:deep(.n-checkbox__label) {
  width: 100%;
}

.list-item>span {
  display: block;
  margin: 2px;
}
</style>
