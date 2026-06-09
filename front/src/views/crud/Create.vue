<template>
  <div ref="pageRootRef" class="edit-container" @scroll.capture="handlePageScroll">
    <n-card :bordered="false" class="edit-card">
      <n-page-header :subtitle="''">
        <template #title>{{ t('crud.newRecord') }}</template>
      </n-page-header>
      <br />
      <div v-if="formLoading" class="form-skeleton">
        <div v-for="i in 8" :key="i" style="margin-bottom: 24px">
          <div
            style="
              display: flex;
              align-items: center;
              justify-content: flex-start;
              gap: 4px;
              margin-bottom: 8px;
            "
          >
            <n-skeleton text style="width: 20%" />
            <n-skeleton text style="width: 40%" />
          </div>
          <n-skeleton text style="width: 100%" />
        </div>
      </div>
      <n-form
        v-else
        ref="formRef"
        :model="formData"
        label-placement="left"
        label-width="auto"
        require-mark-placement="right-hanging"
        :rules="rules"
        :key="formResetKey"
      >
        <n-form-item
          v-for="item in formItems"
          :key="item.field.field_name"
          :path="item.field.field_name"
        >
          <template #label>
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 4px">
              <span>{{ getFieldUiName(item.field) }}</span>
              <n-icon color="#999" :title="item.field.field_type">
                <component :is="fieldTypeIcons[item.field.field_type] || fieldTypeIcons.Default" />
              </n-icon>
            </div>
          </template>
          <div style="display: flex; flex-direction: column; width: 100%">
            <component
              :is="item.component || 'NInput'"
              ref="{{item.field.app_name}}:{{item.field.model_name}}:{{item.field.field_name}}"
              v-model:value="formData[item.field.field_name]"
              v-bind="{
                ...item.componentProps,
                disabled: item.field.read_only || item.field.is_pk,
              }"
              style="align-self: flex-start"
            />
            <FieldDescription :content="getFieldUiDescription(item.field)" />
          </div>
        </n-form-item>
      </n-form>
    </n-card>
    <div class="floating-buttons">
      <n-button type="success" @click="handleSubmit()" size="small">{{ t('button.saveAndClose') }}</n-button>
      <n-button type="success" @click="handleSaveAndEdit()" size="small">{{ t('button.saveAndContinue') }}</n-button>
      <n-button type="success" @click="handleSaveAndAddAnother()" size="small"
        >{{ t('button.saveAndAddAnother') }}</n-button
      >
      <n-button type="error" @click="handleDelete()" size="small">{{ t('button.delete') }}</n-button>
      <n-button @click="handleClearForm" size="small">{{ t('button.clearData') }}</n-button>
      <n-button @click="handleCancel" size="small">{{ t('common.cancel') }}</n-button>
      <!-- <n-button @click="test" size="small">测试</n-button> -->
    </div>
  </div>
</template>
<script setup lang="ts">
  import {
    ref,
    onMounted,
    toRaw,
    onActivated,
    onDeactivated,
    onUnmounted,
    computed,
    nextTick,
    watch,
  } from 'vue';
  import { FormItemFieldComponentMap } from './cmpsForm';
  import {
    createFormRules,
    FrontendMod,
    BackendMod,
    getFormDisplayFields,
    getFormFieldInfo,
    getBackendValidationMessage,
  } from './formData';
  import { fieldTypeIcons } from './columnRender';
  import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router';
  import {
    CreateModelItem,
    GetAllowModelInfo,
    DeleteModelItem,
    RelManage,
  } from '@/api/crud/models';
  import { CRUD_EDIT, CRUD_LIST, CRUD_CREATE } from '@/store/consts';
  import { useTabsViewStore } from '@/store/modules/tabsView';
  // import { useEventBus } from '@vueuse/core';
  import { cloneDeep } from 'lodash-es';
  import { useCrudRefresh } from '@/store/modules/crudListRefresh';
  import { getM2mChangeIds } from './formData';
  import FieldDescription from './FieldDescription.vue';
  import { getFieldUiDescription, getFieldUiName } from './tools';
  import { t } from '@/i18n';

  import { useThemeVars } from 'naive-ui';

  const themeVars = useThemeVars();
  const themeVarsComputed = computed(() => {
    return themeVars.value;
  });

  defineOptions({
    name: CRUD_CREATE,
  });

  const formLoading = ref(false);
  const modelInfo = ref();
  const currentRecord = ref<Recordable>({});
  const formRef = ref();
  const formData = ref({});
  const formResetKey = ref(0);
  const formItems = ref<Recordable[]>([]);
  const pageRootRef = ref<HTMLElement | null>(null);
  const pageScrollPosition = ref({ top: 0, left: 0 });
  let removePageScrollListeners: (() => void) | null = null;
  const pendingRestorePageScroll = ref(false);
  let finishRestoreTimer: number | null = null;
  const pk = ref<string>('');
  const route = useRoute();
  const router = useRouter();
  const tabFullPath = route.fullPath;
  const crudRefresh = useCrudRefresh();
  const tabsViewStore = useTabsViewStore();
  const appName = ref('');
  const modelName = ref('');
  const objId = ref('');
  const createInstanceIndex = ref('');
  const rules = ref({});
  const initialData = {};
  const saveCount = ref(0);
  const restoreTimers: number[] = [];
  const restoreRafIds: number[] = [];
  let pageRestoreToken = 0;
  let isApplyingPageScrollRestore = false;
  const handleSavedPageScroll = () => {
    if (route.fullPath !== tabFullPath || isApplyingPageScrollRestore) return;
    if (pendingRestorePageScroll.value) {
      clearPendingPageScrollRestore();
      savePageScrollPosition(true);
      return;
    }
    savePageScrollPosition();
  };
  const handlePageScroll = () => {
    savePageScrollPosition();
  };
  const handleTabsCardBeforeSwitch = (event: Event) => {
    const detail = (event as CustomEvent).detail;
    if (detail?.fromFullPath === tabFullPath) {
      clearPendingPageScrollRestore();
      savePageScrollPosition(true);
    }
    if (detail?.toFullPath === tabFullPath) {
      window.setTimeout(() => {
        bindPageScrollListeners();
        restorePageScrollPosition();
      }, 0);
    }
  };

  function ensureCreateInstanceIndex() {
    if (createInstanceIndex.value) return;
    const counterKey = `crud:${appName.value}:${modelName.value}:create:counter`;
    const nextIndex = Number(sessionStorage.getItem(counterKey) || 0) + 1;
    sessionStorage.setItem(counterKey, String(nextIndex));
    createInstanceIndex.value = String(nextIndex);
  }

  function getScrollStorageKey() {
    ensureCreateInstanceIndex();
    return `crud:${appName.value}:${modelName.value}:create:${createInstanceIndex.value}:scroll`;
  }

  function getStoredPageScrollPosition() {
    const key = getScrollStorageKey();
    const rawValue = sessionStorage.getItem(key);
    if (!rawValue) return null;
    try {
      return JSON.parse(rawValue);
    } catch {
      sessionStorage.removeItem(key);
      return null;
    }
  }

  const FkField = ['ForeignKeyField', 'OneToOneField'];
  function getFormComponentName(field: Recordable) {
    return field?.form_cmp;
  }

  function getPageScrollElement() {
    const root = pageRootRef.value;
    const layoutScrollEl = Array.from(
      document.querySelectorAll<HTMLElement>('.layout-scroll-container .n-scrollbar-container')
    )
      .filter(
        (el) =>
          (!root || el.contains(root)) &&
          (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth)
      )
      .sort(
        (a, b) =>
          b.scrollHeight -
          b.clientHeight +
          (b.scrollWidth - b.clientWidth) -
          (a.scrollHeight - a.clientHeight + (a.scrollWidth - a.clientWidth))
      )[0];
    if (layoutScrollEl) {
      return layoutScrollEl;
    }

    let el = pageRootRef.value?.parentElement || null;
    while (el) {
      if (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth) {
        return el;
      }
      el = el.parentElement;
    }
    return document.scrollingElement as HTMLElement | null;
  }

  function getPageScrollElements() {
    const elements: HTMLElement[] = [];
    const pageScrollEl = getPageScrollElement();
    if (pageScrollEl) elements.push(pageScrollEl);
    let el = pageRootRef.value as HTMLElement | null;
    while (el) {
      if (
        (el.scrollHeight > el.clientHeight || el.scrollWidth > el.clientWidth) &&
        !elements.includes(el)
      ) {
        elements.push(el);
      }
      el = el.parentElement;
    }
    const docEl = document.scrollingElement as HTMLElement | null;
    if (docEl && !elements.includes(docEl)) {
      elements.push(docEl);
    }
    return elements;
  }

  async function bindPageScrollListeners() {
    removePageScrollListeners?.();
    await nextTick();
    const scrollElements = getPageScrollElements();
    scrollElements.forEach((el) => el.addEventListener('scroll', handleSavedPageScroll, true));
    document.addEventListener('scroll', handleSavedPageScroll, true);
    removePageScrollListeners = () => {
      scrollElements.forEach((el) => el.removeEventListener('scroll', handleSavedPageScroll, true));
      document.removeEventListener('scroll', handleSavedPageScroll, true);
      removePageScrollListeners = null;
    };
  }

  function savePageScrollPosition(force = false) {
    if (pendingRestorePageScroll.value && !force) return;

    const pageScrollEl = getPageScrollElement();
    if (!pageScrollEl) return;
    pageScrollPosition.value = {
      top: pageScrollEl.scrollTop,
      left: pageScrollEl.scrollLeft,
    };
    const previous = getStoredPageScrollPosition();
    const nextHasPosition = pageScrollPosition.value.top || pageScrollPosition.value.left;
    const previousHasPosition = previous?.top || previous?.left;
    if (previousHasPosition && !nextHasPosition) {
      return;
    }
    sessionStorage.setItem(getScrollStorageKey(), JSON.stringify(pageScrollPosition.value));
  }

  function loadPageScrollPosition() {
    const saved = getStoredPageScrollPosition();
    if (!saved) return false;
    pageScrollPosition.value = saved;
    return true;
  }

  function clearPendingPageScrollRestore() {
    pageRestoreToken++;
    if (finishRestoreTimer) {
      window.clearTimeout(finishRestoreTimer);
      finishRestoreTimer = null;
    }
    restoreTimers.splice(0).forEach((timer) => window.clearTimeout(timer));
    restoreRafIds.splice(0).forEach((rafId) => window.cancelAnimationFrame(rafId));
    pendingRestorePageScroll.value = false;
    isApplyingPageScrollRestore = false;
  }

  async function restorePageScrollPosition() {
    clearPendingPageScrollRestore();
    if (!loadPageScrollPosition()) return;
    pageRestoreToken++;
    const restoreToken = pageRestoreToken;
    pendingRestorePageScroll.value = true;
    await nextTick();
    const restore = () => {
      if (!pendingRestorePageScroll.value || restoreToken !== pageRestoreToken) return;

      isApplyingPageScrollRestore = true;
      getPageScrollElements().forEach((el) => {
        if (el.scrollHeight > el.clientHeight) {
          el.scrollTop = pageScrollPosition.value.top;
        }
        if (el.scrollWidth > el.clientWidth) {
          el.scrollLeft = pageScrollPosition.value.left;
        }
      });
      restoreRafIds.push(
        window.requestAnimationFrame(() => {
          if (restoreToken === pageRestoreToken) {
            isApplyingPageScrollRestore = false;
          }
        })
      );
    };

    const scheduleRestore = (delay: number) => {
      restoreTimers.push(window.setTimeout(restore, delay));
    };

    restoreRafIds.push(
      window.requestAnimationFrame(() => {
        restore();
        restoreRafIds.push(window.requestAnimationFrame(restore));
      })
    );
    [50, 120, 240, 480, 800].forEach(scheduleRestore);
    finishRestoreTimer = window.setTimeout(() => {
      if (restoreToken !== pageRestoreToken) return;
      pendingRestorePageScroll.value = false;
      isApplyingPageScrollRestore = false;
      finishRestoreTimer = null;
      savePageScrollPosition(true);
    }, 1000);
  }

  watch(
    () => route.fullPath,
    (newFullPath, oldFullPath) => {
      if (oldFullPath === tabFullPath && newFullPath !== oldFullPath) {
        clearPendingPageScrollRestore();
        savePageScrollPosition(true);
      }
    },
    { flush: 'sync' }
  );

  watch(
    () => route.fullPath,
    async (newFullPath) => {
      if (newFullPath !== tabFullPath) return;
      await bindPageScrollListeners();
      await restorePageScrollPosition();
    },
    { flush: 'post' }
  );

  // ==================== 数据操作函数 ====================
  // 创建新记�?  // returnToList = false, resetForm = false
  async function createRecord() {
    try {
      const raw_data = toRaw(formData.value);
      const { commFields, m2mFields } = BackendMod(raw_data, modelInfo.value.fields_info);
      const { data } = await CreateModelItem(appName.value, modelName.value, commFields);
      objId.value = `${data.id}`;
      formData.value = FrontendMod(data, modelInfo.value.fields_info);
      currentRecord.value = cloneDeep(data);

      for (const [field_name, items] of Object.entries(m2mFields)) {
        const m2m_ids = getM2mChangeIds(items);
        if (!m2m_ids) {
          continue;
        }
        const params = {
          action: 'manage',
          field_name,
          id: toRaw(objId.value),
          m2m_ids: toRaw(m2m_ids),
        };
        await RelManage(appName.value, modelName.value, params);
      }

      window['$message'].success(t('crud.createDone'));
      crudRefresh.setRefreshFlag(appName.value, modelName.value);
      formData.value = {};

      console.log('@@@createRecord', commFields, m2mFields);
      return true;
    } catch (error: any) {
      console.error('创建失败:', error);
      window['$message'].error(
        t('crud.createError', {
          error: getBackendValidationMessage(error, modelInfo.value?.fields_info || {}),
        })
      );
      return false;
    }
  }

  function modelListPage() {
    tabsViewStore.closeCurrentTab(route as any);
    // Navigate back without query params to avoid creating new tabs
    router.push({
      name: CRUD_LIST,
      params: { app_name: appName.value, model_name: modelName.value },
    });
  }

  function editcurrent() {
    tabsViewStore.closeCurrentTab(route as any);
    router.push({
      name: CRUD_EDIT,
      params: {
        app_name: appName.value,
        model_name: modelName.value,
        id: toRaw(objId.value),
      },
      replace: true,
    });
  }

  async function formValidate() {
    try {
      await formRef.value.validate();
    } catch (error) {
      console.log(error);
      window['$message'].error(t('crud.validationFailed'));
      throw error;
    }
  }

  // ==================== 按钮处理函数 ====================

  async function handleSubmit() {
    await formValidate();
    const success = await createRecord();
    if (success) {
      formResetKey.value++;
      modelListPage();
    }
  }

  async function handleSaveAndEdit() {
    await formValidate();
    const success = await createRecord();
    console.log(objId.value);
    if (success) {
      editcurrent();
    }
  }

  async function handleSaveAndAddAnother() {
    await formValidate();
    let success = false;
    success = await createRecord();
    if (success) {
      handleClearForm();
    }
    await router.push({
      name: CRUD_CREATE,
      params: {
        app_name: appName.value,
        model_name: modelName.value,
      },
    });
    // }
  }

  // 删除记录
  function handleDelete() {
    window['$dialog'].warning({
      title: t('crud.deleteConfirmTitle'),
      content: t('crud.deleteConfirmRecord'),
      positiveText: t('crud.confirmDelete'),
      negativeText: t('common.cancel'),
      autoFocus: false,
      onPositiveClick: async () => {
        try {
          await DeleteModelItem(appName.value, modelName.value, currentRecord.value?.id);
          crudRefresh.setRefreshFlag(appName.value, modelName.value);
          window['$message'].success(t('crud.deleteDone'));
          tabsViewStore.closeCurrentTab(route as any);
          router.push({
            name: CRUD_LIST,
            params: { app_name: appName.value, model_name: modelName.value },
          });
        } catch (error: any) {
          console.error('删除失败:', error);
          window['$message'].error(
            t('crud.deleteError', { error: error.message || t('common.unknownError') })
          );
        }
      },
    });
  }
  // 清空数据
  function handleClearForm() {
    formData.value = {};
    formResetKey.value++;
  }

  // 取消
  function handleCancel() {
    tabsViewStore.closeCurrentTab(route as any);
    router.push({
      name: CRUD_LIST,
      params: { app_name: appName.value, model_name: modelName.value },
    });
  }

  // 测试
  // async function test() {
  //   console.log('!!!!!!!!!!!!!!', toRaw(formData.value));
  //   await formValidate();
  // }

  async function generateFormItems(model_info, id) {
    const { fields_info, ui } = model_info.value;
    if (!fields_info) return [];
    const items: any[] = [];
    const excludeFields = ui?.exclude_fields || [];
    const display_fields = getFormDisplayFields(fields_info, ui);
    // 使用 for...of 循环，这样可以按顺序处理每个字段
    // for (const item of Object.values(fields_info)) {
    // 添加类型断言，定�?field 的类�?    // const field = item as { field_type: string; field_name: string };
    // const field = item as Recordable;
    for (const field_name of display_fields) {
      const field = getFormFieldInfo(fields_info, field_name);
      // Skip excluded fields
      if (excludeFields.includes(field_name)) continue;
      const field_group1 = ['ForeignKeyField', 'OneToOneField', 'BackwardFKRelation'];
      if (field.source_field && !field_group1.includes(field.field_type)) {
        console.log(
          `[${field.field_type}:${field.field_name}] FK field id need not to be edit derectly.`
        );
        continue;
      }
      const formComponentName = getFormComponentName(field);
      const resolvedFormComponentName =
        formComponentName && formComponentName in FormItemFieldComponentMap
          ? formComponentName
          : 'InputField';
      if (resolvedFormComponentName in FormItemFieldComponentMap) {
        try {
          let result: any = null;
          const relation_search = ui.relation_search[field.field_name] ||
            ui.relation_search[field.source_field] || ['id'];
          const types_group1 = ['ForeignKeyField', 'ManyToManyField', 'BackwardFKRelation'];
          if (types_group1.includes(field.field_type)) {
            result = FormItemFieldComponentMap[resolvedFormComponentName](
              field,
              id,
              relation_search,
              saveCount
            );
          } else if (FkField.includes(field.field_type)) {
            console.log('formData', formData.value);
            result = FormItemFieldComponentMap[resolvedFormComponentName](
              field,
              id,
              relation_search
            );
          } else {
            result = FormItemFieldComponentMap[resolvedFormComponentName](field);
          }
          // 等待包含下拉框的组件的异步Promise完成或直接使用结�?          // const item = await (result instanceof Promise ? result : Promise.resolve(result));
          const item = result instanceof Promise ? await result : result;
          if (item) items.push(item);
        } catch (error) {
          console.error(`Failed to generate form item for ${field.field_name}`, error);
        }
      }
    }
    return items; // 直接返回对象列表，不�?Promise
  }

  onMounted(async () => {
    // 获取路由参数
    window.addEventListener('tabs-card:before-switch', handleTabsCardBeforeSwitch);
    window.addEventListener('tabs-card:after-switch', handleTabsCardBeforeSwitch);
    appName.value = route.params.app_name as string;
    modelName.value = route.params.model_name as string;
    ensureCreateInstanceIndex();
    console.log(`@@@crud_create:${appName.value}:${modelName.value} onMounted`);
    objId.value = route.params.id as string;
    await bindPageScrollListeners();

    // 加载模型信息
    const { data: model_info_data } = await GetAllowModelInfo({
      model_name: `${appName.value}:${modelName.value}`,
    });
    modelInfo.value = model_info_data;
    console.log('@@@modelInfo', toRaw(modelInfo.value));

    const { fields_info } = modelInfo.value;
    let fk = [] as string[];
    // const pkField = Object.values(fields_info).find((field: any) => field.is_pk) as Recordable;
    Object.values(fields_info).forEach((field: any, _) => {
      if (field.is_pk) {
        pk.value = field.field_name;
      }
      if (FkField.includes(field.field_type)) {
        fk.push(field.field_name);
      }
    });

    formItems.value = await generateFormItems(modelInfo, objId.value);
    rules.value =
      createFormRules(
        fields_info,
        formItems.value.map((item) => item.field.field_name)
      ) || {};

    formItems.value.forEach((item) => {
      if (item.field_type === 'Boolean') {
        initialData[item.field_name] = item.default || false;
      } else {
        if (item.default) {
          initialData[item.field_name] = item.default;
        }
      }
    });
    console.log('@@@initialData', initialData);
    formData.value = cloneDeep(initialData);
    await nextTick();
    await bindPageScrollListeners();
    restorePageScrollPosition();
  });
  onActivated(() => {
    // console.log('edit onActivated', route.fullPath);
    bindPageScrollListeners();
    restorePageScrollPosition();
  });
  onDeactivated(() => {
    clearPendingPageScrollRestore();
    savePageScrollPosition(true);
    removePageScrollListeners?.();
  });
  onBeforeRouteLeave(() => {
    clearPendingPageScrollRestore();
    savePageScrollPosition(true);
  });
  onUnmounted(() => {
    clearPendingPageScrollRestore();
    removePageScrollListeners?.();
    window.removeEventListener('tabs-card:before-switch', handleTabsCardBeforeSwitch);
    window.removeEventListener('tabs-card:after-switch', handleTabsCardBeforeSwitch);
  });

  // const handleBeforeUnload = (event) => {
  //   // 执行一些同步清理操�?  //   console.log('页面即将关闭');
  // };
  // window.addEventListener('beforeunload', handleBeforeUnload);
  // onUnmounted(() => {
  //   console.log(`@@@crud_edit:${appName.value}:${modelName.value} onUnmounted`);
  //   window.removeEventListener('beforeunload', handleBeforeUnload);
  //   formData.value = {};
  // });
</script>
<style lang="less" scoped>
  .edit-container {
    position: relative;
    min-height: 100%;
    padding-bottom: 80px; /* 为底部按钮留出空�?*/
  }

  .floating-buttons {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 10px;
    z-index: 100;
    background-color: v-bind('themeVarsComputed.baseColor');
    padding: 5px 5px;
    border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    width: fit-content;
    margin: 0 auto;
  }

  // .edit-card {
  //   margin-top: 6px;
  // }
</style>
