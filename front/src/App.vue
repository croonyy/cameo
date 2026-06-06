<template>
  <NConfigProvider
    :locale="naiveLocale"
    :theme="getDarkTheme"
    :theme-overrides="getThemeOverrides"
    :date-locale="naiveDateLocale"
  >
    <AppProvider>
      <RouterView v-if="!isLock" />
    </AppProvider>
    <transition v-if="isLock" name="slide-up">
      <LockScreen />
    </transition>
  </NConfigProvider>
</template>

<script lang="ts" setup>
  import { computed, onMounted, onUnmounted, watch } from 'vue';
  import { zhCN, dateZhCN, enUS, dateEnUS, darkTheme } from 'naive-ui';
  import { LockScreen } from '@/components/Lockscreen';
  import { AppProvider } from '@/components/Application';
  import { useScreenLockStore } from '@/store/modules/screenLock.js';
  import { useRoute } from 'vue-router';
  import { useDesignSettingStore } from '@/store/modules/designSetting';
  import { lighten } from '@/utils/index';
  import { getLanguage } from '@/i18n';
  // import { useCrudMenu } from '@/store/modules/crudMenu';
  // import { GetAllModelsInfo } from '@/api/crud/menu';

  const route = useRoute();
  const useScreenLock = useScreenLockStore();
  const designStore = useDesignSettingStore();
  const isLock = computed(() => useScreenLock.isLocked);
  const lockTime = computed(() => useScreenLock.lockTime);
  const naiveLocale = computed(() => (getLanguage() === 'en-US' ? enUS : zhCN));
  const naiveDateLocale = computed(() => (getLanguage() === 'en-US' ? dateEnUS : dateZhCN));

  /**
   * @type import('naive-ui').GlobalThemeOverrides
   */
  const getThemeOverrides = computed(() => {
    const appTheme = designStore.appTheme;
    const lightenStr = lighten(designStore.appTheme, 6);
    return {
      common: {
        primaryColor: appTheme,
        primaryColorHover: lightenStr,
        primaryColorPressed: lightenStr,
        primaryColorSuppl: appTheme,
        railColor: appTheme,
        railColorActive: appTheme,
      },
      LoadingBar: {
        colorLoading: appTheme,
      },
      Menu: {
        railColor: appTheme,
        railColorActive: appTheme,
      },
      // DataTable: {
      //   mergedTdColorSorting: '#ff0000',
      // },
    };
  });

  const getDarkTheme = computed(() => (designStore.darkTheme ? darkTheme : undefined));

  // 同步主题颜色到 :root CSS 变量，供全局 CSS 使用
  const syncThemeColorsToRoot = () => {
    const root = document.documentElement;
    const appTheme = designStore.appTheme;
    const lightenStr = lighten(appTheme, 6);

    root.style.setProperty('--app-primary-color', appTheme);
    root.style.setProperty('--app-primary-color-hover', lightenStr);
  };

  // 监听主题变化
  watch(
    () => designStore.appTheme,
    () => {
      syncThemeColorsToRoot();
    },
    { immediate: true }
  );

  let timer: NodeJS.Timer;

  const timekeeping = () => {
    // @ts-ignore
    clearInterval(timer);
    if (route.name == 'login' || isLock.value) return;
    // 设置不锁屏
    useScreenLock.setLock(false);
    // 重置锁屏时间
    useScreenLock.setLockTime();
    timer = setInterval(() => {
      // 锁屏倒计时递减
      useScreenLock.setLockTime(lockTime.value - 1);
      if (lockTime.value <= 0) {
        // 设置锁屏
        useScreenLock.setLock(true);
        // @ts-ignore
        return clearInterval(timer);
      }
    }, 1000);
  };

  onMounted(async () => {
    // const crudMenuStore = useCrudMenu();
    // const { data } = await GetAllModelsInfo();
    // crudMenuStore.setCrudMenu(data || {});
    document.addEventListener('mousedown', timekeeping);
  });

  onUnmounted(() => {
    document.removeEventListener('mousedown', timekeeping);
  });
</script>
