import { defineStore } from 'pinia';
import { store } from '@/store';

interface PaginationState {
  page: number;
  pageSize: number;
}

export const useCrudRefreshStore = defineStore('crudRefresh', {
  state: () => ({
    refreshFlags: new Map<string, boolean>(), // key: "appName_modelName", value: boolean
    paginationStates: new Map<string, PaginationState>(), // key: "appName_modelName", value: { page, pageSize }
  }),
  actions: {
    setRefreshFlag(appName: string, modelName: string) {
      const key = `${appName}_${modelName}`;
      this.refreshFlags.set(key, true);
    },
    getRefreshFlag(appName: string, modelName: string): boolean {
      const key = `${appName}_${modelName}`;
      return this.refreshFlags.get(key) || false;
    },
    clearRefreshFlag(appName: string, modelName: string) {
      const key = `${appName}_${modelName}`;
      this.refreshFlags.delete(key);
    },
    setPaginationState(appName: string, modelName: string, page: number, pageSize: number) {
      const key = `${appName}_${modelName}`;
      this.paginationStates.set(key, { page, pageSize });
    },
    getPaginationState(appName: string, modelName: string): PaginationState | null {
      const key = `${appName}_${modelName}`;
      return this.paginationStates.get(key) || null;
    },
    clearPaginationState(appName: string, modelName: string) {
      const key = `${appName}_${modelName}`;
      this.paginationStates.delete(key);
    },
  },
});

export function useCrudRefresh() {
  return useCrudRefreshStore(store);
}
