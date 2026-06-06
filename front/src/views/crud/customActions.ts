import type { Router, RouteLocationNormalizedLoaded } from 'vue-router';
import type { MessageApi } from 'naive-ui';
import { Alova } from '@/utils/http/alova';
import { preurl } from '@/utils/prefixUrl';

export interface CustomActionConfig {
  key: string;
  label: string;
  action_key: string;
  placement?: 'row' | 'toolbar';
  icon?: string;
  type?: 'success' | 'error' | 'warning' | 'info' | 'primary' | 'default';
  permission?: string;
  url?: string;
  param?: 'id' | 'record';
  confirm?: boolean | { title?: string; content?: string };
  show_if?: CustomActionCondition | CustomActionCondition[];
  disabled_if?: CustomActionCondition | CustomActionCondition[];
}

export interface CustomActionCondition {
  field: string;
  op?: 'eq' | 'ne' | 'in' | 'not_in' | 'empty' | 'not_empty' | 'truthy' | 'falsy';
  value?: any;
}

export interface CustomActionContext {
  action: CustomActionConfig;
  appName: string;
  modelName: string;
  record?: Recordable;
  selectedRowKeys: Array<string | number>;
  selectedRows: Recordable[];
  rows: Recordable[];
  filters: any[];
  sorter: any;
  pagination: Recordable;
  modelInfo: Recordable;
  route: RouteLocationNormalizedLoaded;
  router: Router;
  message: MessageApi;
  reload: () => Promise<void>;
}

type CustomActionHandler = (context: CustomActionContext) => void | Promise<void>;

function getRowId(record?: Recordable) {
  return record?.id;
}

function getActionParamValue(context: CustomActionContext) {
  const param = context.action.param || 'record';
  if ((context.action.placement || 'row') === 'toolbar') {
    return param === 'id' ? context.selectedRowKeys : context.selectedRows;
  }
  return param === 'id' ? getRowId(context.record) : context.record;
}

async function postCustomAction(context: CustomActionContext) {
  const payload = {
    key: context.action.key,
    action_key: context.action.action_key,
    placement: context.action.placement || 'row',
    param: context.action.param || 'record',
    value: getActionParamValue(context),
  };
  const res = await Alova.Post<InResult>(preurl(context.action.url as string), payload, {
    meta: {
      isReturnNativeResponse: true,
    },
  });
  context.message.success(res?.msg || `${context.action.label}执行成功`);
  return res;
}

const registry: Record<string, CustomActionHandler> = {
  'demo.detail.preview_row': ({ record, message }) => {
    const title = record?.char_field || record?.id || '当前记录';
    message.info(`明细模型行按钮：${title}`);
  },
  'demo.detail.show_context': ({ rows, selectedRowKeys, filters, pagination, message }) => {
    message.info(
      `当前页 ${rows.length} 条，已选 ${selectedRowKeys.length} 条，筛选 ${filters.length} 项，页码 ${
        pagination?.page || 1
      }`
    );
  },
};

export async function executeCustomAction(context: CustomActionContext) {
  if (context.action.url) {
    await postCustomAction(context);
    return;
  }
  const handler = registry[context.action.action_key];
  if (!handler) {
    context.message.warning(`未注册的自定义动作：${context.action.action_key}`);
    return;
  }
  await handler(context);
}
