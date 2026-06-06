import { Alova } from '@/utils/http/alova';
import { preurl } from '@/utils/prefixUrl';

/**
 * @description: 获取用户信息
 */
export function Test() {
  return Alova.Get<InResult>(
    // '/admin_info',
    preurl('/test/test'),
    {
      meta: {
        isReturnNativeResponse: true,
      },
    }
  );
}
/**
 * @description: 获取用户信息
 */
export function getUserInfo() {
  return Alova.Get<InResult>(
    // '/admin_info',
    preurl('/udadmin/security/me'),
    {
      meta: {
        isReturnNativeResponse: true,
      },
    }
  );
}

/**
 * @description: 用户登录
 */
export function login(params) {
  return Alova.Post<InResult>(
    // '/login',
    preurl('/udadmin/security/token'),
    params,
    {
      meta: {
        isReturnNativeResponse: true,
        // authRole: null, // 登录接口不需要token认证拦截
        authRole: 'login',
      },
    }
  );
}

/**
 * @description: 刷新token
 */
export function refresh(params) {
  return Alova.Post<InResult>(
    // '/login',
    preurl('/udadmin/security/refresh'),
    params,
    {
      meta: {
        isReturnNativeResponse: true,
        authRole: 'refreshToken', // 加上这个才能处理refreshToken的拦截
        isVisitor: true, // 访客api，不需要token认证
      },
    }
  );
}

/**
 * @description: 用户修改密码
 */
export function changePassword(params, uid) {
  return Alova.Post(`/user/u${uid}/changepw`, { params });
}

/**
 * @description: 用户登出
 */
export function logout(params) {
  return Alova.Post('/login/logout', {
    params,
  });
}
