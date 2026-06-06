import { h } from 'vue';
import { NIcon } from 'naive-ui';
import { getFieldUiName } from './tools';
import {
  NumberOutlined,
  FieldBinaryOutlined,
  CheckCircleOutlined,
  FieldNumberOutlined,
  FieldStringOutlined,
  CalendarOutlined,
  FieldTimeOutlined,
  FileTextOutlined,
  CodeOutlined,
  FileUnknownOutlined,
  UnorderedListOutlined,
  DatabaseOutlined,
} from '@vicons/antd';
import { t } from '@/i18n';

export const fieldTypeIcons: Record<string, any> = {
  BigInteger: NumberOutlined,
  Boolean: CheckCircleOutlined,
  Date: CalendarOutlined,
  DateTime: FieldTimeOutlined,
  Float: FieldNumberOutlined,
  Integer: NumberOutlined,
  JSON: CodeOutlined,
  LargeBinary: FieldBinaryOutlined,
  Numeric: FieldNumberOutlined,
  SmallInteger: NumberOutlined,
  String: FieldStringOutlined,
  Text: FileTextOutlined,
  ForeignKeyField: DatabaseOutlined,
  OneToOneField: DatabaseOutlined,
  ManyToManyField: UnorderedListOutlined,
  BackwardFKRelation: DatabaseOutlined,
  Default: FileUnknownOutlined,
};

type ColumnRenderer = (field: any) => Recordable;
type ColumnAlign = 'left' | 'center' | 'right';

const UI_ALIGN_MAP: Record<string, ColumnAlign> = {
  L: 'left',
  R: 'right',
  M: 'center',
};

const RELATION_FIELD_TYPES = new Set([
  'BackwardFKRelation',
  'ForeignKeyField',
  'ManyToManyField',
  'OneToOneField',
]);

const CENTER_FIELD_TYPES = new Set([
  'Boolean',
  'Date',
  'DateTime',
  'Time',
  ...RELATION_FIELD_TYPES,
]);

function getFieldTypeIcon(fieldType: string) {
  return fieldTypeIcons[fieldType] || fieldTypeIcons.Default;
}

export function getFieldAlign(field: any): ColumnAlign {
  const uiAlign = String(field?.info?.ui_align || '').toUpperCase();
  if (uiAlign in UI_ALIGN_MAP) {
    return UI_ALIGN_MAP[uiAlign];
  }
  if (CENTER_FIELD_TYPES.has(field.field_type) || field?.choices) {
    return 'center';
  }
  return 'right';
}

export function renderIconTitle(field: any) {
  const IconComponent = getFieldTypeIcon(field.field_type);
  return h('div', { style: 'display: flex; align-items: center;' }, [
    h(
      NIcon,
      { size: 16, style: 'margin-right: 5px;', title: field.field_type },
      { default: () => h(IconComponent, { style: 'color: var(--app-primary-color, #18a058);' }) }
    ),
    getFieldUiName(field),
  ]);
}

function createColumn(field: any, options: Recordable = {}) {
  const align = getFieldAlign(field);
  const titleText = getFieldUiName(field);
  return {
    title: renderIconTitle(field),
    titleText,
    key: field.field_name,
    resizable: true,
    align,
    ...options,
  };
}

export function formatListDisplayValue(value: any) {
  if (value === null) return '∅';
  if (value === '') return '-';
  if (value === undefined) return '?';
  return String(value);
}

const KNOWN_DATA_TEXT_KEYS: Record<string, string> = {
  系统配置: 'data.configDescription.system',
  安全配置: 'data.configDescription.security',
  界面配置: 'data.configDescription.ui',
  存储配置: 'data.configDescription.storage',
  集成配置: 'data.configDescription.integration',
};

export function translateKnownDataText(value: any): any {
  if (typeof value === 'string') {
    const key = KNOWN_DATA_TEXT_KEYS[value];
    return key ? t(key) : value;
  }
  if (Array.isArray(value)) {
    return value.map((item) => translateKnownDataText(item));
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, translateKnownDataText(item)])
    );
  }
  return value;
}

const booleanColumn: ColumnRenderer = (field) =>
  createColumn(field, {
    sorter: true,
    render: (row) => {
      const value = row[field.field_name];
      if (value === null || value === undefined) return formatListDisplayValue(value);
      return value ? t('common.yes') : t('common.no');
    },
  });

const jsonColumn: ColumnRenderer = (field) =>
  createColumn(field, {
    render: (row) => {
      const value = row[field.field_name];
      return value === null || value === undefined
        ? formatListDisplayValue(value)
        : JSON.stringify(translateKnownDataText(value));
    },
  });

const forwardRelationColumn: ColumnRenderer = (field) =>
  createColumn(field, {
    render: (row) =>
      formatListDisplayValue(row[`_${field.field_name}_str`] ?? row[field.source_field]),
  });

const reverseRelationColumn: ColumnRenderer = (field) =>
  createColumn(field, {
    render: (row) => formatListDisplayValue(row[`_${field.field_name}_str`]),
  });

const defaultColumn: ColumnRenderer = (field) =>
  createColumn(field, {
    sorter: true,
    render: (row) => formatListDisplayValue(row[field.field_name]),
  });

export const columnRenderMap: Record<string, ColumnRenderer> = {
  BigInteger: defaultColumn,
  Boolean: booleanColumn,
  Date: defaultColumn,
  DateTime: defaultColumn,
  Float: defaultColumn,
  Integer: defaultColumn,
  JSON: jsonColumn,
  LargeBinary: defaultColumn,
  Numeric: defaultColumn,
  SmallInteger: defaultColumn,
  String: defaultColumn,
  Text: defaultColumn,
  ForeignKeyField: forwardRelationColumn,
  OneToOneField: forwardRelationColumn,
  ManyToManyField: reverseRelationColumn,
  BackwardFKRelation: reverseRelationColumn,
  default: defaultColumn,
};
