import { createAlova } from 'alova';
import VueHook from 'alova/vue';
import adapterFetch from 'alova/fetch';
import { createAlovaMockAdapter } from '@alova/mock';
import { createServerTokenAuthentication } from 'alova/client';
import mocks from './mocks';
import { useUser } from '@/store/modules/user';
import { useGlobSetting } from '@/hooks/setting';
import router from '@/router';
import { getLanguage, t } from '@/i18n';

function getResponseErrorMessage(res: any, fallback = t('common.requestError')) {
  if (!res) return fallback;
  if (typeof res === 'string') return res;
  if (typeof res.error === 'string') return res.error;
  if (typeof res.message === 'string') return res.message;
  if (typeof res.msg === 'string') return res.msg;
  if (typeof res.detail === 'string') return res.detail;
  if (res.error && typeof res.error.message === 'string') return res.error.message;
  return fallback;
}

const showLoginExpiredDialog = () => {
  window.$dialog?.warning({
    title: t('auth.loginExpiredTitle'),
    content: t('auth.loginExpiredContent'),
    positiveText: t('common.confirm'),
    closable: false,
    maskClosable: false,
    onPositiveClick: () => {
      router.push({ name: 'Login' });
    },
  });
};

const { onAuthRequired, onResponseRefreshToken } = createServerTokenAuthentication({
  visitorMeta: {
    isVisitor: true,
  },

  assignToken: (method) => {
    const userStore = useUser();
    const token = userStore.getToken;
    method.config.headers = method.config.headers || {};
    method.config.headers['Accept-Language'] = getLanguage();
    if (!method.meta?.ignoreToken && token) {
      method.config.headers.token = token;
      method.config.headers.Authorization = `Bearer ${token}`;
    }
  },

  refreshTokenOnSuccess: {
    isExpired: (response) => response.status === 401,

    handler: async () => {
      const userStore = useUser();
      try {
        await userStore.refreshToken();
      } catch (err) {
        userStore.logout();
        showLoginExpiredDialog();
        throw err;
      }
    },
  },
});

const { useMock, apiUrl } = useGlobSetting();

const mockAdapter = createAlovaMockAdapter([...mocks], {
  mockRequestLogger: false,
  enable: useMock,
  httpAdapter: adapterFetch(),
  delay: 600,
  onMockError(error, method) {
    console.error('Mock API error:', method.url, error);
  },
});

export const Alova = createAlova({
  baseURL: apiUrl,
  statesHook: VueHook,
  timeout: 10000,
  cacheFor: null,
  cacheLogger: import.meta.env.DEV,
  requestAdapter: mockAdapter,

  beforeRequest: onAuthRequired((method) => {
    method.config.headers = method.config.headers || {};
    method.config.headers['Accept-Language'] = getLanguage();
    if (import.meta.env.DEV) {
      console.log(`[Alova] ${method.type} ${method.url}`);
    }
  }),

  responded: onResponseRefreshToken({
    async onSuccess(response, method) {
      const res = await response.json().catch(() => null);
      if (!res) {
        throw new Error(t('common.requestError'));
      }

      if (!response.ok) {
        const message = getResponseErrorMessage(res);
        window.$message?.error(message);
        const error: any = new Error(message);
        error.code = res.code;
        error.data = res;
        error.extra = res.extra;
        error.response = response;
        throw error;
      }

      if (method.meta?.isReturnNativeResponse) {
        return res;
      }

      return res.data ?? res;
    },

    async onError(error) {
      console.error('Alova request error:', error);
      window.$message?.error(
        getResponseErrorMessage((error as any)?.data, (error as any)?.message || t('common.requestFailed'))
      );
      throw error;
    },
  }),
});
