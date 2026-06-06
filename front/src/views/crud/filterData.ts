import { search_component_key } from './cmpsSearch';
import { timestampFormat } from './tools';
import {
  BOOLEAN_LIKE_FIELD_TYPES,
  DATE_OR_DATETIME_FIELD_TYPES,
  JSON_LIKE_FIELD_TYPES,
  STRING_LIKE_FIELD_TYPES,
  TIME_LIKE_FIELD_TYPES,
} from './types';

export const selectorFilterSymbols = new Map<string, 'eq' | 'icontains'>();
export const EMPTY_STRING_FILTER_VALUE = "''";
export const NULL_FILTER_VALUE = 'null';
export const NULL_FILTER_LABEL = '\u2205';

export function isEmptyValueFilterOption(value: any) {
  return (
    value === EMPTY_STRING_FILTER_VALUE ||
    value === NULL_FILTER_VALUE ||
    value === NULL_FILTER_LABEL
  );
}

export function normalizeEmptyValueFilterOption(value: any) {
  if (value === EMPTY_STRING_FILTER_VALUE) return '';
  if (value === NULL_FILTER_VALUE || value === NULL_FILTER_LABEL) return null;
  return value;
}

function getFilterFieldName(fieldName: string, field: any, value: any) {
  if ((value === NULL_FILTER_VALUE || value === NULL_FILTER_LABEL) && field?.source_field) {
    return field.source_field;
  }
  return fieldName;
}

function createEmptyValueFilter(fieldName: string, field: any, value: any): FilterCondition {
  const filterFieldName = getFilterFieldName(fieldName, field, value);

  if (value === NULL_FILTER_VALUE || value === NULL_FILTER_LABEL) {
    return {
      field: filterFieldName,
      symbol: 'isnull',
      value: true,
    };
  }

  return {
    field: filterFieldName,
    symbol: 'eq',
    value: normalizeEmptyValueFilterOption(value),
  };
}

export function GenerateFilter(values: any, modelInfo: any) {
  const searchFilters: FilterGroup[] = [];
  const fieldFilters: FilterElement[] = [];

  for (const [field_name, value] of Object.entries(values)) {
    if (!value) continue;
    const field = modelInfo.value.fields_info[field_name];
    const search_fields = modelInfo.value.ui.search_fields;
    if (field_name === search_component_key) {
      const querys: FilterCondition[] = search_fields.map((item) => {
        return { field: item, symbol: 'icontains', value };
      });
      if (querys.length > 0) {
        searchFilters.push(['or', ...querys] as FilterGroup);
      }
      continue;
    }
    if (!field) continue;
    if (isEmptyValueFilterOption(value)) {
      fieldFilters.push(createEmptyValueFilter(field_name, field, value));
      continue;
    }

    if (STRING_LIKE_FIELD_TYPES.has(field.field_type)) {
      fieldFilters.push({
        field: field_name,
        symbol: selectorFilterSymbols.get(field_name) || 'icontains',
        value,
      });
    }
    if (JSON_LIKE_FIELD_TYPES.has(field.field_type)) {
      fieldFilters.push({
        field: field_name,
        symbol: 'icontains',
        value,
      });
    }
    if (DATE_OR_DATETIME_FIELD_TYPES.has(field.field_type)) {
      if (!Array.isArray(value)) continue;
      const new_value = value.map((item: any) => timestampFormat(item));
      const [start, end] = new_value;
      if (start && end) {
        fieldFilters.push({
          field: field_name,
          symbol: 'range',
          value: [start, end],
        });
      }
    }
    if (BOOLEAN_LIKE_FIELD_TYPES.has(field.field_type)) {
      fieldFilters.push({
        field: field_name,
        symbol: 'eq',
        value: value == 'true' ? true : false,
      });
    }
    if (TIME_LIKE_FIELD_TYPES.has(field.field_type)) {
      if (!Array.isArray(value)) continue;
      const [start, end] = value;
      if (start && end) {
        fieldFilters.push({
          field: field_name,
          symbol: 'range',
          value: [start, end],
        });
      }
    }
  }

  if (searchFilters.length || fieldFilters.length) {
    return ['and', ...searchFilters, ...fieldFilters] as FilterGroup;
  }
  return [];
}
