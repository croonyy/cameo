<template>
  <div
    class="box-border tabs-view"
    :class="{
      'tabs-view-fix': multiTabsSetting.fixed,
      'tabs-view-default-background': getDarkTheme === false,
      'tabs-view-dark-background': getDarkTheme === true,
    }"
    :style="getChangeStyle"
  >
    <div class="tabs-view-main">
      <div ref="navWrap" class="tabs-card" :class="{ 'tabs-card-scrollable': scrollable }">
        <span
          class="tabs-card-prev"
          :class="{ 'tabs-card-prev-hide': !scrollable }"
          @click="scrollPrev"
        >
          <n-icon size="16" color="#515a6e">
            <LeftOutlined />
          </n-icon>
        </span>
        <span
          class="tabs-card-next"
          :class="{ 'tabs-card-next-hide': !scrollable }"
          @click="scrollNext"
        >
          <n-icon size="16" color="#515a6e">
            <RightOutlined />
          </n-icon>
        </span>
        <div ref="navScroll" class="tabs-card-scroll">
          <Draggable :list="tabsList" animation="300" item-key="fullPath" class="flex">
            <!-- element 是当前路由对象 -->
            <template #item="{ element }">
              <div
                :id="`tag${element.fullPath.split('/').join('\/')}`"
                class="tabs-card-scroll-item"
                :class="{ 'active-item': activeKey === element.fullPath }"
                @click.stop="goPage(element)"
                @contextmenu="handleContextMenu($event, element)"
              >
                <!-- <span>{{ element.meta.title }}</span> -->
                <span>{{ getTabTitle(element) }}</span>
                <n-icon size="14" @click.stop="closeTabItem(element)" v-if="!element.meta.affix">
                  <CloseOutlined />
                </n-icon>
              </div>
            </template>
          </Draggable>
        </div>
      </div>
      <div class="tabs-close">
        <n-dropdown
          trigger="hover"
          @select="closeHandleSelect"
          placement="bottom-end"
          :options="TabsMenuOptions"
        >
          <div class="tabs-close-btn">
            <n-icon size="16" color="#515a6e">
              <DownOutlined />
            </n-icon>
          </div>
        </n-dropdown>
      </div>
      <!-- <n-dropdown
        :show="showDropdown"
        :x="dropdownX"
        :y="dropdownY"
        @clickoutside="onClickOutside"
        placement="bottom-start"
        @select="closeHandleSelect"
        :options="TabsMenuOptions"
      /> -->
    </div>
  </div>
</template>

<script lang="ts">
  import {
    defineComponent,
    reactive,
    computed,
    ref,
    toRefs,
    provide,
    watch,
    onMounted,
    nextTick,
  } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { storage } from '@/utils/Storage';
  import { TABS_ROUTES } from '@/store/mutation-types';
  import { useTabsViewStore } from '@/store/modules/tabsView';
  import { useAsyncRouteStore } from '@/store/modules/asyncRoute';
  import { RouteItem } from '@/store/modules/tabsView';
  import { useProjectSetting } from '@/hooks/setting/useProjectSetting';
  import { useMessage } from 'naive-ui';
  import Draggable from 'vuedraggable';
  import { PageEnum } from '@/enums/pageEnum';
  import {
    DownOutlined,
    ReloadOutlined,
    CloseOutlined,
    ColumnWidthOutlined,
    MinusOutlined,
    LeftOutlined,
    RightOutlined,
  } from '@vicons/antd';
  import { renderIcon } from '@/utils';
  import elementResizeDetectorMaker from 'element-resize-detector';
  import { useDesignSetting } from '@/hooks/setting/useDesignSetting';
  import { useProjectSettingStore } from '@/store/modules/projectSetting';
  import { useThemeVars } from 'naive-ui';
  import { useGo } from '@/hooks/web/usePage';
  import { useCrudMenu } from '@/store/modules/crudMenu';
  import { CRUD_LIST, CRUD_EDIT, CRUD_CREATE } from '@/store/consts';
  import { RedirectName } from '@/router/constant';
  import { t } from '@/i18n';

  export default defineComponent({
    name: 'TabsView',
    components: {
      DownOutlined,
      CloseOutlined,
      LeftOutlined,
      RightOutlined,
      Draggable,
    },
    props: {
      collapsed: {
        type: Boolean,
      },
    },
    setup(props) {
      const { getDarkTheme, getAppTheme } = useDesignSetting();
      const { navMode, headerSetting, menuSetting, multiTabsSetting, isMobile } =
        useProjectSetting();
      const settingStore = useProjectSettingStore();
      const crudMenuStore = useCrudMenu();
      const crud_menus = ref({});

      const message = useMessage();
      const route = useRoute();
      const router = useRouter();
      const tabsViewStore = useTabsViewStore();
      const asyncRouteStore = useAsyncRouteStore();
      const navScroll: any = ref(null);
      const navWrap: any = ref(null);
      const isCurrent = ref(false);
      const go = useGo();
      const themeVars = useThemeVars();
      const getCardColor = computed(() => {
        return themeVars.value.cardColor;
      });
      const crud_type = [CRUD_LIST, CRUD_EDIT, CRUD_CREATE];
      const crudTabType = {
        [CRUD_LIST]: () => t('crud.list'),
        [CRUD_EDIT]: () => t('crud.edit'),
        [CRUD_CREATE]: () => t('crud.create'),
      };
      const getTabTitle = (r: any) => {
        // 自己定义的路由的tab title名字处理
        // return r.meta?.title;
        // if (crud_type.includes(r.meta?.type)) {
        if (r.meta?.type in crudTabType) {
          const appName = r.params.app_name;
          const modelName = r.params.model_name;
          const all_models = crud_menus.value?.['all_models'] || {};
          const actionTitle = crudTabType[r.meta?.type]?.() || r.meta?.type;
          const modelTitle =
            all_models?.[`${appName}:${modelName}`]?.['model_menu_name'] ||
            `${appName}:${modelName}`;
          return `${actionTitle}:${modelTitle}`;
        } else {
          return r.meta.title;
        }
      };

      const getBaseColor = computed(() => {
        return themeVars.value.textColor1;
      });

      const state = reactive({
        activeKey: route.fullPath,
        scrollable: false,
        dropdownX: 0,
        dropdownY: 0,
        showDropdown: false,
        isMultiHeaderFixed: false,
        multiTabsSetting: multiTabsSetting,
      });

      // 获取简易的路由对象
      const getSimpleRoute = (route): RouteItem => {
        const { fullPath, hash, meta, name, params, path, query } = route;
        return { fullPath, hash, meta, name, params, path, query };
      };

      const isMixMenuNoneSub = computed(() => {
        const mixMenu = settingStore.menuSetting.mixMenu;
        const currentRoute = useRoute();
        if (navMode.value != 'horizontal-mix') return true;
        return !(navMode.value === 'horizontal-mix' && mixMenu && currentRoute.meta.isRoot);
      });

      //动态组装样式 菜单缩进
      const getChangeStyle = computed(() => {
        return {
          width: '100%',
          padding: '4px',
        };
      });
      // console.log('getChangeStyle', getChangeStyle.value);

      //tags 右侧下拉菜单
      const TabsMenuOptions = computed(() => {
        const isDisabled = tabsList.value.length <= 1;
        return [
          {
            label: t('tabs.refreshCurrent'),
            key: '1',
            icon: renderIcon(ReloadOutlined),
          },
          {
            label: t('tabs.closeCurrent'),
            key: '2',
            disabled: isCurrent.value || isDisabled,
            icon: renderIcon(CloseOutlined),
          },
          {
            label: t('tabs.closeOthers'),
            key: '3',
            disabled: isDisabled,
            icon: renderIcon(ColumnWidthOutlined),
          },
          {
            label: t('tabs.closeAll'),
            key: '4',
            disabled: isDisabled,
            icon: renderIcon(MinusOutlined),
          },
        ];
      });

      // 初始化CRUD菜单数据
      async function initCrudMenuData() {
        await crudMenuStore.initCrudMenu();
        crud_menus.value = crudMenuStore.getCrudMenu;
        // console.log('CRUD菜单数据已初始化:', crud_menus.value);
      }

      // 处理缓存的路由
      async function processCacheRoutes() {
        // 获取缓存的路由
        let cacheRoutes: RouteItem[] = [];
        const modCacheRoutes: RouteItem[] = [];
        const simpleRoute = getSimpleRoute(route);

        // 从本地存储中读取缓存的路由
        try {
          const routesStr = storage.get(TABS_ROUTES) as string | null | undefined;
          cacheRoutes = routesStr ? JSON.parse(routesStr) : [simpleRoute];
        } catch (e) {
          console.warn('解析缓存路由失败，使用默认路由', e);
          cacheRoutes = [simpleRoute];
        }

        // 获取当前所有路由
        const routes = router.getRoutes();

        // 处理缓存的路由
        cacheRoutes.forEach((cacheRoute) => {
          const matchedRoute = routes.find((route) => route.path === cacheRoute.path);
          if (matchedRoute) {
            cacheRoute.meta = matchedRoute.meta || cacheRoute.meta;
            cacheRoute.name = (matchedRoute.name || cacheRoute.name) as string;
            modCacheRoutes.push(cacheRoute);
          }

          // 处理CRUD类型的路由
          if (crud_type.includes(cacheRoute?.meta?.type as string)) {
            const appName = cacheRoute?.params?.app_name as string;
            const modelName = cacheRoute?.params?.model_name as string;

            // 检查模型是否在允许的模型列表中
            const models = crud_menus.value?.['all_models'];
            if (`${appName}:${modelName}` in models) {
              modCacheRoutes.push(cacheRoute);
            } else {
              console.log(`Model ${modelName} in app ${appName} is not allowed, skipping tab`);
            }
          }
        });

        // 初始化标签页
        // console.log('处理后的路由数量:', modCacheRoutes.length);
        tabsViewStore.initTabs(modCacheRoutes);
      }

      //监听滚动条
      function onScroll(e) {
        let scrollTop =
          e.target.scrollTop ||
          document.documentElement.scrollTop ||
          window.pageYOffset ||
          document.body.scrollTop; // 滚动条偏移量
        state.isMultiHeaderFixed = !!(
          !headerSetting.value.fixed &&
          multiTabsSetting.value.fixed &&
          scrollTop >= 64
        );
      }

      window.addEventListener('scroll', onScroll, true);

      // 移除缓存组件名称
      const getKeepAliveCompName = (tabRoute: any): string | undefined => {
        if (!tabRoute?.meta?.keepAlive) return undefined;
        const matchedRoute = router
          .getRoutes()
          .find((item) => item.name == tabRoute.name || item.path == tabRoute.path);
        const component = matchedRoute?.components?.default as any;
        return component?.name || (tabRoute.name ? String(tabRoute.name) : undefined);
      };

      // 标签页列表
      const tabsList: any = computed(() => tabsViewStore.tabsList);
      const notifyClosedKeepAliveTabs = (closedRoutes: any[]) => {
        const fullPaths = closedRoutes.map((item) => item?.fullPath).filter(Boolean);
        if (!fullPaths.length) return;
        window.dispatchEvent(
          new CustomEvent('tabs-card:closed', {
            detail: {
              fullPaths,
            },
          })
        );
      };

      const syncKeepAliveAfterClose = (closedRoutes: any[]) => {
        if (!closedRoutes.length) return;
        notifyClosedKeepAliveTabs(closedRoutes);
      };

      const refreshKeepAliveRoute = (targetRoute: any) => {
        const name = getKeepAliveCompName(targetRoute);
        if (!name) return;
        asyncRouteStore.setKeepAliveComponents(
          asyncRouteStore.keepAliveComponents.filter((item) => item != name)
        );
      };
      const whiteList: string[] = [
        PageEnum.BASE_LOGIN_NAME,
        PageEnum.REDIRECT_NAME,
        PageEnum.ERROR_PAGE_NAME,
      ];

      watch(
        () => route.fullPath,
        (to, from) => {
          if (whiteList.includes(route.name as string)) return;
          state.activeKey = to;
          // udmod  2023-05-05 当路由是重定向组件时，不添加到标签页列表
          if (route.name != `${RedirectName}Son`) {
            tabsViewStore.addTab(getSimpleRoute(route), from);
          }
          updateNavScroll(true);
        },
        { immediate: true }
      );

      watch(
        () => route.fullPath,
        async (fullPath) => {
          await nextTick();
          restoreActivePageScroll(fullPath);
        },
        { flush: 'post' }
      );

      // 在页面关闭或刷新之前，保存数据
      window.addEventListener('beforeunload', () => {
        storage.set(TABS_ROUTES, JSON.stringify(tabsList.value));
      });

      // 关闭当前页面
      const removeTab = (route) => {
        if (tabsList.value.length === 1) {
          return message.warning(t('tabs.lastPageWarning'));
        }
        tabsViewStore.closeCurrentTab(route);
        syncKeepAliveAfterClose([route]);
        // 如果关闭的是当前页
        if (state.activeKey === route.fullPath) {
          const currentRoute = tabsList.value[Math.max(0, tabsList.value.length - 1)];
          state.activeKey = currentRoute.fullPath;
          router.push(currentRoute);
        }
        updateNavScroll();
      };

      // 刷新页面
      const reloadPage = () => {
        refreshKeepAliveRoute(route);
        router.push({
          path: '/redirect' + route.fullPath,
        });
      };

      // 注入刷新页面方法
      provide('reloadPage', reloadPage);

      // 关闭左侧
      const closeLeft = (route) => {
        const currentIndex = tabsList.value.findIndex((tab) => tab.fullPath == route.fullPath);
        const closedRoutes = tabsList.value.filter(
          (item, index) => index < currentIndex && !(item?.meta?.affix ?? false)
        );
        tabsViewStore.closeLeftTabs(route);
        syncKeepAliveAfterClose(closedRoutes);
        state.activeKey = route.fullPath;
        router.replace(route.fullPath);
        updateNavScroll();
      };

      // 关闭右侧
      const closeRight = (route) => {
        const currentIndex = tabsList.value.findIndex((tab) => tab.fullPath == route.fullPath);
        const closedRoutes = tabsList.value.filter(
          (item, index) => index > currentIndex && !(item?.meta?.affix ?? false)
        );
        tabsViewStore.closeRightTabs(route);
        syncKeepAliveAfterClose(closedRoutes);
        state.activeKey = route.fullPath;
        router.replace(route.fullPath);
        updateNavScroll();
      };

      // 关闭其他
      const closeOther = (route) => {
        const closedRoutes = tabsList.value.filter(
          (item) => item.fullPath != route.fullPath && !(item?.meta?.affix ?? false)
        );
        tabsViewStore.closeOtherTabs(route);
        syncKeepAliveAfterClose(closedRoutes);
        state.activeKey = route.fullPath;
        router.replace(route.fullPath);
        updateNavScroll();
      };

      // 关闭全部
      const closeAll = () => {
        const closedRoutes = tabsList.value.filter((item) => !(item?.meta?.affix ?? false));
        tabsViewStore.closeAllTabs();
        syncKeepAliveAfterClose(closedRoutes);
        router.replace(PageEnum.BASE_HOME);
        updateNavScroll();
      };

      //tab 操作
      const closeHandleSelect = (key) => {
        switch (key) {
          //刷新
          case '1':
            reloadPage();
            break;
          //关闭
          case '2':
            removeTab(route);
            break;
          //关闭其他
          case '3':
            closeOther(route);
            break;
          //关闭所有
          case '4':
            closeAll();
            break;
        }
        updateNavScroll();
        state.showDropdown = false;
      };

      /**
       * @param value 要滚动到的位置
       * @param amplitude 每次滚动的长度
       */
      function scrollTo(value: number, amplitude: number) {
        const currentScroll = navScroll.value.scrollLeft;
        const scrollWidth =
          (amplitude > 0 && currentScroll + amplitude >= value) ||
          (amplitude < 0 && currentScroll + amplitude <= value)
            ? value
            : currentScroll + amplitude;
        navScroll.value && navScroll.value.scrollTo(scrollWidth, 0);
        if (scrollWidth === value) return;
        return window.requestAnimationFrame(() => scrollTo(value, amplitude));
      }

      function scrollPrev() {
        const containerWidth = navScroll.value.offsetWidth;
        const currentScroll = navScroll.value.scrollLeft;

        if (!currentScroll) return;
        const scrollLeft = currentScroll > containerWidth ? currentScroll - containerWidth : 0;
        scrollTo(scrollLeft, (scrollLeft - currentScroll) / 20);
      }

      function scrollNext() {
        const containerWidth = navScroll.value.offsetWidth;
        const navWidth = navScroll.value.scrollWidth;
        const currentScroll = navScroll.value.scrollLeft;

        if (navWidth - currentScroll <= containerWidth) return;
        const scrollLeft =
          navWidth - currentScroll > containerWidth * 2
            ? currentScroll + containerWidth
            : navWidth - containerWidth;
        scrollTo(scrollLeft, (scrollLeft - currentScroll) / 20);
      }

      function scrollActiveTabIntoNav() {
        const scrollContainer = navScroll.value as HTMLElement | null;
        if (!scrollContainer) return;

        const tagList = scrollContainer.querySelectorAll('.tabs-card-scroll-item') || [];
        const activeTag = [...tagList].find(
          (tag: Element) => tag.id === `tag${state.activeKey.split('/').join('\/')}`
        ) as HTMLElement | undefined;
        if (!activeTag) return;

        const currentScroll = scrollContainer.scrollLeft;
        const containerWidth = scrollContainer.clientWidth;
        const tagLeft = activeTag.offsetLeft;
        const tagRight = tagLeft + activeTag.offsetWidth;
        const visibleLeft = currentScroll;
        const visibleRight = currentScroll + containerWidth;
        const gap = 8;

        if (tagLeft < visibleLeft) {
          scrollTo(Math.max(tagLeft - gap, 0), (tagLeft - gap - currentScroll) / 20);
        } else if (tagRight > visibleRight) {
          const target = Math.min(
            tagRight - containerWidth + gap,
            scrollContainer.scrollWidth - containerWidth
          );
          scrollTo(target, (target - currentScroll) / 20);
        }
      }

      /**
       * @param autoScroll 是否开启自动滚动功能
       */
      async function updateNavScroll(autoScroll?: boolean) {
        await nextTick();
        if (!navScroll.value) return;
        const containerWidth = navScroll.value.offsetWidth;
        const navWidth = navScroll.value.scrollWidth;

        if (containerWidth < navWidth) {
          state.scrollable = true;
          if (autoScroll) {
            scrollActiveTabIntoNav();
          }
        } else {
          state.scrollable = false;
        }
      }

      function readScrollPosition(key: string) {
        const rawValue = sessionStorage.getItem(key);
        if (!rawValue) return null;
        try {
          return JSON.parse(rawValue);
        } catch {
          sessionStorage.removeItem(key);
          return null;
        }
      }

      function getStoredPageScroll(fullPath: string) {
        return readScrollPosition(`layout:scroll:${fullPath}`);
      }

      function getActiveCrudPageScrollElement() {
        const root = document.querySelector<HTMLElement>('.crud-list-wrapper, .edit-container');
        const candidates = Array.from(
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
          );
        return candidates[0] || null;
      }

      function restoreActivePageScroll(fullPath: string) {
        const pagePosition = getStoredPageScroll(fullPath);
        if (!pagePosition) return;

        const apply = () => {
          const pageScrollEl = getActiveCrudPageScrollElement();
          if (pageScrollEl && pagePosition) {
            if (pageScrollEl.scrollHeight > pageScrollEl.clientHeight) {
              pageScrollEl.scrollTop = pagePosition.top || 0;
            }
            if (pageScrollEl.scrollWidth > pageScrollEl.clientWidth) {
              pageScrollEl.scrollLeft = pagePosition.left || 0;
            }
          }
        };

        requestAnimationFrame(() => {
          apply();
          requestAnimationFrame(apply);
        });
        [80, 200, 500, 900, 1400, 2200, 3200, 4500].forEach((delay) =>
          window.setTimeout(apply, delay)
        );
      }

      function handleResize() {
        updateNavScroll(true);
      }

      function handleContextMenu(e, item) {
        e.preventDefault();
        isCurrent.value = PageEnum.BASE_HOME_REDIRECT === item.path;
        state.showDropdown = false;
        nextTick().then(() => {
          state.showDropdown = true;
          state.dropdownX = e.clientX;
          state.dropdownY = e.clientY;
        });
      }

      function onClickOutside() {
        state.showDropdown = false;
      }

      //tags 跳转页面
      function goPage(e) {
        const { fullPath } = e;
        if (fullPath === route.fullPath) return;
        window.dispatchEvent(
          new CustomEvent('tabs-card:before-switch', {
            detail: {
              fromFullPath: route.fullPath,
              toFullPath: fullPath,
            },
          })
        );
        state.activeKey = fullPath;
        go(e, true);
        [0, 120, 300].forEach((delay) => {
          window.setTimeout(() => {
            restoreActivePageScroll(fullPath);
            window.dispatchEvent(
              new CustomEvent('tabs-card:after-switch', {
                detail: {
                  fromFullPath: route.fullPath,
                  toFullPath: fullPath,
                },
              })
            );
          }, delay);
        });
      }

      //删除tab
      function closeTabItem(e) {
        const { fullPath } = e;
        const routeInfo = tabsList.value.find((item) => item.fullPath == fullPath);
        removeTab(routeInfo);
      }

      onMounted(async () => {
        // 先初始化CRUD菜单数据
        await initCrudMenuData();
        // 然后处理缓存的路由
        await processCacheRoutes();
        // 最后设置元素大小监听
        onElementResize();
      });

      function onElementResize() {
        let observer;
        observer = elementResizeDetectorMaker();
        observer.listenTo(navWrap.value, handleResize);
      }

      return {
        ...toRefs(state),
        navWrap,
        navScroll,
        route,
        tabsList,
        goPage,
        closeTabItem,
        closeLeft,
        closeRight,
        closeOther,
        closeAll,
        reloadPage,
        getChangeStyle,
        TabsMenuOptions,
        closeHandleSelect,
        scrollNext,
        scrollPrev,
        handleContextMenu,
        onClickOutside,
        getDarkTheme,
        getAppTheme,
        getCardColor,
        getBaseColor,
        getTabTitle,
      };
    },
  });
</script>

<style lang="less" scoped>
  .tabs-view {
    width: 100%;
    padding: 6px 0;
    display: flex;
    transition: all 0.2s ease-in-out;
    box-shadow: 0px 4px 5px 0px #0001;

    &-main {
      height: 32px;
      display: flex;
      max-width: 100%;
      min-width: 100%;

      .tabs-card {
        -webkit-box-flex: 1;
        flex-grow: 1;
        flex-shrink: 1;
        overflow: hidden;
        position: relative;

        .tabs-card-prev,
        .tabs-card-next {
          width: 32px;
          text-align: center;
          position: absolute;
          line-height: 32px;
          cursor: pointer;

          .n-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 32px;
            width: 32px;
          }
        }

        .tabs-card-prev {
          left: 0;
        }

        .tabs-card-next {
          right: 0;
        }

        .tabs-card-next-hide,
        .tabs-card-prev-hide {
          display: none;
        }

        &-scroll {
          white-space: nowrap;
          overflow: hidden;

          &-item {
            background: v-bind(getCardColor);
            color: v-bind(getBaseColor);
            height: 32px;
            padding: 6px 16px 4px;
            border-radius: var(--radius-sm);
            // border: var(--common-border);
            margin-right: 6px;
            cursor: pointer;
            display: inline-block;
            position: relative;
            flex: 0 0 auto;
            // box-shadow: inset 0 0 0 1px color-mix(in srgb, v-bind(getBaseColor) 80%, transparent);
            box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.15);

            span {
              float: left;
              vertical-align: middle;
            }

            &:hover {
              color: #ffffff;
              background-color: color-mix(in srgb, v-bind(getAppTheme) 60%, transparent);
            }
            /* 🔥 按住左键（active）：强制保持样式，不变白 */
            &:active {
              color: #ffffff !important;
              background-color: color-mix(in srgb, v-bind(getAppTheme) 40%, transparent) !important;
            }

            .n-icon {
              height: 22px;
              width: 21px;
              margin-right: -6px;
              position: relative;
              vertical-align: middle;
              text-align: center;
              color: #808695;

              &:hover {
                color: #ffffff;
              }

              svg {
                height: 21px;
                display: inline-block;
              }
            }
          }

          .active-item {
            color: #ffffff;
            background-color: color-mix(in srgb, v-bind(getAppTheme) 100%, transparent);

            .n-icon {
              color: rgba(255, 255, 255, 0.82);

              &:hover {
                color: #ffffff;
              }
            }

            &:hover {
              color: #ffffff;
              background-color: color-mix(in srgb, v-bind(getAppTheme) 100%, transparent);
            }
            /* 🔥 按住左键（active）：强制保持样式，不变白 */
            &:active {
              color: #ffffff !important;
              background-color: color-mix(in srgb, v-bind(getAppTheme) 60%, transparent) !important;
            }
          }
        }
      }

      .tabs-card-scrollable {
        padding: 0 32px;
        overflow: hidden;
      }
    }

    .tabs-close {
      min-width: 32px;
      width: 32px;
      height: 32px;
      line-height: 32px;
      text-align: center;
      background: var(--color);
      border-radius: 2px;
      cursor: pointer;

      &-btn {
        color: var(--color);
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
  }

  .tabs-view-default-background {
    background: rgba(var(--n-color-focus), 0.2);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
  }

  .tabs-view-dark-background {
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
  }

  .tabs-view-fix {
    flex: 0 0 auto;
    z-index: 5;
  }

  // .tabs-card-scroll {
  //   border: 2px solid red;
  // }
  // .tabs-card-scroll-item {
  //   background: v-bind(getBaseColor) !important;
  // }
  :global(.n-dropdown-menu .n-dropdown-option .n-dropdown-option-body::before) {
    top: 2px !important;
    bottom: 2px !important;
  }
</style>
