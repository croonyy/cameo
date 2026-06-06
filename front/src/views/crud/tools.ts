import { t } from '@/i18n';

const MAX_COLUMN_WIDTH = 800;
const MIN_COLUMN_WIDTH = 112;
const ACTION_COLUMN_WIDTH = 148;

const padZero = (value: number): string => {
  return value < 10 ? `0${value}` : String(value);
};

export function getFieldInfo(field: any) {
  return field?.info || {};
}

export function getFieldUiName(field: any) {
  const uiName = getFieldInfo(field).ui_name || field.field_name;
  const key = field?.field_name ? `uiField.${field.field_name}` : '';
  const translated = key ? t(key) : key;
  if (translated !== key) return translated;
  return uiName;
}

export function getFieldUiDescription(field: any) {
  return getFieldInfo(field).ui_desc || '';
}

export function getFieldUiOrder(field: any) {
  return getFieldInfo(field).ui_order;
}

export function buildChoiceOptions(choices: any) {
  if (choices && !Array.isArray(choices) && typeof choices === 'object') {
    return Object.entries(choices).map(([label, value]) => ({ label, value }));
  }

  return (choices || []).map((choice: any) => {
    if (choice && typeof choice === 'object') {
      const label = choice.label ?? choice.key ?? choice.name ?? choice.value;
      const value = choice.value ?? choice.key ?? choice.name ?? label;
      return { label: String(label), value };
    }

    return { label: String(choice), value: choice };
  });
}

export function hasChoices(choices: any) {
  return buildChoiceOptions(choices).length > 0;
}

export function normalizeChoiceValue(value: any, choices: any) {
  const options = buildChoiceOptions(choices);

  if (options.some((option) => option.value === value)) {
    return value;
  }

  const numericValue = Number(value);
  if (Number.isInteger(numericValue) && numericValue >= 1 && numericValue <= options.length) {
    return options[numericValue - 1].value;
  }

  return value;
}

export function formatChoiceValue(value: any, choices: any) {
  const normalizedValue = normalizeChoiceValue(value, choices);
  const option = buildChoiceOptions(choices).find((item) => item.value === normalizedValue);

  if (option) return option.label;
  if (normalizedValue === null) return '∅';
  if (normalizedValue === '') return '-';
  if (normalizedValue === undefined) return '?';
  return String(normalizedValue);
}

export const timestampFormat = (timestamp: number, format = 'yyyy-MM-dd HH:mm:ss'): string => {
  const date = new Date(timestamp);

  const formatMap = {
    yyyy: date.getFullYear(),
    MM: padZero(date.getMonth() + 1),
    M: date.getMonth() + 1,
    dd: padZero(date.getDate()),
    d: date.getDate(),
    HH: padZero(date.getHours()),
    H: date.getHours(),
    mm: padZero(date.getMinutes()),
    m: date.getMinutes(),
    ss: padZero(date.getSeconds()),
    s: date.getSeconds(),
  };

  return format.replace(/yyyy|MM|M|dd|d|HH|H|mm|m|ss|s/g, (match) => {
    return String(formatMap[match as keyof typeof formatMap]);
  });
};

export function getISOStringWithLocalTimezone(timestamp: number) {
  const date = new Date(timestamp);
  const timezoneOffsetMinutes = date.getTimezoneOffset();
  const adjustedDate = new Date(date.getTime() - timezoneOffsetMinutes * 60000);
  const isoString = adjustedDate.toISOString().replace(/\.\d{3}/, '');
  const timezoneOffset =
    timezoneOffsetMinutes <= 0
      ? `+${String(Math.floor(Math.abs(timezoneOffsetMinutes) / 60)).padStart(2, '0')}:${String(
          Math.abs(timezoneOffsetMinutes) % 60
        ).padStart(2, '0')}`
      : `-${String(Math.floor(timezoneOffsetMinutes / 60)).padStart(2, '0')}:${String(
          timezoneOffsetMinutes % 60
        ).padStart(2, '0')}`;

  return isoString.replace('Z', timezoneOffset);
}

export function getTextWidth(text: string) {
  return Array.from(text).reduce((width, char) => {
    return width + (/[\u4e00-\u9fa5]/.test(char) ? 16 : 9);
  }, 0);
}

export function getTitleText(title: any, fallback: any): string {
  if (typeof title === 'string' || typeof title === 'number') {
    return String(title);
  }
  if (typeof title === 'function') {
    return getTitleText(title(), fallback);
  }
  if (Array.isArray(title)) {
    return title.map((item) => getTitleText(item, '')).join('');
  }
  if (title && typeof title === 'object') {
    return getTitleText(title.children, fallback);
  }
  return fallback != null ? String(fallback) : '';
}

export function getColumnWidth(column: any, rows: Recordable[]) {
  if (typeof column.width === 'number') return Math.min(column.width, MAX_COLUMN_WIDTH);
  if (typeof column.minWidth === 'number') return Math.min(column.minWidth, MAX_COLUMN_WIDTH);
  if (column.key === 'action') return Number(column.width || ACTION_COLUMN_WIDTH);

  const title = getTitleText(column.title, column.key);
  const titleWidth = Math.max(getTextWidth(title), getTextWidth(String(column.key || '')));
  const contentWidth = Math.max(
    0,
    ...rows.slice(0, 20).map((row) => {
      const value = row?.[column.key];
      return getTextWidth(value == null ? '' : String(value));
    })
  );
  const headerControlsWidth =
    30 + (column.sorter ? 26 : 0) + (column.resizable ? 16 : 0) + (column.edit ? 20 : 0);

  return Math.min(
    Math.max(Math.max(titleWidth + headerControlsWidth, contentWidth + 16), MIN_COLUMN_WIDTH),
    MAX_COLUMN_WIDTH
  );
}
