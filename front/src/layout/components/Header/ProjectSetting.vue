<template>
  <n-drawer v-model:show="isDrawer" :width="width" :placement="placement">
    <n-drawer-content :title="drawerTitle" :native-scrollbar="false">
      <div class="drawer">
        <n-divider title-placement="center">{{ t('settings.theme') }}</n-divider>

        <div class="justify-center drawer-setting-item dark-switch">
          <n-tooltip placement="bottom">
            <template #trigger>
              <n-switch v-model:value="designStore.darkTheme" class="dark-theme-switch">
                <template #checked>
                  <n-icon size="14" color="#ffd93b">
                    <SunnySharp />
                  </n-icon>
                </template>
                <template #unchecked>
                  <n-icon size="14" color="#ffd93b">
                    <Moon />
                  </n-icon>
                </template>
              </n-switch>
            </template>
            <span>{{
              designStore.darkTheme ? t('settings.darkTheme') : t('settings.lightTheme')
            }}</span>
          </n-tooltip>
        </div>

        <n-divider title-placement="center">{{ t('settings.systemTheme') }}</n-divider>

        <div class="drawer-setting-item align-items-top">
          <span
            class="theme-item"
            v-for="(item, index) in appThemeList"
            :key="index"
            :style="{ 'background-color': item }"
            @click="togTheme(item)"
          >
            <n-icon size="12" v-if="item === designStore.appTheme">
              <CheckOutlined />
            </n-icon>
          </span>
        </div>

        <n-divider title-placement="center">{{ t('settings.navMode') }}</n-divider>

        <div class="drawer-setting-item align-items-top">
          <div class="drawer-setting-item-style align-items-top">
            <n-tooltip placement="top">
              <template #trigger>
                <img
                  src="~@/assets/images/nav-theme-dark.svg"
                  @click="togNavMode('vertical')"
                  :alt="t('settings.navModeVertical')"
                />
              </template>
              <span>{{ t('settings.navModeVertical') }}</span>
            </n-tooltip>
            <n-badge dot color="#19be6b" v-show="settingStore.navMode === 'vertical'" />
          </div>

          <div class="drawer-setting-item-style">
            <n-tooltip placement="top">
              <template #trigger>
                <img
                  src="~@/assets/images/nav-horizontal.svg"
                  :alt="t('settings.navModeHorizontal')"
                  @click="togNavMode('horizontal')"
                />
              </template>
              <span>{{ t('settings.navModeHorizontal') }}</span>
            </n-tooltip>
            <n-badge dot color="#19be6b" v-show="settingStore.navMode === 'horizontal'" />
          </div>

          <div class="drawer-setting-item-style">
            <n-tooltip placement="top">
              <template #trigger>
                <img
                  src="~@/assets/images/nav-horizontal-mix.svg"
                  @click="togNavMode('horizontal-mix')"
                  :alt="t('settings.navModeHorizontalMix')"
                />
              </template>
              <span>{{ t('settings.navModeHorizontalMix') }}</span>
            </n-tooltip>
            <n-badge dot color="#19be6b" v-show="settingStore.navMode === 'horizontal-mix'" />
          </div>
        </div>

        <n-divider title-placement="center">{{ t('settings.navTheme') }}</n-divider>

        <div class="drawer-setting-item align-items-top">
          <div class="drawer-setting-item-style align-items-top">
            <n-tooltip placement="top">
              <template #trigger>
                <img
                  src="~@/assets/images/nav-theme-dark.svg"
                  :alt="t('settings.navThemeDarkSidebar')"
                  @click="togNavTheme('dark')"
                />
              </template>
              <span>{{ t('settings.navThemeDarkSidebar') }}</span>
            </n-tooltip>
            <n-badge dot color="#19be6b" v-if="settingStore.navTheme === 'dark'" />
          </div>

          <div class="drawer-setting-item-style">
            <n-tooltip placement="top">
              <template #trigger>
                <img
                  src="~@/assets/images/nav-theme-light.svg"
                  :alt="t('settings.navThemeLightSidebar')"
                  @click="togNavTheme('light')"
                />
              </template>
              <span>{{ t('settings.navThemeLightSidebar') }}</span>
            </n-tooltip>
            <n-badge dot color="#19be6b" v-if="settingStore.navTheme === 'light'" />
          </div>

          <div class="drawer-setting-item-style">
            <n-tooltip placement="top">
              <template #trigger>
                <img
                  src="~@/assets/images/header-theme-dark.svg"
                  @click="togNavTheme('header-dark')"
                  :alt="t('settings.navThemeDarkHeader')"
                />
              </template>
              <span>{{ t('settings.navThemeDarkHeader') }}</span>
            </n-tooltip>
            <n-badge dot color="#19be6b" v-if="settingStore.navTheme === 'header-dark'" />
          </div>
        </div>
        <n-divider title-placement="center">{{ t('settings.interfaceFeatures') }}</n-divider>

        <div class="drawer-setting-item">
          <div class="drawer-setting-item-title">{{ t('settings.splitMenu') }}</div>
          <div class="drawer-setting-item-action">
            <n-switch
              :disabled="settingStore.navMode !== 'horizontal-mix'"
              v-model:value="settingStore.menuSetting.mixMenu"
            />
          </div>
        </div>

        <div class="drawer-setting-item">
          <div class="drawer-setting-item-title">{{ t('settings.fixedHeader') }}</div>
          <div class="drawer-setting-item-action">
            <n-switch v-model:value="settingStore.headerSetting.fixed" />
          </div>
        </div>

        <!--        <div class="drawer-setting-item">-->
        <!--          <div class="drawer-setting-item-title">-->
        <!--            固定侧边栏-->
        <!--          </div>-->
        <!--          <div class="drawer-setting-item-action">-->
        <!--            <n-switch v-model:value="settingStore.menuSetting.fixed" />-->
        <!--          </div>-->
        <!--        </div>-->

        <div class="drawer-setting-item">
          <div class="drawer-setting-item-title">{{ t('settings.fixedTabs') }}</div>
          <div class="drawer-setting-item-action">
            <n-switch v-model:value="settingStore.multiTabsSetting.fixed" />
          </div>
        </div>

        <n-divider title-placement="center">{{ t('settings.interfaceDisplay') }}</n-divider>

        <div class="drawer-setting-item">
          <div class="drawer-setting-item-title">{{ t('settings.showReload') }}</div>
          <div class="drawer-setting-item-action">
            <n-switch v-model:value="settingStore.headerSetting.isReload" />
          </div>
        </div>

        <div class="drawer-setting-item">
          <div class="drawer-setting-item-title">{{ t('settings.showBreadcrumb') }}</div>
          <div class="drawer-setting-item-action">
            <n-switch v-model:value="settingStore.crumbsSetting.show" />
          </div>
        </div>

        <div class="drawer-setting-item">
          <div class="drawer-setting-item-title">{{ t('settings.showBreadcrumbIcon') }}</div>
          <div class="drawer-setting-item-action">
            <n-switch v-model:value="settingStore.crumbsSetting.showIcon" />
          </div>
        </div>

        <div class="drawer-setting-item">
          <div class="drawer-setting-item-title">{{ t('settings.showTabs') }}</div>
          <div class="drawer-setting-item-action">
            <n-switch v-model:value="settingStore.multiTabsSetting.show" />
          </div>
        </div>
        <!--1.15废弃，没啥用，占用操作空间-->
        <!--        <div class="drawer-setting-item">-->
        <!--          <div class="drawer-setting-item-title"> 显示页脚 </div>-->
        <!--          <div class="drawer-setting-item-action">-->
        <!--            <n-switch v-model:value="settingStore.showFooter" />-->
        <!--          </div>-->
        <!--        </div>-->

        <n-divider title-placement="center">{{ t('settings.animation') }}</n-divider>

        <div class="drawer-setting-item">
          <div class="drawer-setting-item-title">{{ t('settings.enableAnimation') }}</div>
          <div class="drawer-setting-item-action">
            <n-switch v-model:value="settingStore.isPageAnimate" />
          </div>
        </div>

        <div class="drawer-setting-item">
          <div class="drawer-setting-item-title">{{ t('settings.animationType') }}</div>
          <div class="drawer-setting-item-select">
            <n-select v-model:value="settingStore.pageAnimateType" :options="animateOptions" />
          </div>
        </div>

        <div class="drawer-setting-item">
          <n-alert type="warning" :showIcon="false">
            <p>{{ alertText }}</p>
          </n-alert>
        </div>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<script lang="ts">
  import { defineComponent, reactive, toRefs, unref, watch, computed } from 'vue';
  import { useProjectSettingStore } from '@/store/modules/projectSetting';
  import { useDesignSettingStore } from '@/store/modules/designSetting';
  import { CheckOutlined } from '@vicons/antd';
  import { Moon, SunnySharp } from '@vicons/ionicons5';
  import { darkTheme } from 'naive-ui';
  import { animates as rawAnimateOptions } from '@/settings/animateSetting';
  import { t } from '@/i18n';

  export default defineComponent({
    name: 'ProjectSetting',
    components: { CheckOutlined, Moon, SunnySharp },
    props: {
      title: {
        type: String,
        default: '',
      },
      width: {
        type: Number,
        default: 280,
      },
    },
    setup(props) {
      const settingStore = useProjectSettingStore();
      const designStore = useDesignSettingStore();
      const drawerTitle = computed(() => props.title || t('settings.projectConfig'));
      const state = reactive({
        width: props.width,
        isDrawer: false,
        placement: 'right',
        appThemeList: designStore.appThemeList,
      });
      const alertText = computed(() => t('settings.previewAlert'));
      const animateOptions = computed(() =>
        rawAnimateOptions.map((item) => ({
          ...item,
          label: t(`settings.animate.${item.value}`),
        }))
      );

      watch(
        () => designStore.darkTheme,
        (to) => {
          settingStore.navTheme = to ? 'header-dark' : 'dark';
        }
      );

      const directionsOptions = computed(() => {
        return animateOptions.value.find((item) => item.value == unref(settingStore.pageAnimateType));
      });

      function openDrawer() {
        state.isDrawer = true;
      }

      function closeDrawer() {
        state.isDrawer = false;
      }

      function togNavTheme(theme) {
        settingStore.navTheme = theme;
        if (settingStore.navMode === 'horizontal' && ['light'].includes(theme)) {
          settingStore.navTheme = 'dark';
        }
      }

      function togTheme(color) {
        designStore.appTheme = color;
      }

      function togNavMode(mode) {
        settingStore.navMode = mode;
        settingStore.menuSetting.mixMenu = false;
      }

      return {
        ...toRefs(state),
        settingStore,
        designStore,
        drawerTitle,
        alertText,
        togNavTheme,
        togNavMode,
        togTheme,
        darkTheme,
        openDrawer,
        closeDrawer,
        animateOptions,
        directionsOptions,
        t,
      };
    },
  });
</script>

<style lang="less" scoped>
  .drawer {
    .n-divider:not(.n-divider--vertical) {
      margin: 10px 0;
    }

    &-setting-item {
      display: flex;
      align-items: center;
      padding: 12px 0;
      flex-wrap: wrap;

      &-style {
        display: inline-block;
        position: relative;
        margin-right: 16px;
        cursor: pointer;
        text-align: center;
      }

      &-title {
        flex: 1 1;
        font-size: 14px;
      }

      &-action {
        flex: 0 0 auto;
      }

      &-select {
        flex: 1;
      }

      .theme-item {
        width: 20px;
        min-width: 20px;
        height: 20px;
        cursor: pointer;
        border: 1px solid #eee;
        border-radius: 2px;
        margin: 0 5px 5px 0;
        text-align: center;
        line-height: 14px;

        .n-icon {
          color: #fff;
        }
      }
    }

    .align-items-top {
      align-items: flex-start;
      padding: 2px 0;
    }

    .justify-center {
      justify-content: center;
    }

    .dark-switch .n-switch {
      ::v-deep(.n-switch__rail) {
        background-color: #000e1c;
      }
    }
  }
</style>
