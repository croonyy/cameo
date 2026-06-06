import { defineStore } from 'pinia';
import { store } from '@/store';
import { GetAllModelsInfo } from '@/api/crud/models';
import { storage } from '@/utils/Storage';
import { ACCESS_TOKEN, REFRESH_TOKEN } from '@/store/mutation-types';
import { useUser } from '@/store/modules/user';

// interface CrudMenuState {
//   crudMenu: Record<string, any>;
// }

interface ModelInfo {
  menu_name: string;
  app: string;
  tb_name: string;
  tb_description: string;
  model_name: string;
  url: string;
}

interface AppInfo {
  models: ModelInfo[];
  name: string;
  menu_name: string;
  description: string;
  icon: string;
}

interface UnionInfo {
  all_models: string[];
  allow_models: string[];
  allow_models_info: Record<string, AppInfo>;
}

interface CrudMenuState {
  crudMenu: UnionInfo;
  isloaded: boolean;
}

export const useCrudMenuStore = defineStore('crud-menu', {
  state: (): CrudMenuState => ({
    crudMenu: {
      all_models: [],
      allow_models: [],
      allow_models_info: {},
    },
    isloaded: false,
  }),

  getters: {
    getCrudMenu(): UnionInfo {
      return this.crudMenu;
    },
  },
  actions: {
    isCrudMenuEmpty(): boolean {
      return Object.keys(this.crudMenu).length === 0;
    },
    setCrudMenu(data: UnionInfo) {
      this.crudMenu = data;
    },
    async fetchCrudMenu() {
      try {
        const { data } = await GetAllModelsInfo();
        console.log('@@@allModelsInfo', data);
        this.setCrudMenu(data || {});
      } catch (error) {
        console.log(error);
      } finally {
        this.isloaded = true;
      }
    },
    async initCrudMenu() {
      if (this.isloaded) {
        return;
      } else {
        if (storage.get(ACCESS_TOKEN)) {
          await this.fetchCrudMenu();
          this.isloaded = true;
        } else {
          console.log('@@@本地存储没有找到ACCESS_TOKEN，或者过期了。');
          // 如果access_token过期，则刷新token
          // 修改时间过期用来测试
          // access_token:{"value":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInR5cGUiOiJqd3QifQ.eyJpYXQiOjE3NDUwNzc5NzEuMjUxMDQ5LCJleHAiOjE3NDUwNzg1NzEuMjUxMDQ5LCJwYXNzd29yZCI6IiQyYiQxMiRoQUU1Mi9BUzYxL1R5Q1AyL1FlVm0ub3prY0NkQm5ZUlNWaEwyb2RvN3BVU3NybkRDdVJIdSIsImxhc3RfbG9naW4iOm51bGwsImlzX2RlbGV0ZSI6ZmFsc2UsImdlbmRlciI6Ilx1NzUzNyIsInVzZXJuYW1lIjoiYWRtaW4iLCJpZCI6MSwiaXNfc3VwZXJ1c2VyIjp0cnVlLCJjbl9uYW1lIjoiXHU3YmExXHU3NDA2XHU1NDU4IiwidXBkYXRlZF9hdCI6IjIwMjUtMDQtMTAgMjI6NTU6MTEiLCJjcmVhdGVkX2F0IjoiMjAyNS0wNC0xMCAyMTo1OToyMSIsImlzX2FjdGl2ZSI6dHJ1ZX0.6HSjusWsoTUWoe1M84bcIe-4jGQbf-jDAiTQvs3F4tE","expire":1735078569251}
          // refresh_token:{"value":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInR5cGUiOiJqd3QifQ.eyJpYXQiOjE3NDUwNzg4ODYuODQwMTY0LCJleHAiOjE3NDYzNzQ4ODYuODQwMTY0LCJwYXNzd29yZCI6IiQyYiQxMiRoQUU1Mi9BUzYxL1R5Q1AyL1FlVm0ub3prY0NkQm5ZUlNWaEwyb2RvN3BVU3NybkRDdVJIdSIsImxhc3RfbG9naW4iOm51bGwsImlzX2RlbGV0ZSI6ZmFsc2UsImdlbmRlciI6Ilx1NzUzNyIsInVzZXJuYW1lIjoiYWRtaW4iLCJpZCI6MSwiaXNfc3VwZXJ1c2VyIjp0cnVlLCJjbl9uYW1lIjoiXHU3YmExXHU3NDA2XHU1NDU4IiwidXBkYXRlZF9hdCI6IjIwMjUtMDQtMTAgMjI6NTU6MTEiLCJjcmVhdGVkX2F0IjoiMjAyNS0wNC0xMCAyMTo1OToyMSIsImlzX2FjdGl2ZSI6dHJ1ZSwiZ3JhbnRfdHlwZSI6InJlZnJlc2gifQ.VtzBODaVMLimjegpsJmmbOwP_l6GAJZ-1u94bUjUKSY","expire":1735078569251}
          const userStore = useUser();
          const isRefresh = await userStore.refreshToken();
          if (isRefresh) {
            await this.fetchCrudMenu();
            this.isloaded = true;
          }
        }
      }
    },
  },
});

// Need to be used outside the setup
export function useCrudMenu() {
  return useCrudMenuStore(store);
}
