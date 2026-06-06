import { ComponentType } from '../../types/componentType';
import { t } from '@/i18n';

/**
 * @description: 生成placeholder
 */
export function createPlaceholderMessage(component: ComponentType) {
  if (component === 'NInput') return t('form.inputPlaceholder');
  if (
    ['NPicker', 'NSelect', 'NCheckbox', 'NRadio', 'NSwitch', 'NDatePicker', 'NTimePicker'].includes(
      component
    )
  )
    return t('form.selectPlaceholder');
  return '';
}
