import './styles/tailwind.css';
import './styles/index.less';
import './styles/udcss.css';
import { createApp } from 'vue';
import { setupNaiveDiscreteApi, setupNaive, setupDirectives } from '@/plugins';
import App from './App.vue';
import router, { setupRouter } from './router';
import { setupStore } from '@/store';
import { setupSettingPersistence } from '@/store/modules/projectSetting';
import { setupDesignSettingPersistence } from '@/store/modules/designSetting';
import './assets/css/udTheme.css';
import { initI18n } from '@/i18n';

async function bootstrap() {
  const app = createApp(App);
  initI18n();

  // 挂载状态管理
  setupStore(app);

  // 启用设置持久化（自动监听设置变化并保存到 localStorage）
  setupSettingPersistence();
  setupDesignSettingPersistence();

  // 注册全局常用的 naive-ui 组件
  setupNaive(app);

  // 挂载 naive-ui 脱离上下文的 Api
  setupNaiveDiscreteApi();

  // 注册全局自定义组件
  //setupCustomComponents();

  // 注册全局自定义指令，如：v-permission权限指令
  setupDirectives(app);

  // 注册全局方法，如：app.config.globalProperties.$message = message
  //setupGlobalMethods(app);

  // 挂载路由
  setupRouter(app);

  // 路由准备就绪后挂载 APP 实例
  // https://router.vuejs.org/api/interfaces/router.html#isready
  await router.isReady();

  // https://www.naiveui.com/en-US/os-theme/docs/style-conflict#About-Tailwind's-Preflight-Style-Override
  const meta = document.createElement('meta');
  meta.name = 'naive-ui-style';
  document.head.appendChild(meta);

  app.mount('#app', true);
}

void bootstrap();
