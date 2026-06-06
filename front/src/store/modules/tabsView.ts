import { defineStore } from 'pinia';
import { RouteLocationNormalized } from 'vue-router';

// 不需要出现在标签页中的路由
const whiteList = ['Redirect', 'login'];

export type RouteItem = Partial<RouteLocationNormalized> & {
  fullPath: string;
  path: string;
  name: string;
  hash: string;
  meta: object;
  params: object;
  query: object;
};

export type ITabsViewState = {
  tabsList: RouteItem[]; // 标签页
};

//保留固定路由
function retainAffixRoute(list: any[]) {
  return list.filter((item) => item?.meta?.affix ?? false);
}

export const useTabsViewStore = defineStore({
  id: 'app-tabs-view',
  state: (): ITabsViewState => ({
    tabsList: [],
  }),
  getters: {},
  actions: {
    initTabs(routes: RouteItem[]) {
      // 初始化标签页
      this.tabsList = routes;
    },
    delTabByFullPath(full_path: string) {
      // 删除标签页
      this.tabsList = this.tabsList.filter((item) => item.fullPath != full_path);
    },
    addTab(route: RouteItem, afterFullPath?: string): boolean {
      // 添加标签页
      if (whiteList.includes(route.name)) return false;
      const isExists = this.tabsList.some((item) => item.fullPath == route.fullPath);
      if (!isExists) {
        const insertIndex = afterFullPath
          ? this.tabsList.findIndex((item) => item.fullPath == afterFullPath)
          : -1;
        if (insertIndex >= 0) {
          this.tabsList.splice(insertIndex + 1, 0, route);
        } else {
          this.tabsList.push(route);
        }
      }
      return true;
    },
    closeLeftTabs(route: RouteItem) {
      // 关闭左侧
      const index = this.tabsList.findIndex((item) => item.fullPath == route.fullPath);
      this.tabsList = this.tabsList.filter((item, i) => i >= index || (item?.meta?.affix ?? false));
    },
    closeRightTabs(route: RouteItem) {
      // 关闭右侧
      const index = this.tabsList.findIndex((item) => item.fullPath == route.fullPath);
      this.tabsList = this.tabsList.filter((item, i) => i <= index || (item?.meta?.affix ?? false));
    },
    closeOtherTabs(route: RouteItem) {
      // 关闭其他
      this.tabsList = this.tabsList.filter(
        (item) => item.fullPath == route.fullPath || (item?.meta?.affix ?? false)
      );
    },
    closeCurrentTab(route: RouteItem) {
      // 关闭当前页
      const index = this.tabsList.findIndex((item) => item.fullPath == route.fullPath);
      this.tabsList.splice(index, 1);
    },
    closeAllTabs() {
      // 关闭全部
      this.tabsList = retainAffixRoute(this.tabsList);
    },
  },
});
