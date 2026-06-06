<template>
  <!--导航卡片-->
  <!-- <div class="mt-4"> -->
  <div>
    <div v-for="[key, value] of Object.entries(modelInfo)" :key="key" style="margin-bottom: 12px">
      <n-card size="small">
        <template #header>
          <h3>{{ appInfo[key]?.app_menu_name || appInfo[key]?.app }}</h3>
          <span v-if="appInfo[key]?.app_description" style="font-size: 12px; color: #999999">{{
            appInfo[key]?.app_description
          }}</span>
        </template>
        <n-grid
          :key="key"
          cols="3 s:4 m:6 l:8 xl:10 2xl:12"
          responsive="screen"
          :x-gap="4"
          :y-gap="4"
        >
          <n-grid-item v-for="(item, index) in value" :key="index">
            <div
              class="flex flex-col justify-center text-gray-500 icon-container"
              style="text-align: center; padding: 10px"
            >
              <!-- <span class="text-center custom-icon" :title="item.icon"> -->
              <span class="text-center custom-icon" :title="item.icon" @click="handerclick(item)">
                <!-- <n-icon :size="50" :color="'#68c755'" @click="handerclick(item)"> -->
                <!-- <DashboardOutlined /> -->
                <component :is="getIcon(item.model_icon)" />
                <!-- </n-icon> -->
              </span>
              <span class="text-center text-lx">{{ item.title || item.model_name }}</span>
            </div>
            <!-- {{ item.title }} -->
          </n-grid-item>
        </n-grid>
      </n-card>
    </div>
  </div>
</template>
<script lang="ts" setup>
  import { onMounted, reactive, ref, computed } from 'vue';
  import { useCrudMenu } from '@/store/modules/crudMenu';
  import { getIcon } from '@/utils/getIconByName';
  import router from '@/router';
  import { CRUD_LIST } from '@/store/consts';
  import { useThemeVars } from 'naive-ui';
  defineOptions({
    name: 'dashboard_console',
  });

  const themeVars = useThemeVars();
  console.log('@@@theme_vars', themeVars.value);
  const themeVarsComputed = computed(() => themeVars.value);

  // const loading = ref(false);
  const crudMenuStore = useCrudMenu();
  let crud_menus = reactive({}); // crud菜单
  const modelInfo = ref<Record<string, any>>({}); // 表示值类型为任意、键值对个数任意的对象形式？
  const appInfo = ref<Record<string, any>>({}); // 表示值类型为任意、键值对个数任意的对象形式？
  function handerclick(item) {
    console.log('item:', item);
    router.push({
      name: CRUD_LIST,
      params: {
        app_name: item.app,
        model_name: item.model_name,
      },
      // query: {
      //   is_edit: 'true',
      // },
      replace: true,
    });
  }
  onMounted(async () => {
    await crudMenuStore.initCrudMenu();
    crud_menus = crudMenuStore.getCrudMenu?.all_models || {};

    for (const key in crud_menus) {
      const model = crud_menus[key];
      // const app_name = model.app_menu_name || model.app;
      const app_name = model.ud_app || model.app;
      const model_name = model.model_menu_name || model.model_name;
      if (!modelInfo.value.hasOwnProperty(app_name)) {
        modelInfo.value[app_name] = []; // 如果不存在，则添加一个空数组
      }
      if (!appInfo.value.hasOwnProperty(app_name)) {
        const { app, app_description, app_icon, app_menu_name, app_name } = model;
        appInfo.value[app_name] = {
          app,
          app_description,
          app_icon,
          app_menu_name,
          app_name,
        }; // 如果不存在，则添加一个空数组
      }
      modelInfo.value[app_name].push({
        ...model,
        size: '32',
        title: model_name,
        color: '#ffc069',
        eventObject: {
          click: () => {},
        },
      });
    }
    console.log('modelInfo:', modelInfo.value);
    console.log('appInfo:', appInfo.value);
  });
</script>

<style lang="less" scoped>
  .project-card {
    margin-right: -6px;

    &-item {
      margin: -1px;
      width: 33.333333%;
    }
  }

  .custom-icon {
    font-size: 50px; /* 使用 font-size 控制图标大小 */
    // color: rgb(0, 186, 254);
    // color: v-bind(active_color);
    color: v-bind('themeVarsComputed.primaryColor');
    transition: all 0.3s ease;

    &:hover {
      transform: scale(1.6);
      // color: #1890ff;
      color: v-bind('themeVarsComputed.primaryColorHover');
      cursor: pointer;
      // box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
  }

  // .icon-container {
  //   background-color: #f0f0f0;
  // }
</style>
