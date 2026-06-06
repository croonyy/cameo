import { renderIcon } from '@/utils/index';
import * as antd from '@vicons/antd';
import * as ionicons5 from '@vicons/ionicons5';

const iconsGroup = {
  antd,
  ionicons5,
};

export function getIcon(tag: String) {
  // Default icon if tag is invalid
  const defaultIcon = ['ionicons5', 'Cube'];

  // Only process tag if it exists and can be split into exactly 2 parts
  const names =
    tag && typeof tag === 'string' && tag.split(':').length === 2 ? tag.split(':') : defaultIcon;

  const [icon_group, icon_name] = names;

  // Return icon if exists in group, otherwise return default
  return renderIcon(
    iconsGroup[icon_group]?.[icon_name] || iconsGroup[defaultIcon[0]][defaultIcon[1]]
  );
}
