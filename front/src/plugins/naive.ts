import type { App } from 'vue';
import {
  create,
  // Provider 组件（必须全局注册）
  NMessageProvider,
  NDialogProvider,
  NNotificationProvider,
  NLoadingBarProvider,
  // 以下组件通过 h() 或动态 :is 渲染，自动按需引入无法识别，需全局注册
  NIcon,
  NCheckbox,
  NSelect,
  NDatePicker,
  NInputNumber,
  NInput,
  NAutoComplete,
  NSwitch,
} from 'naive-ui';

/**
 * Naive UI 组件注册
 *
 * - Provider 组件必须全局注册
 * - 通过 h() 函数或动态 :is 绑定字符串渲染的组件，自动按需引入无法识别，需要全局注册
 * - 其他组件通过 unplugin-vue-components 按需自动引入
 */
const naive = create({
  components: [
    // 必须全局注册的 Provider 组件
    NMessageProvider,
    NDialogProvider,
    NNotificationProvider,
    NLoadingBarProvider,
    // h() / 动态 :is 使用的组件
    NIcon,
    NCheckbox,
    NSelect,
    NDatePicker,
    NInputNumber,
    NInput,
    NAutoComplete,
    NSwitch,
  ],
});

export function setupNaive(app: App<Element>) {
  app.use(naive);
}
