import { defineStore } from 'pinia';
import { store } from '@/store';
import designSetting from '@/settings/designSetting';
import { watch } from 'vue';

const { darkTheme, appTheme, appThemeList } = designSetting;
const STORAGE_KEY = 'app-design-setting';

function loadSavedSettings() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error('Failed to load design settings from localStorage:', e);
  }
  return null;
}

function saveSettings(state: DesignSettingState) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        darkTheme: state.darkTheme,
        appTheme: state.appTheme,
      })
    );
  } catch (e) {
    console.error('Failed to save design settings to localStorage:', e);
  }
}

interface DesignSettingState {
  //深色主题
  darkTheme: boolean;
  //系统风格
  appTheme: string;
  //系统内置风格
  appThemeList: string[];
}

export const useDesignSettingStore = defineStore({
  id: 'app-design-setting',
  state: (): DesignSettingState => {
    const saved = loadSavedSettings();
    return {
      darkTheme: saved?.darkTheme ?? darkTheme,
      appTheme: saved?.appTheme ?? appTheme,
      appThemeList,
    };
  },
  getters: {
    getDarkTheme(): boolean {
      return this.darkTheme;
    },
    getAppTheme(): string {
      return this.appTheme;
    },
    getAppThemeList(): string[] {
      return this.appThemeList;
    },
  },
  actions: {
    persistSettings(): void {
      saveSettings(this.$state);
    },
  },
});

export function setupDesignSettingPersistence() {
  const store = useDesignSettingStore();
  watch(
    () => ({
      darkTheme: store.darkTheme,
      appTheme: store.appTheme,
    }),
    () => {
      store.persistSettings();
    },
    { deep: true }
  );
}

// Need to be used outside the setup
export function useDesignSetting() {
  return useDesignSettingStore(store);
}
