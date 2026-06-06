<template>
  <div class="transfer-list-container">
    <div class="list-box">
      <div class="title">
        {{ leftTitle || '可选关系对象' }}
        <n-popover trigger="hover" placement="right-end">
          <template #trigger>
            <span class="help help-tooltip help-icon">
              <QuestionCircleFilled style="display: inline; height: 16px" />
            </span>
          </template>
          这是可用的{{
            modelName
          }}列表。你可以在选择框下面进行选择，然后点击两选框之间的"选择"箭头。
        </n-popover>
      </div>

      <div class="list-header">
        <n-input
          v-model:value="leftSearch"
          placeholder="搜索..."
          clearable
          @update:value="handleLeftSearch"
        />
      </div>
      <div class="list-content">
        <n-scrollbar @scroll="handleLeftScroll">
          <n-spin :show="leftLoading">
            <n-checkbox-group v-model:value="leftSelected">
              <div v-for="item in filteredLeftList" :key="item.value" class="list-item">
                <n-checkbox :value="item.value" :label="item.label" @update:checked="test" />
              </div>
            </n-checkbox-group>
          </n-spin>
        </n-scrollbar>
      </div>
      <div class="list-footer">
        <n-checkbox
          :checked="isAllLeftSelected"
          :indeterminate="isLeftIndeterminate"
          @update:checked="handleLeftSelectAll"
        >
          全选
        </n-checkbox>
        <span>{{ leftSelected.length }}/{{ leftList.length }}</span>
      </div>
    </div>

    <!-- <div class="transfer-controls">
      <n-button
        :disabled="leftSelected.length === 0"
        @click="handleMoveToRight"
        circle
        type="primary"
        size="tiny"
      >
        <template #icon>
          <n-icon><ArrowRightOutlined /></n-icon>
        </template>
      </n-button>
      <n-button
        :disabled="rightSelected.length === 0"
        @click="handleMoveToLeft"
        circle
        type="primary"
        size="tiny"
      >
        <template #icon>
          <n-icon><ArrowLeftOutlined /></n-icon>
        </template>
      </n-button>
    </div> -->

    <div class="list-box">
      <div class="title">
        {{ rightTitle || '已选关系对象' }}
      </div>
      <div class="list-header">
        <n-input
          v-model:value="rightSearch"
          placeholder="搜索..."
          clearable
          @update:value="handleRightSearch"
        />
      </div>
      <div class="list-content">
        <n-scrollbar @scroll="handleRightScroll">
          <n-spin :show="rightLoading">
            <n-checkbox-group v-model:value="rightSelected">
              <div v-for="item in filteredRightList" :key="item.value" class="list-item">
                <n-checkbox :value="item.value" :label="item.label" />
              </div>
            </n-checkbox-group>
          </n-spin>
        </n-scrollbar>
      </div>
      <div class="list-footer">
        <n-checkbox
          :checked="isAllRightSelected"
          :indeterminate="isRightIndeterminate"
          @update:checked="handleRightSelectAll"
        >
          全选
        </n-checkbox>
        <span>{{ rightSelected.length }}/{{ rightList.length }}</span>
      </div>
    </div>
    <div class="list-box">
      <div class="title">tmp</div>
      <div class="list-content">
        <!-- <n-scrollbar></n-scrollbar> -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, watchEffect, onMounted } from 'vue';
  import { ArrowLeftOutlined, ArrowRightOutlined, QuestionCircleFilled } from '@vicons/antd';
  import { debounce } from 'lodash-es';

  interface TransferItem {
    label: string;
    value: string | number;
  }

  function test(value: boolean) {
    console.log('test');
  }

  const props = withDefaults(
    defineProps<{
      sourceList: TransferItem[];
      value?: (string | number)[];
      rightListIn?: TransferItem[];
      onLeftSearch?: (search: string) => Promise<TransferItem[]>;
      onRightSearch?: (search: string) => Promise<TransferItem[]>;
      onScrollLeft?: (event: Event) => void;
      onScrollRight?: (event: Event) => void;
    }>(),
    {
      sourceList: () => [],
      value: () => [],
      rightListIn: () => [],
      onLeftSearch: undefined,
      onRightSearch: undefined,
      onScrollLeft: undefined,
      onScrollRight: undefined,
    }
  );

  const emit = defineEmits<{
    (e: 'update:leftList', value: TransferItem[]): void;
    (e: 'update:rightList', value: TransferItem[]): void;
    (e: 'update:value', value: (string | number)[]): void;
    (e: 'scroll-left', event: Event): void;
    (e: 'scroll-right', event: Event): void;
  }>();

  const leftList = ref<TransferItem[]>([]);
  const rightList = ref<TransferItem[]>([]);
  const leftSelected = ref<(string | number)[]>([]);
  const rightSelected = ref<(string | number)[]>([]);
  const leftSearch = ref('');
  const rightSearch = ref('');
  const leftLoading = ref(false);
  const rightLoading = ref(false);
  const leftTitle = ref('');
  const rightTitle = ref('');
  const modelName = ref('');

  // 搜索处理函数
  const handleLeftSearch = async (value: string) => {
    if (!props.onLeftSearch) return;

    try {
      leftLoading.value = true;
      const results = await props.onLeftSearch(value);
      leftList.value = results;
    } catch (error) {
      console.error('左侧搜索失败:', error);
    } finally {
      leftLoading.value = false;
    }
  };

  const handleRightSearch = async (value: string) => {
    if (!props.onRightSearch) return;

    try {
      rightLoading.value = true;
      const results = await props.onRightSearch(value);
      rightList.value = results;
    } catch (error) {
      console.error('右侧搜索失败:', error);
    } finally {
      rightLoading.value = false;
    }
  };

  // 防抖处理搜索
  const debouncedLeftSearch = debounce(handleLeftSearch, 300);
  const debouncedRightSearch = debounce(handleRightSearch, 300);

  // 监听sourceList变化并更新leftList
  watchEffect(() => {
    leftList.value = [...props.sourceList];
  });

  // 监听value属性变化，同步到rightList
  watchEffect(() => {
    if (props.value) {
      // 从sourceList中找出对应value的项目，移到rightList
      const valueSet = new Set(props.value);
      const selectedItems = props.sourceList.filter((item) => valueSet.has(item.value));
      rightList.value = selectedItems;
      leftList.value = props.sourceList.filter((item) => !valueSet.has(item.value));
    }
  });

  // 过滤后的列表（现在主要用于本地过滤）
  const filteredLeftList = computed(() => {
    return leftList.value;
  });

  const filteredRightList = computed(() => {
    return rightList.value;
  });

  // 全选状态
  const isAllLeftSelected = computed(() => {
    return leftList.value.length > 0 && leftSelected.value.length === leftList.value.length;
  });

  const isAllRightSelected = computed(() => {
    return rightList.value.length > 0 && rightSelected.value.length === rightList.value.length;
  });

  const isLeftIndeterminate = computed(() => {
    return leftSelected.value.length > 0 && leftSelected.value.length < leftList.value.length;
  });

  const isRightIndeterminate = computed(() => {
    return rightSelected.value.length > 0 && rightSelected.value.length < rightList.value.length;
  });

  // 处理全选
  const handleLeftSelectAll = (checked: boolean) => {
    leftSelected.value = checked ? leftList.value.map((item) => item.value) : [];
  };

  const handleRightSelectAll = (checked: boolean) => {
    rightSelected.value = checked ? rightList.value.map((item) => item.value) : [];
  };

  // 处理移动
  const handleMoveToRight = () => {
    const itemsToMove = leftList.value.filter((item) => leftSelected.value.includes(item.value));
    rightList.value = [...rightList.value, ...itemsToMove];
    leftList.value = leftList.value.filter((item) => !leftSelected.value.includes(item.value));
    leftSelected.value = [];
    emit('update:leftList', leftList.value);
    emit('update:rightList', rightList.value);
    emit(
      'update:value',
      rightList.value.map((item) => item.value)
    );
  };

  const handleMoveToLeft = () => {
    const itemsToMove = rightList.value.filter((item) => rightSelected.value.includes(item.value));
    leftList.value = [...leftList.value, ...itemsToMove];
    rightList.value = rightList.value.filter((item) => !rightSelected.value.includes(item.value));
    rightSelected.value = [];
    emit('update:leftList', leftList.value);
    emit('update:rightList', rightList.value);
    emit(
      'update:value',
      rightList.value.map((item) => item.value)
    );
  };

  // 处理滚动事件
  const handleLeftScroll = (event: Event) => {
    if (props.onScrollLeft) {
      props.onScrollLeft(event);
    }
    emit('scroll-left', event);
  };

  const handleRightScroll = (event: Event) => {
    if (props.onScrollRight) {
      props.onScrollRight(event);
    }
    emit('scroll-right', event);
  };

  onMounted(() => {
    if (props.rightListIn) {
      console.log('rightListIn:', props.rightListIn);
      rightList.value = props.rightListIn;
    }
  });
</script>

<style scoped>
  .transfer-list-container {
    width: 100%;
    max-width: 800px;
    display: flex;
    align-items: stretch;
    gap: 4px;
    min-height: 300px;
  }

  .list-box {
    /* min-width: 300px; */
    /* width: 400px; */
    width: 100%;
    border: 1px solid #e5e7eb;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    background-color: #ffffff;
  }

  .list-header {
    padding: 4px;
    border-bottom: 1px solid #e5e7eb;
  }

  .title {
    padding: 8px;
    border-bottom: 1px solid #e5e7eb;
    /* font-weight: bold; */
    color: #666;
  }

  .list-content {
    /* flex: 1; */
    /* min-height: 300px; */
    /* max-height: 300px; */
    height: 300px;
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
    border-radius: 4px;
    margin-bottom: 0px;
  }

  .list-item:hover {
    background-color: #eeeeee;
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
</style>
