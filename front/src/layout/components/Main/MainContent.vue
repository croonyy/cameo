<template>
  <RouterView>
    <template #default="{ Component, route }">
      <template v-if="mode === 'production'">
        <keep-alive ref="keepAliveRef" :include="getKeepAliveInclude" :max="getKeepAliveMax">
          <component
            v-if="route.meta.keepAlive"
            :is="Component"
            :key="getKeepAliveCacheKey(route)"
          />
        </keep-alive>
        <transition :name="getTransitionName" mode="out-in" appear>
          <component v-if="!route.meta.keepAlive" :is="Component" :key="route.fullPath" />
        </transition>
      </template>
      <template v-else>
        <keep-alive ref="keepAliveRef" :include="getKeepAliveInclude" :max="getKeepAliveMax">
          <component
            v-if="route.meta.keepAlive"
            :is="Component"
            :key="getKeepAliveCacheKey(route)"
          />
        </keep-alive>
        <component v-if="!route.meta.keepAlive" :is="Component" :key="route.fullPath" />
      </template>
    </template>
  </RouterView>
</template>

<script>
  import {
    defineComponent,
    computed,
    unref,
    ref,
    onMounted,
    onBeforeUnmount,
  } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { useTabsViewStore } from '@/store/modules/tabsView';
  import { useProjectSetting } from '@/hooks/setting/useProjectSetting';
  // import CrudList from '@/views/crud/list.vue';

  export default defineComponent({
    name: 'MainView',
    components: {},
    props: {
      notNeedKey: {
        type: Boolean,
        default: false,
      },
      animate: {
        type: Boolean,
        default: true,
      },
    },
    setup() {
      const { isPageAnimate, pageAnimateType } = useProjectSetting();
      const currentRoute = useRoute();
      const router = useRouter();
      const tabsViewStore = useTabsViewStore();
      const keepAliveRef = ref(null);
      const invalidatedRouteVersions = ref({});

      const getKeepAliveVersion = (fullPath) => invalidatedRouteVersions.value[fullPath] || 0;

      const getKeepAliveCacheKey = (route) => {
        const fullPath = route?.fullPath || '';
        if (!fullPath) return '';
        return `${fullPath}__alive_${getKeepAliveVersion(fullPath)}`;
      };

      const getKeepAliveComponentName = (route) => {
        if (!route?.meta?.keepAlive) return undefined;
        const matchedRoute = router
          .getRoutes()
          .find((item) => item.name == route.name || item.path == route.path);
        const component = matchedRoute?.components?.default;
        return component?.name || (route.name ? String(route.name) : undefined);
      };

      const getKeepAliveInclude = computed(() => {
        const names = tabsViewStore.tabsList
          .map(getKeepAliveComponentName)
          .filter((name) => !!name);
        const currentName = getKeepAliveComponentName(currentRoute);
        if (currentName && !names.includes(currentName)) {
          names.push(currentName);
        }
        return names.length ? names : [];
      });

      const getKeepAliveMax = computed(() => {
        const keepAliveTabCount = tabsViewStore.tabsList.filter((item) => item?.meta?.keepAlive)
          .length;
        return Math.max(keepAliveTabCount, currentRoute.meta?.keepAlive ? 1 : 0, 1);
      });

      const getTransitionName = computed(() => {
        return unref(isPageAnimate) ? unref(pageAnimateType) : '';
      });

      const mode = import.meta.env.MODE;
      // console.log('@@@mode', mode);

      const handleClosedTabs = (event) => {
        const fullPaths = event?.detail?.fullPaths || [];
        fullPaths.forEach((fullPath) => {
          invalidatedRouteVersions.value[fullPath] = getKeepAliveVersion(fullPath) + 1;
        });
      };

      onMounted(() => {
        window.addEventListener('tabs-card:closed', handleClosedTabs);
      });

      onBeforeUnmount(() => {
        window.removeEventListener('tabs-card:closed', handleClosedTabs);
      });

      return {
        keepAliveRef,
        getKeepAliveInclude,
        getKeepAliveMax,
        getKeepAliveCacheKey,
        getTransitionName,
        mode,
      };
    },
  });
</script>

<style lang="less" scoped></style>
