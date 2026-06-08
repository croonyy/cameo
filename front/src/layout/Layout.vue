<template>
  <n-layout class="layout" :position="fixedMenu" has-sider>
    <!-- 正常菜单栏 -->
    <n-layout-sider
      v-if="
        !isMobile && isMixMenuNoneSub && (navMode === 'vertical' || navMode === 'horizontal-mix')
      "
      show-trigger="bar"
      @collapse="collapsed = true"
      :position="fixedMenu"
      @expand="collapsed = false"
      :collapsed="collapsed"
      collapse-mode="width"
      :collapsed-width="40"
      :width="leftMenuWidth"
      :native-scrollbar="false"
      :inverted="siderInverted"
      class="layout-sider"
    >
      <Logo :collapsed="collapsed" />
      <AsideMenu v-model:collapsed="collapsed" v-model:location="getMenuLocation" />
      <div
        v-if="!collapsed"
        class="layout-sider-resizer"
        title="拖拽调整菜单宽度"
        @mousedown.prevent="startResizeMenu"
      />
    </n-layout-sider>

    <!-- 移动端的抽屉式菜单栏 -->
    <n-drawer
      v-model:show="showSideDrawer"
      :width="menuWidth"
      :placement="'left'"
      class="layout-side-drawer"
    >
      <n-layout-sider
        :position="fixedMenu"
        :collapsed="false"
        :width="menuWidth"
        :native-scrollbar="false"
        :inverted="siderInverted"
        class="layout-sider"
      >
        <Logo :collapsed="collapsed" />
        <AsideMenu v-model:location="getMenuLocation" />
      </n-layout-sider>
    </n-drawer>

    <div class="layout-right-wrapper">
      <div class="layout-right-header">
        <PageHeader
          v-model:collapsed="collapsed"
          :inverted="headerInverted"
          :sider-width="leftMenuWidth"
        />
      </div>

      <TabsView v-if="isMultiTabs && fixedMulti" v-model:collapsed="collapsed" />
      <n-layout :inverted="contentInverted" class="layout-right" :native-scrollbar="false">
        <n-scrollbar
          ref="layoutScrollbarRef"
          class="layout-scroll-container"
          :class="{ 'layout-default-background': getDarkTheme === false }"
          @scroll="handleLayoutScroll"
        >
          <TabsView v-if="isMultiTabs && !fixedMulti" v-model:collapsed="collapsed" />
          <div class="content-wrapper">
            <div
              class="main-view"
              :class="{
                noMultiTabs: !isMultiTabs,
                'mt-3': !isMultiTabs,
              }"
            >
              <MainView />
            </div>
          </div>
        </n-scrollbar>
        <n-back-top :right="100" />
      </n-layout>
    </div>
  </n-layout>
</template>

<script lang="ts" setup>
  import {
    ref,
    unref,
    computed,
    onMounted,
    onBeforeMount,
    onBeforeUnmount,
    watch,
    nextTick,
  } from 'vue';
  import Logo from './components/Logo/Logo.vue';
  import AsideMenu from './components/Menu/AsideMenu.vue';
  import PageHeader from './components/Header/PageHeader.vue';
  import TabsView from './components/TagsView/TabsView.vue';
  import MainView from './components/Main/MainContent.vue';
  import { useProjectSetting } from '@/hooks/setting/useProjectSetting';
  import { useDesignSetting } from '@/hooks/setting/useDesignSetting';
  import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute } from 'vue-router';
  import { useProjectSettingStore } from '@/store/modules/projectSetting';
  // import { useCrudMenu } from '@/store/modules/crudMenu';
  // import { GetAllModelsInfo } from '@/api/crud/menu';

  import { useThemeVars } from 'naive-ui';
  const themeVars = useThemeVars();
  const themeVarsComputed = computed(() => themeVars.value);
  const route = useRoute();
  const layoutScrollbarRef = ref<any>(null);
  const routeScrollMap = new Map<string, { top: number; left: number }>();
  let layoutRestoreId = 0;
  let removeLayoutScrollListener: (() => void) | null = null;
  let layoutScrollSnapshotTimer: ReturnType<typeof window.setInterval> | null = null;
  const layoutRestoreTimers: ReturnType<typeof window.setTimeout>[] = [];
  const layoutRestoreRafIds: number[] = [];
  let isApplyingLayoutScrollRestore = false;
  const closedLayoutScrollPaths = new Set<string>();

  const { getDarkTheme } = useDesignSetting();
  const {
    // showFooter,
    navMode,
    navTheme,
    headerSetting,
    menuSetting,
    multiTabsSetting,
  } = useProjectSetting();

  const settingStore = useProjectSettingStore();

  // 从 localStorage 读取菜单状态，默认为 false
  const MENU_COLLAPSED_KEY = 'menu_collapsed';
  const getStoredCollapsed = () => {
    try {
      const stored = localStorage.getItem(MENU_COLLAPSED_KEY);
      return stored ? stored === 'true' : false;
    } catch {
      return false;
    }
  };

  const collapsed = ref<boolean>(getStoredCollapsed());

  function getLayoutScrollKey(fullPath = route.fullPath) {
    return `layout:scroll:${fullPath}`;
  }

  function clearLayoutScrollPosition(fullPath: string) {
    routeScrollMap.delete(fullPath);
    sessionStorage.removeItem(getLayoutScrollKey(fullPath));
  }

  function getLayoutScrollContainer() {
    const asHTMLElement = (value: any): HTMLElement | null =>
      value instanceof HTMLElement ? value : null;
    const activePageRoot = document.querySelector<HTMLElement>(
      '.crud-list-wrapper, .edit-container, .main-content'
    );
    let activeParent = activePageRoot?.parentElement || null;
    while (activeParent) {
      if (
        activeParent.scrollHeight > activeParent.clientHeight + 1 ||
        activeParent.scrollWidth > activeParent.clientWidth + 1
      ) {
        return activeParent;
      }
      activeParent = activeParent.parentElement;
    }

    const componentRoot = asHTMLElement(layoutScrollbarRef.value?.$el);
    const exposedEl = asHTMLElement(
      layoutScrollbarRef.value?.containerRef ||
        layoutScrollbarRef.value?.scrollableElRef ||
        layoutScrollbarRef.value?.$el?.querySelector?.('.n-scrollbar-container')
    );
    if (exposedEl && exposedEl.scrollHeight > exposedEl.clientHeight) {
      return exposedEl;
    }

    const ownScrollbarContainer = componentRoot?.querySelector<HTMLElement>(
      ':scope > .n-scrollbar-container'
    );
    if (
      ownScrollbarContainer &&
      (ownScrollbarContainer.scrollHeight > ownScrollbarContainer.clientHeight ||
        ownScrollbarContainer.scrollWidth > ownScrollbarContainer.clientWidth)
    ) {
      return ownScrollbarContainer;
    }

    const ownScrollableContainer = Array.from(
      componentRoot?.querySelectorAll<HTMLElement>('.n-scrollbar-container') || []
    )
      .filter(
        (el) =>
          el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1
      )
      .sort(
        (a, b) =>
          b.scrollHeight -
          b.clientHeight +
          (b.scrollWidth - b.clientWidth) -
          (a.scrollHeight - a.clientHeight + (a.scrollWidth - a.clientWidth))
      )[0];
    if (ownScrollableContainer) {
      return ownScrollableContainer;
    }

    const layoutRightEl = document.querySelector<HTMLElement>(
      '.layout-right > .n-layout-scroll-container'
    );
    if (layoutRightEl && layoutRightEl.scrollHeight > layoutRightEl.clientHeight) {
      return layoutRightEl;
    }

    return (
      (exposedEl as HTMLElement | null) ||
      layoutRightEl ||
      document.querySelector<HTMLElement>('.layout-scroll-container > .n-scrollbar-container')
    );
  }

  function saveLayoutScrollPosition(fullPath = route.fullPath) {
    if (closedLayoutScrollPaths.has(fullPath)) return;
    const el = getLayoutScrollContainer();
    if (!el) return;
    const position = {
      top: el.scrollTop,
      left: el.scrollLeft,
    };
    const previous = routeScrollMap.get(fullPath) || loadLayoutScrollPosition(fullPath);
    if (position.top === 0 && position.left === 0 && (previous.top > 0 || previous.left > 0)) {
      return;
    }
    routeScrollMap.set(fullPath, position);
    sessionStorage.setItem(getLayoutScrollKey(fullPath), JSON.stringify(position));
  }

  function loadLayoutScrollPosition(fullPath = route.fullPath) {
    const cached = routeScrollMap.get(fullPath);
    if (cached) return cached;
    const rawValue = sessionStorage.getItem(getLayoutScrollKey(fullPath));
    if (!rawValue) return { top: 0, left: 0 };
    try {
      const saved = JSON.parse(rawValue);
      routeScrollMap.set(fullPath, saved);
      return saved;
    } catch {
      sessionStorage.removeItem(getLayoutScrollKey(fullPath));
      return { top: 0, left: 0 };
    }
  }

  function clearLayoutScrollRestore() {
    layoutRestoreId++;
    layoutRestoreTimers.splice(0).forEach((timer) => window.clearTimeout(timer));
    layoutRestoreRafIds.splice(0).forEach((rafId) => window.cancelAnimationFrame(rafId));
    isApplyingLayoutScrollRestore = false;
  }

  async function restoreLayoutScrollPosition(fullPath = route.fullPath) {
    clearLayoutScrollRestore();
    const restoreId = layoutRestoreId;
    const position = loadLayoutScrollPosition(fullPath);
    await nextTick();
    const restore = () => {
      if (restoreId !== layoutRestoreId || route.fullPath !== fullPath) return;
      isApplyingLayoutScrollRestore = true;
      layoutScrollbarRef.value?.scrollTo?.({
        top: position.top,
        left: position.left,
      });
      const el = getLayoutScrollContainer();
      if (el) {
        el.scrollTop = position.top;
        el.scrollLeft = position.left;
      }
      layoutRestoreRafIds.push(
        requestAnimationFrame(() => {
          if (restoreId === layoutRestoreId) {
            isApplyingLayoutScrollRestore = false;
          }
        })
      );
    };
    const rafId = requestAnimationFrame(() => {
      if (restoreId !== layoutRestoreId || route.fullPath !== fullPath) return;
      restore();
      layoutRestoreRafIds.push(requestAnimationFrame(restore));
    });
    layoutRestoreRafIds.push(rafId);
    [80, 240].forEach((delay) => {
      layoutRestoreTimers.push(window.setTimeout(restore, delay));
    });
  }

  function handleLayoutScroll(e: Event) {
    if (closedLayoutScrollPaths.has(route.fullPath)) return;
    if (isApplyingLayoutScrollRestore) return;
    if (layoutRestoreTimers.length || layoutRestoreRafIds.length) {
      clearLayoutScrollRestore();
    }
    const target = e.target as HTMLElement | null;
    const isLayoutScrollTarget =
      target &&
      (target.classList?.contains('layout-scroll-container') ||
        target.classList?.contains('n-layout-scroll-container') ||
        target.closest?.('.layout-scroll-container') === layoutScrollbarRef.value?.$el);
    const el =
      isLayoutScrollTarget &&
      (target.scrollHeight > target.clientHeight || target.scrollWidth > target.clientWidth)
        ? target
        : getLayoutScrollContainer();
    if (!el) return;
    const position = {
      top: el.scrollTop,
      left: el.scrollLeft,
    };
    routeScrollMap.set(route.fullPath, position);
    sessionStorage.setItem(getLayoutScrollKey(), JSON.stringify(position));
  }

  function handleClosedTabs(event: Event) {
    const fullPaths = (event as CustomEvent).detail?.fullPaths;
    if (!Array.isArray(fullPaths)) return;
    fullPaths.filter(Boolean).forEach((fullPath) => {
      closedLayoutScrollPaths.add(fullPath);
      clearLayoutScrollPosition(fullPath);
    });
  }

  function startLayoutScrollSnapshot() {
    if (layoutScrollSnapshotTimer) return;
    layoutScrollSnapshotTimer = window.setInterval(() => {
      saveLayoutScrollPosition();
    }, 250);
  }

  async function bindLayoutScrollListener() {
    removeLayoutScrollListener?.();
    await nextTick();
    const el = getLayoutScrollContainer();
    if (!el) return;
    el.addEventListener('scroll', handleLayoutScroll, { passive: true });
    document.addEventListener('scroll', handleLayoutScroll, true);
    removeLayoutScrollListener = () => {
      el.removeEventListener('scroll', handleLayoutScroll);
      document.removeEventListener('scroll', handleLayoutScroll, true);
      removeLayoutScrollListener = null;
    };
  }

  const { mobileWidth, menuWidth } = unref(menuSetting);
  const MENU_WIDTH_KEY = 'menu_width';
  const MIN_RESIZABLE_MENU_WIDTH = 160;
  const MAX_RESIZABLE_MENU_WIDTH = 360;
  const getStoredMenuWidth = () => {
    try {
      const stored = Number(localStorage.getItem(MENU_WIDTH_KEY));
      if (!Number.isFinite(stored)) return menuWidth;
      return Math.min(
        MAX_RESIZABLE_MENU_WIDTH,
        Math.max(MIN_RESIZABLE_MENU_WIDTH, stored)
      );
    } catch {
      return menuWidth;
    }
  };
  const resizedMenuWidth = ref<number>(getStoredMenuWidth());

  const isMobile = computed<boolean>({
    get: () => settingStore.getIsMobile,
    set: (val) => settingStore.setIsMobile(val),
  });

  const fixedHeader = computed(() => {
    const { fixed } = unref(headerSetting);
    return fixed ? 'absolute' : 'static';
  });

  const isMixMenuNoneSub = computed(() => {
    const mixMenu = unref(menuSetting).mixMenu;
    const currentRoute = useRoute();
    if (unref(navMode) != 'horizontal-mix') return true;
    if (unref(navMode) === 'horizontal-mix' && mixMenu && currentRoute.meta.isRoot) {
      return false;
    }
    return true;
  });

  const fixedMenu = computed(() => {
    const { fixed } = unref(headerSetting);
    return fixed ? 'absolute' : 'static';
  });

  const isMultiTabs = computed(() => {
    return unref(multiTabsSetting).show;
  });

  const fixedMulti = computed(() => {
    return unref(multiTabsSetting).fixed;
  });

  const siderInverted = computed(() => {
    return ['dark', 'header-dark'].includes(unref(navTheme));
  });

  const headerInverted = computed(() => {
    return unref(navTheme) === 'header-dark';
  });

  const contentInverted = computed(() => false);

  const leftMenuWidth = computed(() => {
    const { minMenuWidth } = unref(menuSetting);
    return collapsed.value ? minMenuWidth : resizedMenuWidth.value;
  });

  function startResizeMenu(event: MouseEvent) {
    if (isMobile.value || collapsed.value) return;
    const startX = event.clientX;
    const startWidth = resizedMenuWidth.value;
    document.body.classList.add('layout-sider-resizing');

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const nextWidth = startWidth + moveEvent.clientX - startX;
      resizedMenuWidth.value = Math.min(
        MAX_RESIZABLE_MENU_WIDTH,
        Math.max(MIN_RESIZABLE_MENU_WIDTH, nextWidth)
      );
    };

    const handleMouseUp = () => {
      document.body.classList.remove('layout-sider-resizing');
      localStorage.setItem(MENU_WIDTH_KEY, String(resizedMenuWidth.value));
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  }

  const getMenuLocation = computed(() => {
    return 'left';
  });

  // 控制显示或隐藏移动端侧边栏
  const showSideDrawer = computed({
    get: () => isMobile.value && collapsed.value,
    set: (val) => (collapsed.value = val),
  });

  //监听菜单状态变化并保存到 localStorage
  watch(collapsed, (newVal) => {
    try {
      localStorage.setItem(MENU_COLLAPSED_KEY, String(newVal));
    } catch (e) {
      console.error('Failed to save menu state:', e);
    }
  });

  watch(
    () => route.fullPath,
    (newFullPath, oldFullPath) => {
      if (oldFullPath && newFullPath !== oldFullPath) {
        saveLayoutScrollPosition(oldFullPath);
      }
    },
    { flush: 'sync' }
  );

  watch(
    () => route.fullPath,
    async (newFullPath) => {
      closedLayoutScrollPaths.delete(newFullPath);
      await bindLayoutScrollListener();
      await restoreLayoutScrollPosition(newFullPath);
    },
    { flush: 'post' }
  );

  onBeforeRouteUpdate((to, from) => {
    saveLayoutScrollPosition(from.fullPath);
  });

  onBeforeRouteLeave((to, from) => {
    saveLayoutScrollPosition(from.fullPath);
  });

  //判断是否触发移动端模式
  const checkMobileMode = () => {
    if (document.body.clientWidth <= mobileWidth) {
      isMobile.value = true;
      // 移动端强制折叠
      collapsed.value = true;
    } else {
      isMobile.value = false;
      // 桌面端恢复用户保存的状态
      collapsed.value = getStoredCollapsed();
    }
  };

  const watchWidth = () => {
    const Width = document.body.clientWidth;
    const wasMobile = isMobile.value;
    const isNowMobile = Width <= mobileWidth;

    // 只在移动端/桌面端状态切换时改变 collapsed
    if (isNowMobile && !wasMobile) {
      // 进入移动端模式
      isMobile.value = true;
      collapsed.value = true;
    } else if (!isNowMobile && wasMobile) {
      // 退出移动端模式，恢复用户保存的状态
      isMobile.value = false;
      collapsed.value = getStoredCollapsed();
    }
  };

  onMounted(() => {
    // 桌面端使用保存的状态，移动端强制折叠
    if (document.body.clientWidth <= mobileWidth) {
      isMobile.value = true;
      collapsed.value = true;
    } else {
      isMobile.value = false;
      // 不覆盖从 localStorage 读取的状态
    }
    window.addEventListener('resize', watchWidth);
    window.addEventListener('tabs-card:closed', handleClosedTabs);
    document.addEventListener('scroll', handleLayoutScroll, true);
    bindLayoutScrollListener();
    startLayoutScrollSnapshot();
    restoreLayoutScrollPosition();
  });

  onBeforeUnmount(() => {
    clearLayoutScrollRestore();
    removeLayoutScrollListener?.();
    if (layoutScrollSnapshotTimer) {
      window.clearInterval(layoutScrollSnapshotTimer);
      layoutScrollSnapshotTimer = null;
    }
    document.removeEventListener('scroll', handleLayoutScroll, true);
    window.removeEventListener('tabs-card:closed', handleClosedTabs);
    window.removeEventListener('resize', watchWidth);
    document.body.classList.remove('layout-sider-resizing');
  });

  onBeforeMount(async () => {
    // const crudMenuStore = useCrudMenu();
    // const { data } = await GetAllModelsInfo();
    // crudMenuStore.setCrudMenu(data || {});
  });
</script>

<style lang="less">
  .layout-side-drawer {
    background-color: rgb(0, 20, 40);

    .layout-sider {
      min-height: 100vh;
      box-shadow: 2px 0 8px 0 rgb(29 35 41 / 5%);
      position: relative;
      z-index: 13;
      transition: all 0.2s ease-in-out;
    }
  }

  // 自己添加的样式
  // 按钮条（关闭打开菜单用的）
  .n-layout-toggle-bar__top,
  .n-layout-toggle-bar__bottom {
    // background-color: #2d8cf0 !important;
    background-color: v-bind('themeVarsComputed.primaryColor') !important;
  }

  .n-layout-sider .n-layout-toggle-bar {
    right: -20px !important;
  }

  body.layout-sider-resizing {
    cursor: col-resize !important;
    user-select: none;
  }

  // header的高度自定义，然后后面的页面内容要跟着header的高度走
  .layout-header {
    height: 40px !important;
  }
  .layout-content-main,
  .layout-content-main-fix {
    padding-top: 40px !important;
  }

  // logo高度自定义
  .logo {
    height: 40px !important;
  }

  // 菜单栏的宽度自定义在\src\settings\projectSetting.ts里面定义
</style>
<style lang="less" scoped>
  // Root layout - horizontal flex for sider + main content
  .layout {
    display: flex;
    flex-direction: row;
    height: 100vh;
    overflow: hidden;

    &-default-background {
      background: #eeeeee;
    }

    .layout-sider {
      height: 100vh;
      box-shadow: 2px 0 8px 0 rgb(29 35 41 / 5%);
      position: relative;
      z-index: 13;
      transition: all 0.2s ease-in-out;
    }

    .layout-sider-resizer {
      position: absolute;
      top: 0;
      right: -3px;
      bottom: 0;
      z-index: 20;
      width: 6px;
      cursor: col-resize;
      background: transparent;
      transition: background-color 0.16s ease;

      &:hover {
        background-color: color-mix(
          in srgb,
          var(--app-primary-color, #18a058) 35%,
          transparent
        );
      }
    }

    .layout-sider-fix {
      position: fixed;
      top: 0;
      left: 0;
    }

    .ant-layout {
      overflow: hidden;
    }

    .layout-right-fix {
      overflow-x: hidden;
      padding-left: 200px;
      height: 100vh;
      transition: all 0.2s ease-in-out;
    }

    .n-layout-footer {
      background: none;
    }
  }

  // Right side wrapper - contains header + scrollable content
  .layout-right-wrapper {
    flex: 1;
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
  }

  .layout-right-header {
    flex-shrink: 0;
    height: 40px;
    z-index: 11;
  }

  .layout-right {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .layout-scroll-container {
    flex: 1;
    min-height: 0;
    height: 100%;
  }

  .content-wrapper {
    padding: 12px 20px 12px 12px;
    min-height: calc(100vh - 160px);
  }

  .noMultiTabs {
    padding-top: 0;
  }
</style>
