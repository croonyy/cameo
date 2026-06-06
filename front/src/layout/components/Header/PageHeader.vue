<template>
  <div class="layout-header" :class="inverted ? 'layout-header-dark' : 'layout-header-light'">
    <!--顶部菜单-->
    <div
      class="layout-header-left"
      v-if="navMode === 'horizontal' || (navMode === 'horizontal-mix' && mixMenu)"
    >
      <div class="logo header-logo" v-if="navMode === 'horizontal'">
        <img :src="websiteConfig.logo" alt="" />
        <h2 v-show="!headerMenuCollapsed" class="title">{{ websiteConfig.title }}</h2>
      </div>
      <AsideMenu
        class="header-menu"
        :collapsed="headerMenuCollapsed"
        v-model:location="getMenuLocation"
        :inverted="getInverted"
        mode="horizontal"
      />
    </div>
    <!--左侧菜单-->
    <div class="layout-header-left" v-else>
      <!-- 菜单收起 -->
      <div
        class="ml-1 layout-header-trigger layout-header-trigger-min"
        @click="handleMenuCollapsed"
      >
        <n-icon size="18" v-if="collapsed">
          <MenuUnfoldOutlined />
        </n-icon>
        <n-icon size="18" v-else>
          <MenuFoldOutlined />
        </n-icon>
      </div>
      <!-- 刷新 -->
      <div
        class="mr-1 layout-header-trigger layout-header-trigger-min"
        v-if="headerSetting.isReload"
        @click="reloadPage"
      >
        <n-icon size="18">
          <ReloadOutlined />
        </n-icon>
      </div>
      <!-- 面包屑 -->
      <n-breadcrumb v-if="crumbsSetting.show">
        <template
          v-for="routeItem in breadcrumbList"
          :key="routeItem.name === 'Redirect' ? void 0 : routeItem.name"
        >
          <n-breadcrumb-item v-if="routeItem.meta.title">
            <n-dropdown
              v-if="routeItem.children.length"
              :options="routeItem.children"
              @select="dropdownSelect"
            >
              <span class="link-text">
                <component
                  v-if="crumbsSetting.showIcon && routeItem.meta.icon"
                  :is="routeItem.meta.icon"
                />
                {{ routeItem.meta.title }}
              </span>
            </n-dropdown>
            <span class="link-text" v-else>
              <component
                v-if="crumbsSetting.showIcon && routeItem.meta.icon"
                :is="routeItem.meta.icon"
              />
              {{ routeItem.meta.title }}
            </span>
          </n-breadcrumb-item>
        </template>
      </n-breadcrumb>
    </div>
    <div class="layout-header-right">
      <div
        class="layout-header-trigger layout-header-trigger-min layout-header-action"
        v-for="item in iconList"
        :key="item.icon"
      >
        <n-tooltip placement="bottom">
          <template #trigger>
            <button
              type="button"
              class="layout-header-icon-button"
              :aria-label="item.tips"
              @click="item.eventObject?.click?.()"
            >
              <n-icon size="18">
                <component :is="item.icon" />
              </n-icon>
            </button>
          </template>
          <span>{{ item.tips }}</span>
        </n-tooltip>
      </div>
      <!--切换全屏-->
      <div class="layout-header-trigger layout-header-trigger-min layout-header-action">
        <n-tooltip placement="bottom">
          <template #trigger>
            <button
              type="button"
              class="layout-header-icon-button"
              aria-label="toggle fullscreen"
              @click="toggleFullScreen"
            >
              <n-icon size="18">
                <component :is="fullscreenIcon" />
              </n-icon>
            </button>
          </template>
          <span>{{ t('common.fullscreen') }}</span>
        </n-tooltip>
      </div>
      <!--语言切换-->
      <div class="layout-header-trigger layout-header-trigger-min layout-header-action">
        <n-tooltip placement="bottom">
          <template #trigger>
            <button
              type="button"
              class="layout-header-icon-button"
              :aria-label="languageSwitchLabel"
              @click="toggleLanguage"
            >
              <n-icon size="18">
                <TranslationOutlined />
              </n-icon>
            </button>
          </template>
          <span>{{ languageSwitchLabel }}</span>
        </n-tooltip>
      </div>
      <!-- 个人中心 -->
      <div class="layout-header-trigger layout-header-trigger-min layout-header-user">
        <!-- 已登录显示头像和下拉菜单 -->
        <n-dropdown
          v-if="tokenExists"
          trigger="hover"
          @select="avatarSelect"
          :options="avatarOptions"
        >
          <div class="avatar">
            <n-avatar :src="websiteConfig.logo">
              <template #icon>
                <UserOutlined />
              </template>
            </n-avatar>
            <n-divider vertical />
            <span class="avatar-name">{{ username }}</span>
          </div>
        </n-dropdown>
        <!-- 未登录显示登录按钮 -->
        <div v-else class="avatar">
          <n-button size="small" @click="$router.push({ name: 'Login' })">{{ t('common.login') }}</n-button>
        </div>
      </div>
      <!--设置-->
      <div
        class="layout-header-trigger layout-header-trigger-min layout-header-action"
        @click="openSetting"
      >
        <n-tooltip placement="bottom-end">
          <template #trigger>
            <n-icon size="18" style="font-weight: bold">
              <SettingOutlined />
            </n-icon>
          </template>
          <span>{{ t('settings.projectConfig') }}</span>
        </n-tooltip>
      </div>
    </div>
  </div>
  <!--项目配置-->
  <ProjectSetting ref="drawerSetting" />
</template>

<script lang="ts">
  import {
    defineComponent,
    reactive,
    toRefs,
    ref,
    computed,
    unref,
    nextTick,
    onBeforeUnmount,
  } from 'vue';
  import { useRouter, useRoute } from 'vue-router';
  import components from './components';
  import { NDialogProvider, useDialog, useMessage, useThemeVars } from 'naive-ui';
  import { TABS_ROUTES } from '@/store/mutation-types';
  import { useUserStore } from '@/store/modules/user';
  import { useScreenLockStore } from '@/store/modules/screenLock';
  import ProjectSetting from './ProjectSetting.vue';
  import AsideMenu from '@/layout/components/Menu/AsideMenu.vue';
  import { useProjectSetting } from '@/hooks/setting/useProjectSetting';
  import { websiteConfig } from '@/config/website.config';
  // import { useTabsViewStore } from '@/store/modules/tabsView';
  import { useAsyncRouteStore } from '@/store/modules/asyncRoute';
  import { useDesignSetting } from '@/hooks/setting/useDesignSetting';
  import { useCrudMenuStore } from '@/store/modules/crudMenu';
  import { CRUD_CREATE, CRUD_EDIT, CRUD_LIST } from '@/store/consts';
  import { getLanguage, setLanguage, t, type AppLanguage } from '@/i18n';

  const HEADER_MENU_COLLAPSED = false;
  const USER_SETTING_ROUTE_PARAMS = {
    app_name: 'udadmin',
    model_name: 'User',
  };
  const FULLSCREEN_CHANGE_EVENTS = [
    'fullscreenchange',
    'webkitfullscreenchange',
    'mozfullscreenchange',
    'MSFullscreenChange',
  ];
  export default defineComponent({
    name: 'PageHeader',
    components: { ...components, NDialogProvider, ProjectSetting, AsideMenu },
    props: {
      collapsed: {
        type: Boolean,
      },
      inverted: {
        type: Boolean,
      },
    },
    emits: ['update:collapsed'],
    setup(props, { emit }) {
      const { getDarkTheme, getAppTheme } = useDesignSetting();
      const themeVars = useThemeVars();
      const userStore = useUserStore();
      const useLockscreen = useScreenLockStore();
      const message = useMessage();
      const dialog = useDialog();
      const asyncRouteStore = useAsyncRouteStore();
      const crudMenuStore = useCrudMenuStore();
      const { navMode, navTheme, headerSetting, menuSetting, crumbsSetting } = useProjectSetting();

      const drawerSetting = ref();
      const currentLanguage = ref<AppLanguage>(getLanguage());

      const state = reactive({
        // tokenExists: userStore?.token ?? '',
        username: userStore?.info?.username ?? '',
        fullscreenIcon: 'FullscreenOutlined',
        navMode,
        navTheme,
        headerSetting,
        crumbsSetting,
      });

      const getBaseColor = computed(() => {
        return themeVars.value.cardColor;
      });

      // const tokenExists: userStore?.token ?? '',
      const tokenExists = computed(() => {
        return userStore?.token ?? '';
      });
      const getInverted = computed(() => {
        return ['light', 'header-dark'].includes(unref(navTheme))
          ? props.inverted
          : !props.inverted;
      });

      const mixMenu = computed(() => {
        return unref(menuSetting).mixMenu;
      });

      const headerMenuCollapsed = computed(() => {
        return HEADER_MENU_COLLAPSED;
      });

      const getChangeStyle = computed(() => {
        const { collapsed } = props;
        const { minMenuWidth, menuWidth } = unref(menuSetting);
        return {
          left: collapsed ? `${minMenuWidth}px` : `${menuWidth}px`,
          width: `calc(100% - ${collapsed ? `${minMenuWidth}px` : `${menuWidth}px`})`,
        };
      });

      const getMenuLocation = computed(() => {
        return 'header';
      });

      const targetLanguage = computed<AppLanguage>(() =>
        currentLanguage.value === 'zh-CN' ? 'en-US' : 'zh-CN'
      );
      const languageSwitchLabel = computed(() =>
        targetLanguage.value === 'en-US'
          ? t('settings.switchToEnglish')
          : t('settings.switchToChinese')
      );

      function toggleLanguage() {
        currentLanguage.value = setLanguage(targetLanguage.value);
        window.location.reload();
      }

      const router = useRouter();
      const route = useRoute();
      const crudBreadcrumbTypeTitle = computed(() => ({
        [CRUD_LIST]: t('crud.list'),
        [CRUD_EDIT]: t('crud.edit'),
        [CRUD_CREATE]: t('crud.create'),
      }));

      const getCrudModelTitle = (appName: any, modelName: any) => {
        const modelKey = `${appName}:${modelName}`;
        const allModels = (crudMenuStore.getCrudMenu as any)?.all_models || {};
        return allModels?.[modelKey]?.model_menu_name || modelName || modelKey;
      };

      const getBreadcrumbTitle = (item) => {
        const typeTitleMap = crudBreadcrumbTypeTitle.value;
        if (item.name !== route.name || !(item.meta?.type in typeTitleMap)) {
          return item.meta?.title;
        }

        const appName = route.params.app_name;
        const modelName = route.params.model_name;
        const modelTitle = getCrudModelTitle(appName, modelName);
        const id = route.params.id;
        const actionTitle = typeTitleMap[item.meta.type];

        return item.meta.type === CRUD_EDIT && id
          ? `${actionTitle}:${modelTitle} #${id}`
          : `${actionTitle}:${modelTitle}`;
      };

      const generator: any = (routerMap) => {
        return routerMap.map((item) => {
          const currentMenu = {
            ...item,
            meta: {
              ...item.meta,
              title: getBreadcrumbTitle(item),
            },
            label: getBreadcrumbTitle(item),
            key: item.name,
            disabled: item.path === '/',
          };
          // 是否有子菜单，并递归处理
          if (item.children && item.children.length > 0) {
            // Recursion
            currentMenu.children = generator(item.children, currentMenu);
          }
          return currentMenu;
        });
      };

      const breadcrumbList = computed(() => {
        return generator(route.matched);
      });

      const dropdownSelect = (key) => {
        router.push({ name: key });
      };

      // 刷新页面
      const reloadPage = () => {
        // 临时性将组件设置为非缓存
        let router_name = router.currentRoute.value.name;
        let is_alive =
          typeof router_name === 'string' &&
          asyncRouteStore.keepAliveComponents.includes(router_name);
        if (is_alive) {
          asyncRouteStore.keepAliveComponents = asyncRouteStore.keepAliveComponents.filter(
            (item) => item != router.currentRoute.value.name
          );
        }

        router
          .push({
            path: '/redirect' + unref(route).fullPath,
          })
          .then(() => {
            // 恢复组件缓存属性
            if (is_alive && typeof router_name === 'string') {
              nextTick(() => {
                asyncRouteStore.keepAliveComponents.push(router_name);
              });
            }
          });
      };

      // 退出登录
      const doLogout = () => {
        dialog.info({
          title: '提示',
          content: '您确定要退出登录吗',
          positiveText: '确定',
          negativeText: '取消',
          onPositiveClick: () => {
            userStore.logout().then(() => {
              message.success('成功退出登录');
              // 移除标签页
              localStorage.removeItem(TABS_ROUTES);
              router
                .replace({
                  name: 'Login',
                  query: {
                    redirect: route.fullPath,
                  },
                })
                // .finally(() => location.reload());
                .finally();
            });
          },
          onNegativeClick: () => {},
        });
      };

      // 切换全屏图标
      const getFullscreenElement = () => {
        const fullscreenDocument = document as Document & {
          webkitFullscreenElement?: Element | null;
          mozFullScreenElement?: Element | null;
          msFullscreenElement?: Element | null;
        };
        return (
          document.fullscreenElement ||
          fullscreenDocument.webkitFullscreenElement ||
          fullscreenDocument.mozFullScreenElement ||
          fullscreenDocument.msFullscreenElement ||
          null
        );
      };

      const requestFullscreen = () => {
        const fullscreenElement = document.documentElement as HTMLElement & {
          webkitRequestFullscreen?: () => Promise<void> | void;
          mozRequestFullScreen?: () => Promise<void> | void;
          msRequestFullscreen?: () => Promise<void> | void;
        };
        const request =
          fullscreenElement.requestFullscreen ||
          fullscreenElement.webkitRequestFullscreen ||
          fullscreenElement.mozRequestFullScreen ||
          fullscreenElement.msRequestFullscreen;

        if (!request) {
          return Promise.reject(new Error('Fullscreen API is not supported'));
        }
        return Promise.resolve(request.call(fullscreenElement));
      };

      const exitFullscreen = () => {
        const fullscreenDocument = document as Document & {
          webkitExitFullscreen?: () => Promise<void> | void;
          mozCancelFullScreen?: () => Promise<void> | void;
          msExitFullscreen?: () => Promise<void> | void;
        };
        const exit =
          document.exitFullscreen ||
          fullscreenDocument.webkitExitFullscreen ||
          fullscreenDocument.mozCancelFullScreen ||
          fullscreenDocument.msExitFullscreen;

        if (!exit) {
          return Promise.reject(new Error('Fullscreen API is not supported'));
        }
        return Promise.resolve(exit.call(document));
      };

      const toggleFullscreenIcon = () =>
        (state.fullscreenIcon =
          getFullscreenElement() !== null ? 'FullscreenExitOutlined' : 'FullscreenOutlined');

      const enterFullscreen = () => {
        if (!getFullscreenElement()) {
          requestFullscreen()
            .catch((error) => {
              console.warn('Failed to enter fullscreen:', error);
            })
            .finally(toggleFullscreenIcon);
        }
      };

      const leaveFullscreen = () => {
        if (getFullscreenElement()) {
          exitFullscreen()
            .catch((error) => {
              console.warn('Failed to exit native fullscreen:', error);
            })
            .finally(toggleFullscreenIcon);
          return;
        }
        toggleFullscreenIcon();
      };

      // 监听全屏切换事件
      FULLSCREEN_CHANGE_EVENTS.forEach((eventName) => {
        document.addEventListener(eventName, toggleFullscreenIcon);
      });
      onBeforeUnmount(() => {
        FULLSCREEN_CHANGE_EVENTS.forEach((eventName) => {
          document.removeEventListener(eventName, toggleFullscreenIcon);
        });
      });

      // 全屏切换
      const toggleFullScreen = () => {
        if (getFullscreenElement()) {
          leaveFullscreen();
        } else {
          enterFullscreen();
        }
      };

      // 图标列表
      const iconList = [
        {
          icon: 'SearchOutlined',
          tips: t('button.search'),
        },
        {
          icon: 'GithubOutlined',
          tips: 'github',
          eventObject: {
            click: () => window.open('https://github.com/croonyy/cameo', '_blank'),
          },
        },
        {
          icon: 'LockOutlined',
          tips: t('settings.lockScreen'),
          eventObject: {
            click: () => useLockscreen.setLock(true),
          },
        },
      ];
      const avatarOptions = [
        {
          label: t('settings.profile'),
          key: 1,
        },
        {
          label: t('settings.logout'),
          key: 2,
        },
      ];

      //头像下拉菜单
      const avatarSelect = (key) => {
        switch (key) {
          case 1:
            openUserSetting();
            break;
          case 2:
            doLogout();
            break;
        }
      };

      async function openUserSetting() {
        let userInfo = userStore.getUserInfo || {};
        if (userInfo?.id == null) {
          userInfo = await userStore.getInfo();
        }
        if (userInfo?.id == null) {
          message.warning(t('settings.currentUserMissing'));
          return;
        }
        router.push({
          name: CRUD_EDIT,
          params: {
            ...USER_SETTING_ROUTE_PARAMS,
            id: userInfo.id,
          },
        });
      }

      function openSetting() {
        const { openDrawer } = drawerSetting.value;
        openDrawer();
      }

      function handleMenuCollapsed() {
        emit('update:collapsed', !props.collapsed);
      }

      return {
        ...toRefs(state),
        iconList,
        toggleFullScreen,
        doLogout,
        route,
        dropdownSelect,
        avatarOptions,
        getChangeStyle,
        avatarSelect,
        breadcrumbList,
        reloadPage,
        drawerSetting,
        openSetting,
        languageSwitchLabel,
        toggleLanguage,
        getInverted,
        headerMenuCollapsed,
        getMenuLocation,
        mixMenu,
        websiteConfig,
        handleMenuCollapsed,
        tokenExists,
        getAppTheme,
        getDarkTheme,
        getBaseColor,
        t,
      };
    },
  });
</script>

<style lang="less" scoped>
  .layout-header {
    background-color: v-bind(getBaseColor);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0;
    height: 40px;
    box-shadow: 0 1px 4px rgb(0 21 41 / 8%);
    transition: all 0.2s ease-in-out;
    width: 100%;
    z-index: 11;

    &-left {
      display: flex;
      align-items: center;
      flex: 1 1 auto;
      min-width: 0;

      .logo {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 40px;
        line-height: 40px;
        overflow: hidden;
        white-space: nowrap;
        padding-left: 10px;

        img {
          width: auto;
          height: 32px;
          margin-right: 10px;
        }

        .title {
          margin-bottom: 0;
        }
      }

      .header-logo {
        flex: 0 0 auto;
        min-width: 108px;
        padding-right: 14px;
        overflow: visible;

        img {
          flex: 0 0 auto;
        }

        .title {
          flex: 0 0 auto;
          line-height: 40px;
        }
      }

      .header-menu {
        flex: 1 1 auto;
        min-width: 0;
      }

      ::v-deep(.ant-breadcrumb span:last-child .link-text) {
        color: #515a6e;
      }

      .n-breadcrumb {
        display: inline-block;
      }

      &-menu {
        color: var(--text-color);
      }
    }

    &-right {
      display: flex;
      align-items: center;
      flex: 0 0 auto;
      gap: 4px;
      height: 40px;
      padding: 0 10px 0 6px;
      margin-right: 4px;

      .avatar {
        display: flex;
        align-items: center;
        gap: 6px;
        height: 32px;
        padding: 0 15px;
        border-radius: var(--radius-sm);
        transition: background-color 0.18s ease, box-shadow 0.18s ease;

        &:hover {
          background: color-mix(in srgb, var(--app-primary-color, #18a058) 10%, transparent);
        }

        img {
          pointer-events: none;
        }
      }

      > * {
        cursor: pointer;
      }

      .layout-header-trigger {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 34px;
        padding: 0;
        border-radius: var(--radius-sm);
        color: color-mix(in srgb, currentColor 82%, transparent);
        transition: color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease,
          transform 0.18s ease;

        &:hover {
          color: var(--app-primary-color, #18a058);
          background: color-mix(in srgb, var(--app-primary-color, #18a058) 12%, transparent);
          box-shadow: inset 0 0 0 1px
            color-mix(in srgb, var(--app-primary-color, #18a058) 18%, transparent);
        }

        &:active {
          transform: scale(0.96);
        }

        .n-icon {
          height: 34px;
          line-height: 34px;
        }
      }

      .layout-header-action {
        flex: 0 0 34px;
        width: 34px;
        overflow: hidden;
      }

      .layout-header-user {
        flex: 0 0 auto;
        width: auto;
        max-width: 196px;
        overflow: visible;

        .avatar {
          max-width: 196px;
          overflow: visible;
          white-space: nowrap;
        }

        :deep(.n-avatar) {
          flex: 0 0 auto;
          overflow: visible;
        }

        .n-divider {
          flex: 0 0 auto;
          margin: 0 2px;
        }

        .avatar-name {
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      }
    }

    &-trigger {
      display: inline-block;
      width: 40px;
      // height: 40px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s ease-in-out;

      .n-icon {
        display: flex;
        align-items: center;
        height: 40px;
        line-height: 40px;
      }

      &:hover {
        background: hsla(0, 0%, 100%, 0.08);
      }

      .anticon {
        font-size: 16px;
        color: #515a6e;
      }
    }

    &-trigger-min {
      width: auto;
      padding: 0 12px;
    }

    &-icon-button {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 34px;
      height: 34px;
      padding: 0;
      margin: 0;
      color: inherit;
      cursor: pointer;
      background: transparent;
      border: 0;
      outline: 0;
      border-radius: inherit;

      .n-icon {
        height: 34px;
        line-height: 34px;
      }
    }
  }

  .layout-header-light {
    background: #fff;
    color: #515a6e;

    .n-icon {
      color: #515a6e;
    }

    .layout-header-left {
      ::v-deep(.n-breadcrumb .n-breadcrumb-item:last-child .n-breadcrumb-item__link) {
        color: #515a6e;
      }
    }

    .layout-header-trigger {
      &:hover {
        background: #f8f8f9;
      }
    }
  }

  .layout-header-dark {
    background: #001529;
    color: rgba(255, 255, 255, 0.86);

    .n-icon {
      color: rgba(255, 255, 255, 0.86);
    }

    .layout-header-left {
      ::v-deep(.n-breadcrumb .n-breadcrumb-item__link),
      ::v-deep(.n-breadcrumb .n-breadcrumb-item__separator) {
        color: rgba(255, 255, 255, 0.72);
      }

      ::v-deep(.n-breadcrumb .n-breadcrumb-item:last-child .n-breadcrumb-item__link) {
        color: rgba(255, 255, 255, 0.92);
      }
    }

    .layout-header-trigger {
      &:hover {
        background: rgba(255, 255, 255, 0.12);
      }
    }

    .layout-header-right {
      .layout-header-trigger:hover,
      .avatar:hover {
        background: rgba(255, 255, 255, 0.12);
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
      }
    }
  }

  .layout-header-fix {
    position: fixed;
    top: 0;
    right: 0;
    left: 200px;
    z-index: 11;
  }

  //::v-deep(.menu-router-link) {
  //  color: #515a6e;
  //
  //  &:hover {
  //    color: #1890ff;
  //  }
  //}
  :global(.n-dropdown-menu .n-dropdown-option .n-dropdown-option-body::before) {
    top: 2px !important;
    bottom: 2px !important;
  }
</style>
