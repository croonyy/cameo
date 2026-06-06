import type { RouteRecordRaw } from 'vue-router';
import { isNavigationFailure, Router } from 'vue-router';
import { useUser } from '@/store/modules/user';
import { useAsyncRoute } from '@/store/modules/asyncRoute';
import { ACCESS_TOKEN } from '@/store/mutation-types';
import { storage } from '@/utils/Storage';
import { PageEnum } from '@/enums/pageEnum';
import { ErrorPageRoute } from '@/router/base';

// const whitePathList = [PageEnum.BASE_LOGIN, '/']; // no redirect whitelist
const whitePathList = [PageEnum.BASE_LOGIN, '/crud/test', '/']; // no redirect whitelist

export function createRouterGuards(router: Router) {
  const userStore = useUser();
  const asyncRouteStore = useAsyncRoute();

  router.beforeEach(async (to, from, next) => {
    const Loading = window['$loading'] || null;
    Loading && Loading.start();

    if (from.path === PageEnum.BASE_LOGIN && to.name === 'errorPage') {
      next(PageEnum.BASE_HOME);
      return;
    }

    if (whitePathList.includes(to.path as PageEnum) || to.meta.ignoreAuth) {
      next();
      return;
    }

    const redirectData: { path: string; replace: boolean; query?: Recordable<string> } = {
      path: PageEnum.BASE_LOGIN,
      replace: true,
    };
    if (to.path) {
      redirectData.query = { redirect: to.fullPath || to.path };
    }

    if (!storage.get(ACCESS_TOKEN)) {
      try {
        const refreshed = await userStore.refreshToken();
        if (!refreshed) {
          next(redirectData);
          return;
        }
      } catch (error) {
        await userStore.logout();
        next(redirectData);
        return;
      }
    }

    if (!asyncRouteStore.getIsDynamicRouteAdded) {
      try {
        const userInfo = await userStore.getInfo();
        const routes = await asyncRouteStore.generateRoutes(userInfo);
        routes.forEach((item: unknown) => {
          router.addRoute(item as unknown as RouteRecordRaw);
        });

        const isErrorPage = router.getRoutes().findIndex((item) => item.name === ErrorPageRoute.name);
        if (isErrorPage === -1) {
          router.addRoute(ErrorPageRoute as unknown as RouteRecordRaw);
        }
        asyncRouteStore.setDynamicRouteAdded(true);
        next({ ...to, replace: true });
        return;
      } catch (error) {
        await userStore.logout();
        next(redirectData);
        return;
      }
    }

    next();
  });

  router.afterEach((to, _, failure) => {
    // console.log('@@@afterEach  to', to);
    // console.log('@@@afterEach  failure', failure);
    document.title = (to?.meta?.title as string) || document.title;
    if (isNavigationFailure(failure)) {
      // console.log('failed navigation', failure);
    }
    const asyncRouteStore = useAsyncRoute();
    // 在这里设置需要缓存的组件名称
    const keepAliveComponents = asyncRouteStore.keepAliveComponents;
    // 获取组件名称（懒加载组件无法从 import 函数上读取 name，回退用路由名）
    const matchedRoute = to.matched.find((item) => item.name == to.name);
    const currentComName: any =
      matchedRoute?.components?.default?.name || (to.meta?.keepAlive ? String(to.name) : undefined);
    if (currentComName && !keepAliveComponents.includes(currentComName) && to.meta?.keepAlive) {
      // 需要缓存的组件
      keepAliveComponents.push(currentComName);
    } else if (!to.meta?.keepAlive || to.name == 'Redirect') {
      // 不需要缓存的组件
      const index = asyncRouteStore.keepAliveComponents.findIndex((name) => name == currentComName);
      if (index != -1) {
        keepAliveComponents.splice(index, 1);
      }
    }
    // console.log('@@@guards setkeepAliveComponents', keepAliveComponents);
    asyncRouteStore.setKeepAliveComponents(keepAliveComponents);
    const Loading = window['$loading'] || null;
    Loading && Loading.finish();
  });

  router.onError((error) => {
    console.log(error, '路由错误');
  });
}
