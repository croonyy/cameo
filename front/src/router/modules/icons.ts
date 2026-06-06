import { RouteRecordRaw } from 'vue-router';
import { Layout } from '@/router/constant';
import { getIcon } from '@/utils/getIconByName';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/icons',
    name: 'icons',
    // redirect: '/icons/index',
    component: Layout,
    meta: {
      title: 'Icons',
      icon: getIcon('ionicons5:HeartOutline'),
      // permissions: ['dashboard_console', 'dashboard_console', 'dashboard_workplace'],
      sort: 0,
    },
    children: [
      {
        path: 'antd',
        name: 'antd',
        meta: {
          title: 'antd',
          // keepAlive: true,
          alwaysShow: true,
          // permissions: ['dashboard_workplace'],
        },
        component: () => import('@/views/icons/antd.vue'),
      },
      {
        path: 'ionicons5',
        name: 'ionicons5',
        meta: {
          title: 'ionicons5',
        },
        component: () => import('@/views/icons/ionicons5.vue'),
      },
    ],
  },
];

export default routes;
