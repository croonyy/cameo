import { defineStore } from 'pinia';
import projectSetting from '@/settings/projectSetting';
import type { IHeaderSetting, IMenuSetting, IMultiTabsSetting, ICrumbsSetting } from '/#/config';
import { watch } from 'vue';

const {
  navMode,
  navTheme,
  isMobile,
  headerSetting,
  showFooter,
  menuSetting,
  multiTabsSetting,
  crumbsSetting,
  permissionMode,
  isPageAnimate,
  pageAnimateType,
} = projectSetting;

const STORAGE_KEY = 'app-project-setting';

// 从 localStorage 读取已保存的设置，与默认值合并
function loadSavedSettings() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error('Failed to load settings from localStorage:', e);
  }
  return null;
}

// 将需要持久化的字段保存到 localStorage
function saveSettings(state: any) {
  try {
    const toSave = {
      navMode: state.navMode,
      navTheme: state.navTheme,
      headerSetting: { ...state.headerSetting },
      menuSetting: { ...state.menuSetting },
      multiTabsSetting: { ...state.multiTabsSetting },
      crumbsSetting: { ...state.crumbsSetting },
      showFooter: state.showFooter,
      permissionMode: state.permissionMode,
      isPageAnimate: state.isPageAnimate,
      pageAnimateType: state.pageAnimateType,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  } catch (e) {
    console.error('Failed to save settings to localStorage:', e);
  }
}

interface ProjectSettingState {
  navMode: string; //导航模式
  navTheme: string; //导航风格
  headerSetting: IHeaderSetting; //顶部设置
  showFooter: boolean; //页脚
  menuSetting: IMenuSetting; //多标签
  multiTabsSetting: IMultiTabsSetting; //多标签
  crumbsSetting: ICrumbsSetting; //面包屑
  permissionMode: string; //权限模式
  isPageAnimate: boolean; //是否开启路由动画
  pageAnimateType: string; //路由动画类型
  isMobile: boolean; // 是否处于移动端模式
}

export const useProjectSettingStore = defineStore({
  id: 'app-project-setting',
  state: (): ProjectSettingState => {
    const saved = loadSavedSettings();
    return {
      navMode: saved?.navMode ?? navMode,
      navTheme: saved?.navTheme ?? navTheme,
      isMobile,
      headerSetting: saved?.headerSetting
        ? { ...headerSetting, ...saved.headerSetting }
        : { ...headerSetting },
      menuSetting: saved?.menuSetting
        ? { ...menuSetting, ...saved.menuSetting }
        : { ...menuSetting },
      multiTabsSetting: saved?.multiTabsSetting
        ? { ...multiTabsSetting, ...saved.multiTabsSetting }
        : { ...multiTabsSetting },
      crumbsSetting: saved?.crumbsSetting
        ? { ...crumbsSetting, ...saved.crumbsSetting }
        : { ...crumbsSetting },
      permissionMode: saved?.permissionMode ?? permissionMode,
      showFooter: saved?.showFooter ?? showFooter,
      isPageAnimate: saved?.isPageAnimate ?? isPageAnimate,
      pageAnimateType: saved?.pageAnimateType ?? pageAnimateType,
    };
  },
  getters: {
    getNavMode(): string {
      return this.navMode;
    },
    getNavTheme(): string {
      return this.navTheme;
    },
    getIsMobile(): boolean {
      return this.isMobile;
    },
    getHeaderSetting(): object {
      return this.headerSetting;
    },
    getShowFooter(): boolean {
      return this.showFooter;
    },
    getMenuSetting(): object {
      return this.menuSetting;
    },
    getMultiTabsSetting(): object {
      return this.multiTabsSetting;
    },
    getCrumbsSetting(): object {
      return this.crumbsSetting;
    },
    getPermissionMode(): string {
      return this.permissionMode;
    },
    getIsPageAnimate(): boolean {
      return this.isPageAnimate;
    },
    getPageAnimateType(): string {
      return this.pageAnimateType;
    },
  },
  actions: {
    setNavTheme(value: string): void {
      this.navTheme = value;
    },
    setIsMobile(value: boolean): void {
      this.isMobile = value;
    },
    // 持久化保存当前设置
    persistSettings(): void {
      saveSettings(this.$state);
    },
  },
});

// 导出一个辅助函数，在应用初始化时调用，自动监听状态变化并持久化
export function setupSettingPersistence() {
  const store = useProjectSettingStore();
  watch(
    () => ({
      navMode: store.navMode,
      navTheme: store.navTheme,
      headerSetting: { ...store.headerSetting },
      menuSetting: { ...store.menuSetting },
      multiTabsSetting: { ...store.multiTabsSetting },
      crumbsSetting: { ...store.crumbsSetting },
      showFooter: store.showFooter,
      permissionMode: store.permissionMode,
      isPageAnimate: store.isPageAnimate,
      pageAnimateType: store.pageAnimateType,
    }),
    () => {
      store.persistSettings();
    },
    { deep: true }
  );
}
