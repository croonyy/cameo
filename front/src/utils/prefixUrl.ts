import { useGlobSetting } from '@/hooks/setting';
const { urlPrefix } = useGlobSetting();

export function preurl(urlstr: string) {
  return `${urlPrefix}${urlstr}`;
}
