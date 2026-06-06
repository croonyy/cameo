import { timestampFormat, getISOStringWithLocalTimezone, getFieldUiName } from './tools';
import {
  DATE_LIKE_FIELD_TYPES,
  DATETIME_LIKE_FIELD_TYPES,
  JSON_LIKE_FIELD_TYPES,
  MANY_RELATION_FIELD_TYPES,
  SINGLE_RELATION_FIELD_TYPES,
} from './types';

export function getObjChangedFields(data_before: Recordable, data_after: Recordable) {
  const changedFields = {};
  for (const key in data_after) {
    if (key in data_before) {
      if (JSON.stringify(data_after[key]) !== JSON.stringify(data_before[key])) {
        changedFields[key] = data_after[key];
      }
    } else {
      changedFields[key] = data_after[key];
    }
  }
  return changedFields;
}

export function getM2mChangeIds(items: any) {
  const add = Array.isArray(items?.add) ? items.add : [];
  const del = Array.isArray(items?.del) ? items.del : [];
  const addIds = add.map((item) => item.value);
  const delIds = del.map((item) => item.value);

  if (addIds.length === 0 && delIds.length === 0) {
    return null;
  }

  return {
    ...(addIds.length > 0 ? { add: addIds } : {}),
    ...(delIds.length > 0 ? { del: delIds } : {}),
  };
}

export const FrontendMod = (data: any, fields_info: any): Recordable => {
  const tmp = { ...data };
  Object.entries(fields_info).forEach(([key, field]: [string, any]) => {
    if (
      DATE_LIKE_FIELD_TYPES.has(field.field_type) ||
      DATETIME_LIKE_FIELD_TYPES.has(field.field_type)
    ) {
      if (tmp[key]) {
        tmp[key] = new Date(tmp[key]).getTime();
      }
    }
    if (JSON_LIKE_FIELD_TYPES.has(field.field_type)) {
      if (typeof tmp[key] === 'object' && tmp[key] !== null) {
        tmp[key] = JSON.stringify(tmp[key], null, 2);
      } else if (typeof tmp[key] === 'string') {
        try {
          tmp[key] = JSON.stringify(JSON.parse(tmp[key]), null, 2);
        } catch {
          // Keep invalid JSON strings as-is.
        }
      }
    }
  });
  return tmp;
};

export const BackendMod = (data: Recordable, fields_info: Recordable): Recordable => {
  const comm = {};
  const m2m = {};
  Object.entries(data).forEach(([key, value]: [string, any]) => {
    const field = fields_info[key] || {};
    if (DATE_LIKE_FIELD_TYPES.has(field.field_type)) {
      if (value) comm[key] = timestampFormat(value, 'yyyy-MM-dd');
    } else if (DATETIME_LIKE_FIELD_TYPES.has(field.field_type)) {
      if (value) comm[key] = getISOStringWithLocalTimezone(value);
    } else if (MANY_RELATION_FIELD_TYPES.has(field.field_type)) {
      m2m[key] = value;
    } else if (SINGLE_RELATION_FIELD_TYPES.has(field.field_type)) {
      comm[field.source_field] = value;
    } else if (JSON_LIKE_FIELD_TYPES.has(field.field_type)) {
      if (value == null) {
        comm[key] = null;
      } else if (typeof value === 'object') {
        comm[key] = value;
      } else {
        try {
          comm[key] = JSON.parse(value);
        } catch (error) {
          console.error(`parse JSON[${key}]: ${value} failed.`, error);
        }
      }
    } else {
      comm[key] = value;
    }
  });
  return { commFields: comm, m2mFields: m2m };
};

function isEmptyValue(value: any) {
  return (
    value === null ||
    value === undefined ||
    value === '' ||
    (Array.isArray(value) && value.length === 0)
  );
}

export function getFormDisplayFields(fieldsInfo: Recordable, ui: Recordable = {}) {
  const allFieldNames = Object.keys(fieldsInfo || {});
  const relationSourceMap = getRelationSourceFieldMap(fieldsInfo);
  const configuredFields = ui?.editable_fields?.length
    ? ui.editable_fields
    : (ui?.list_display || []).includes('*')
    ? allFieldNames
    : ui?.list_display || [];
  const requiredFields = allFieldNames.filter((fieldName) => fieldsInfo[fieldName]?.is_required);
  const excludeFields = new Set(ui?.exclude_fields || []);
  const readonlyFields = new Set(ui?.readonly_fields || []);
  const fields = [...configuredFields, ...requiredFields].map(
    (fieldName) => relationSourceMap[fieldName] || fieldName
  );

  return [...new Set(fields)].filter((fieldName) => {
    const field = fieldsInfo[fieldName];
    const sourceField = field?.source_field;
    return (
      field &&
      !excludeFields.has(fieldName) &&
      !excludeFields.has(sourceField) &&
      !readonlyFields.has(fieldName) &&
      !readonlyFields.has(sourceField) &&
      !field.is_pk &&
      !field.read_only
    );
  });
}

function getRelationSourceFieldMap(fieldsInfo: Recordable) {
  const relationSourceMap: Record<string, string> = {};
  Object.entries(fieldsInfo || {}).forEach(([fieldName, field]: [string, any]) => {
    if (SINGLE_RELATION_FIELD_TYPES.has(field?.field_type) && field.source_field) {
      relationSourceMap[field.source_field] = fieldName;
    }
  });
  return relationSourceMap;
}

export function getFormFieldInfo(fieldsInfo: Recordable, fieldName: string) {
  const field = fieldsInfo[fieldName];
  const sourceField = field?.source_field ? fieldsInfo[field.source_field] : null;
  if (!field || !sourceField) return field;

  return {
    ...field,
    info: {
      ...(sourceField.info || {}),
      ...(field.info || {}),
      ui_name: field.info?.ui_name || sourceField.info?.ui_name,
    },
  };
}

export function createFormRules(fieldsInfo: any, renderedFieldNames?: string[]) {
  const rules = {};
  const fieldNames = renderedFieldNames?.length
    ? renderedFieldNames
    : Object.keys(fieldsInfo || {});
  for (const field_name of fieldNames) {
    const field = fieldsInfo[field_name];
    if (!field) continue;
    const fieldRules: Recordable = [];
    const label = getFieldUiName(field);

    if (field.is_required) {
      const message = `${label} 不能为空`;
      fieldRules.push({
        required: true,
        message,
        trigger: ['blur', 'input', 'change'],
        validator: (_rule: any, value: any) => {
          return isEmptyValue(value) ? new Error(message) : true;
        },
      });
    }

    if (field.choices) {
      const choices = Array.isArray(field.choices) ? field.choices : Object.values(field.choices);
      fieldRules.push({
        trigger: ['blur', 'change'],
        validator: (_rule: any, value: any) => {
          if (isEmptyValue(value)) return true;
          return choices.includes(value) ? true : new Error(`${label} 不在可选值范围内`);
        },
      });
    }

    switch (field.field_type) {
      case 'String':
      case 'Text':
      case 'LargeBinary':
        fieldRules.push({
          trigger: ['blur', 'input'],
          validator: (_rule: any, value: any) => {
            if (isEmptyValue(value)) return true;
            if (typeof value !== 'string') return new Error(`${label} 必须是字符串`);
            if (field.max_length != null && value.length > Number(field.max_length)) {
              return new Error(`${label} 最多 ${field.max_length} 个字符`);
            }
            return true;
          },
        });
        break;
      case 'JSON':
        fieldRules.push({
          validator: (_rule, value) => {
            if (typeof value === 'string' && !isNaN(Number(value))) {
              return new Error(`${label} 必须是有效的JSON`);
            }
            if (value === null || value === undefined || value === '') return true;
            try {
              if (typeof value === 'string') {
                JSON.parse(value);
              } else if (typeof value === 'object') {
                JSON.stringify(value);
              }
              return true;
            } catch (e) {
              return new Error(`${label} 必须是有效的JSON`);
            }
          },
          message: `${label} 必须是有效的JSON`,
          trigger: ['blur', 'input', 'change'],
        });
        break;
      case 'BigInteger':
      case 'Integer':
      case 'SmallInteger':
        fieldRules.push({
          trigger: ['blur', 'input', 'change'],
          validator: (_rule: any, value: any) => {
            if (isEmptyValue(value)) return true;
            return Number.isInteger(Number(value)) ? true : new Error(`${label} 必须是整数`);
          },
        });
        break;
      case 'Float':
      case 'Numeric':
        fieldRules.push({
          trigger: ['blur', 'input'],
          validator: (_rule: any, value: any) => {
            if (isEmptyValue(value)) return true;
            const numericValue = Number(value);
            if (Number.isNaN(numericValue)) return new Error(`${label} 必须是数字`);
            const [integerPart = '', decimalPart = ''] = String(value).replace('-', '').split('.');
            if (field.decimal_places != null && decimalPart.length > Number(field.decimal_places)) {
              return new Error(`${label} 最多 ${field.decimal_places} 位小数`);
            }
            if (
              field.max_digits != null &&
              integerPart.length + decimalPart.length > Number(field.max_digits)
            ) {
              return new Error(`${label} 最多 ${field.max_digits} 位数字`);
            }
            return true;
          },
        });
        break;
      case 'Boolean':
        fieldRules.push({
          trigger: ['blur', 'change'],
          validator: (_rule: any, value: any) => {
            if (isEmptyValue(value)) return true;
            return typeof value === 'boolean' ? true : new Error(`${label} 必须是布尔值`);
          },
        });
        break;
    }
    if (fieldRules.length > 0) {
      rules[field_name] = fieldRules;
    }
  }
  return rules;
}

function getErrorPayload(error: any) {
  return error?.data || error?.response?.data || error;
}

export function getBackendValidationMessage(error: any, fieldsInfo: Recordable = {}) {
  const payload = getErrorPayload(error);
  const errors = payload?.extra?.errors;
  if (!Array.isArray(errors) || errors.length === 0) {
    return error?.message || payload?.msg || payload?.error || 'Validation failed';
  }

  return errors
    .map((item: any) => {
      const loc = Array.isArray(item.loc) ? item.loc : [];
      const fieldName = [...loc]
        .reverse()
        .find((part) => typeof part === 'string' && part !== 'body');
      const field = fieldName ? fieldsInfo[fieldName] : null;
      const label = field ? getFieldUiName(field) : fieldName || loc.join('.');
      const rawMessage = item.msg || item.message || 'Invalid value';
      const message =
        item.type === 'missing' || rawMessage === 'Field required' ? '不能为空' : rawMessage;
      return `${label}: ${message}`;
    })
    .join('; ');
}
