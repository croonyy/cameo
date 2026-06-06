import zhCN from './resources/zh-CN.json';
import enUS from './resources/en-US.json';

export type AppLanguage = 'zh-CN' | 'en-US';

const STORAGE_KEY = 'app_language';
const DEFAULT_LANGUAGE: AppLanguage = 'zh-CN';
const resources: Record<AppLanguage, Record<string, string>> = {
  'zh-CN': zhCN,
  'en-US': enUS,
};
const listeners = new Set<(language: AppLanguage) => void>();

function normalizeLanguage(language?: string | null): AppLanguage {
  if (!language) return DEFAULT_LANGUAGE;
  const normalized = language.trim();
  if (normalized === 'zh-CN' || normalized.toLowerCase() === 'zh') return 'zh-CN';
  if (normalized === 'en-US' || normalized.toLowerCase() === 'en') return 'en-US';
  if (normalized.toLowerCase().startsWith('zh')) return 'zh-CN';
  if (normalized.toLowerCase().startsWith('en')) return 'en-US';
  return DEFAULT_LANGUAGE;
}

function getStoredLanguage(): AppLanguage | null {
  if (typeof window === 'undefined') return null;
  return normalizeLanguage(window.localStorage.getItem(STORAGE_KEY));
}

let currentLanguage: AppLanguage =
  getStoredLanguage() ||
  normalizeLanguage(typeof navigator === 'undefined' ? undefined : navigator.language);

export function getLanguage(): AppLanguage {
  return currentLanguage;
}

export function setLanguage(language: AppLanguage | string): AppLanguage {
  const nextLanguage = normalizeLanguage(language);
  currentLanguage = nextLanguage;
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, nextLanguage);
    document.documentElement.lang = nextLanguage;
  }
  listeners.forEach((listener) => listener(nextLanguage));
  return nextLanguage;
}

export function subscribeLanguageChange(callback: (language: AppLanguage) => void) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

export function t(key: string, params?: Record<string, string | number | boolean | null | undefined>): string {
  const template = resources[currentLanguage]?.[key] || resources[DEFAULT_LANGUAGE]?.[key] || key;
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, name) => {
    const value = params[name];
    return value === null || typeof value === 'undefined' ? '' : String(value);
  });
}

export function initI18n() {
  setLanguage(currentLanguage);
}
