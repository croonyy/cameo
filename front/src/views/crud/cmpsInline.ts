import { computed, h } from 'vue';
import { NCheckbox, NDatePicker, NInput, NInputNumber, NSelect, NTimePicker } from 'naive-ui';
import { buildChoiceOptions, formatChoiceValue, hasChoices, normalizeChoiceValue } from './tools';
import { formatListDisplayValue, translateKnownDataText } from './columnRender';
import {
  BOOLEAN_LIKE_FIELD_TYPES,
  DATE_LIKE_FIELD_TYPES,
  DATETIME_LIKE_FIELD_TYPES,
  JSON_LIKE_FIELD_TYPES,
  NUMBER_LIKE_FIELD_TYPES,
  TEXT_LIKE_FIELD_TYPES,
  TIME_LIKE_FIELD_TYPES,
} from './types';
import { t } from '@/i18n';

type InlineFieldContext = {
  props: any;
  isEditing: any;
  editValue: any;
  inputEl: any;
  startEdit: () => void;
  emitChange: (val: any) => void;
  emitRawChange: (val: any) => void;
  renderAlignedContent: (content: any) => any;
  renderFullWidthEditor: (editor: any) => any;
  getAlignedControlStyle: (width?: string) => string;
  displayTextStyle: string;
  fullWidthTextareaStyle: string;
  getDisplayText: (value: any) => string;
  getJsonDisplayText: (value: any) => string;
  formatDateDisplayValue: (value: any, isDateTime: boolean) => any;
  normalizeDatePickerValue: (value: any, isDateTime: boolean) => string | null;
  normalizeTimePickerValue: (value: any) => string | null;
};

export const InlineFieldComponentMap: Record<string, (ctx: InlineFieldContext) => any> = {
  BooleanField,
  SelectField,
  DateField,
  DatetimeField,
  TimeField,
  NumberComponent,
  JSONField,
  TextField,
  InputField,
};

export function getInlineComponentName(fieldType: string, choices?: any) {
  if (BOOLEAN_LIKE_FIELD_TYPES.has(fieldType)) return 'BooleanField';
  if (hasChoices(choices)) return 'SelectField';
  if (DATETIME_LIKE_FIELD_TYPES.has(fieldType)) return 'DatetimeField';
  if (DATE_LIKE_FIELD_TYPES.has(fieldType)) return 'DateField';
  if (TIME_LIKE_FIELD_TYPES.has(fieldType)) return 'TimeField';
  if (NUMBER_LIKE_FIELD_TYPES.has(fieldType)) return 'NumberComponent';
  if (JSON_LIKE_FIELD_TYPES.has(fieldType)) return 'JSONField';
  if (TEXT_LIKE_FIELD_TYPES.has(fieldType)) return 'TextField';
  return 'InputField';
}

export function getInlineDisplayText(value: any) {
  return formatListDisplayValue(value);
}

export function getInlineJsonDisplayText(value: any) {
  return value === null || value === undefined
    ? formatListDisplayValue(value)
    : JSON.stringify(translateKnownDataText(value));
}

export function BooleanField(ctx: InlineFieldContext) {
  const { props, editValue, emitChange, getDisplayText, renderAlignedContent } = ctx;
  const currentValue = computed(() => !!(editValue.value ?? props.value));
  return () => {
    if (!props.canEdit) {
      return renderAlignedContent(
        h(
          'span',
          {},
          props.value === null || props.value === undefined
            ? getDisplayText(props.value)
            : props.value
            ? t('common.yes')
            : t('common.no')
        )
      );
    }
    return renderAlignedContent(
      h(NCheckbox, {
        checked: currentValue.value,
        onUpdateChecked: (val: boolean) => emitChange(val),
        style: 'transform: scale(0.85);',
      })
    );
  };
}

export function SelectField(ctx: InlineFieldContext) {
  const { props, editValue, emitChange, getAlignedControlStyle, renderAlignedContent } = ctx;
  const selectOptions = buildChoiceOptions(props.choices);
  return () => {
    const currentValue = normalizeChoiceValue(editValue.value ?? props.value, props.choices);
    if (!props.canEdit) {
      return renderAlignedContent(h('span', {}, formatChoiceValue(currentValue, props.choices)));
    }
    return renderAlignedContent(
      h(NSelect, {
        value: currentValue,
        options: selectOptions,
        size: 'small',
        style: `${getAlignedControlStyle('70%')}min-width:80px;max-width:300px;`,
        consistentMenuWidth: false,
        onUpdateValue: (val: any) => emitChange(val),
      })
    );
  };
}

export function DateField(ctx: InlineFieldContext) {
  return dateLikeField(ctx, false);
}

export function DatetimeField(ctx: InlineFieldContext) {
  return dateLikeField(ctx, true);
}

function dateLikeField(ctx: InlineFieldContext, isDateTime: boolean) {
  const {
    props,
    editValue,
    inputEl,
    isEditing,
    emitChange,
    startEdit,
    displayTextStyle,
    formatDateDisplayValue,
    getAlignedControlStyle,
    getDisplayText,
    normalizeDatePickerValue,
    renderAlignedContent,
  } = ctx;
  const valueFormat = isDateTime ? 'yyyy-MM-dd HH:mm:ss' : 'yyyy-MM-dd';
  return () => {
    if (!props.canEdit) {
      return renderAlignedContent(
        h('span', {}, getDisplayText(formatDateDisplayValue(props.value, isDateTime)))
      );
    }
    if (isEditing.value) {
      return h(NDatePicker, {
        ref: inputEl,
        formattedValue: normalizeDatePickerValue(editValue.value ?? props.value, isDateTime),
        valueFormat,
        type: isDateTime ? 'datetime' : 'date',
        format: valueFormat,
        size: 'small',
        style: getAlignedControlStyle('100%'),
        onUpdateFormattedValue: (val: string | null) => emitChange(val),
      });
    }
    const displayVal = getDisplayText(formatDateDisplayValue(props.value, isDateTime));
    return h(
      'span',
      {
        style: `${displayTextStyle}text-align:${props.align};`,
        onDblclick: startEdit,
      },
      displayVal
    );
  };
}

export function TimeField(ctx: InlineFieldContext) {
  const {
    props,
    editValue,
    inputEl,
    isEditing,
    emitChange,
    startEdit,
    displayTextStyle,
    getAlignedControlStyle,
    getDisplayText,
    normalizeTimePickerValue,
    renderAlignedContent,
  } = ctx;
  return () => {
    if (!props.canEdit) {
      return renderAlignedContent(h('span', {}, getDisplayText(props.value)));
    }
    if (isEditing.value) {
      return h(NTimePicker, {
        ref: inputEl,
        formattedValue: normalizeTimePickerValue(editValue.value ?? props.value),
        valueFormat: 'HH:mm:ss',
        format: 'HH:mm:ss',
        size: 'small',
        style: getAlignedControlStyle('100%'),
        onUpdateFormattedValue: (val: string | null) => emitChange(val),
      });
    }
    const displayVal = getDisplayText(props.value);
    return h(
      'span',
      {
        style: `${displayTextStyle}text-align:${props.align};`,
        onDblclick: startEdit,
      },
      displayVal
    );
  };
}

export function NumberComponent(ctx: InlineFieldContext) {
  const {
    props,
    editValue,
    inputEl,
    isEditing,
    emitChange,
    startEdit,
    displayTextStyle,
    getAlignedControlStyle,
    getDisplayText,
  } = ctx;
  return () => {
    if (!props.canEdit) {
      return h('span', {}, getDisplayText(props.value));
    }
    if (isEditing.value) {
      return h(NInputNumber, {
        ref: inputEl,
        value: editValue.value ?? props.value,
        size: 'small',
        style: getAlignedControlStyle('100%'),
        showButton: false,
        onUpdateValue: (val: number | null) => emitChange(val),
      });
    }
    const displayVal = getDisplayText(props.value);
    return h(
      'span',
      {
        style: `${displayTextStyle}text-align:${props.align};`,
        onDblclick: startEdit,
      },
      displayVal
    );
  };
}

export function JSONField(ctx: InlineFieldContext) {
  const {
    props,
    editValue,
    inputEl,
    isEditing,
    emitRawChange,
    startEdit,
    displayTextStyle,
    fullWidthTextareaStyle,
    getJsonDisplayText,
    renderFullWidthEditor,
  } = ctx;
  return () => {
    if (!props.canEdit) {
      return h('span', {}, getJsonDisplayText(props.value));
    }
    if (isEditing.value) {
      return renderFullWidthEditor(
        h(NInput, {
          ref: inputEl,
          value:
            editValue.value != null
              ? typeof editValue.value === 'object'
                ? JSON.stringify(editValue.value, null, 2)
                : String(editValue.value)
              : '',
          type: 'textarea',
          size: 'small',
          rows: 2,
          class: 'inline-textarea-editor',
          style: fullWidthTextareaStyle,
          onUpdateValue: (val: string) => {
            editValue.value = val;
            try {
              emitRawChange(JSON.parse(val));
            } catch {
              emitRawChange(val);
            }
          },
        })
      );
    }
    const displayVal = getJsonDisplayText(props.value);
    return h(
      'span',
      {
        style: `${displayTextStyle}font-size:12px;`,
        onDblclick: startEdit,
      },
      displayVal
    );
  };
}

export function TextField(ctx: InlineFieldContext) {
  const {
    props,
    editValue,
    inputEl,
    isEditing,
    emitChange,
    startEdit,
    displayTextStyle,
    fullWidthTextareaStyle,
    getDisplayText,
    renderFullWidthEditor,
  } = ctx;
  return () => {
    if (!props.canEdit) {
      return h('span', {}, getDisplayText(props.value));
    }
    if (isEditing.value) {
      return renderFullWidthEditor(
        h(NInput, {
          ref: inputEl,
          value: editValue.value ?? props.value ?? '',
          type: 'textarea',
          size: 'small',
          rows: 2,
          class: 'inline-textarea-editor',
          style: fullWidthTextareaStyle,
          onUpdateValue: (val: string) => emitChange(val),
        })
      );
    }
    const displayVal = getDisplayText(props.value);
    return h(
      'span',
      {
        style: displayTextStyle,
        onDblclick: startEdit,
      },
      displayVal
    );
  };
}

export function InputField(ctx: InlineFieldContext) {
  const {
    props,
    editValue,
    inputEl,
    isEditing,
    emitChange,
    startEdit,
    displayTextStyle,
    getDisplayText,
  } = ctx;
  return () => {
    if (isEditing.value && props.canEdit) {
      return h(NInput, {
        ref: inputEl,
        value: editValue.value ?? props.value ?? '',
        size: 'small',
        style: 'width:100%;',
        onUpdateValue: (val: string) => emitChange(val),
      });
    }
    const displayVal = getDisplayText(props.value);
    return h(
      'span',
      {
        style: props.canEdit ? `${displayTextStyle}text-align:${props.align};` : '',
        onDblclick: startEdit,
      },
      displayVal
    );
  };
}
