import { Alova } from '@/utils/http/alova';

/**
 * @description: 角色列表
 */
export function getRoleList(params) {
  return Alova.Get('/role/list', { params });
}
