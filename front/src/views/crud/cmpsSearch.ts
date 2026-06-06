import { getFieldUiName } from './tools';
import { t } from '@/i18n';

export const search_component_key = '__search_value__';

export function SearchFieldComponent(fields: any[]) {
  const names = fields.map((field) => getFieldUiName(field)).join('、');
  const placeholder = t('form.keywordSearchPlaceholder', { fields: names });
  return {
    field: search_component_key,
    component: 'NInput',
    label: t('form.searchLabel'),
    componentProps: {
      placeholder,
      title: placeholder,
    },
  };
}
