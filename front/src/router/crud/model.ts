import { RouteRecordRaw } from 'vue-router';
import { Layout } from '@/router/constant';
// import { getIcon } from '@/utils/getIconByName';
import { UD_MENU, CRUD_LIST, CRUD_EDIT, CRUD_CREATE } from '@/store/consts';

export const CrudRoute: RouteRecordRaw = {
  path: '/crud',
  name: 'crud_app',
  component: Layout,
  meta: {
    type: UD_MENU,
    title: 'admin管理',
    hideBreadcrumb: true,
  },
  children: [
    {
      path: 'list/:app_name/:model_name',
      // name: 'crud_:app_name_:model_name',
      name: CRUD_LIST, // 组件缓存,组件里面也需要定义name  defineOptions({ name: CRUD_LIST });
      component: () => import('@/views/crud/List.vue'),
      meta: {
        type: CRUD_LIST,
        title: 'DB模型管理',
        // hideBreadcrumb: true,
        // 添加 keepAlive 支持
        keepAlive: true,
        // activeMenu: 'activeMenu crud_list_app_name',
        // componentKey: (route: any) => `crud_${route.params.app_name}_${route.params.model_name}`,
      },
      // beforeEnter: (to, from, next) => {
      //   const { app_name, model_name } = to.params;
      //   // 动态设置路由名称
      //   // to.name = `crud_${app_name}_${model_name}`;
      //   // 动态设置页面标题
      //   to.meta.title = `${app_name}_${model_name}`;；
      //   next();
      // },
      // props: (route) => ({
      //   // 传递参数给组件
      //   appName: route.params.app_name,
      //   modelName: route.params.model_name,
      //   // 用于组件缓存的key
      //   cacheKey: `crud_${route.params.app_name}_${route.params.model_name}`,
      // }),
    },
    {
      path: 'edit/:app_name/:model_name/:id?',
      name: CRUD_EDIT,
      component: () => import('@/views/crud/Edit.vue'),
      meta: {
        type: CRUD_EDIT,
        title: 'DB模型编辑',
        keepAlive: true,
        activeMenu: CRUD_LIST,
      },
    },
    {
      path: 'create/:app_name/:model_name/',
      name: CRUD_CREATE,
      component: () => import('@/views/crud/Create.vue'),
      meta: {
        type: CRUD_CREATE,
        title: 'DB模型创建',
        keepAlive: true,
        activeMenu: CRUD_LIST,
      },
    },
  ],
};
