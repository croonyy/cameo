import { Alova } from '@/utils/http/alova';

//获取table
export function getTableList(params) {
  return Alova.Get('/table/list', { params });
}
