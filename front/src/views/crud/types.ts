export const STRING_LIKE_FIELD_TYPES = new Set([
  'Integer',
  'BigInteger',
  'SmallInteger',
  'String',
  'Text',
  'Enum',
  'Float',
  'LargeBinary',
  'Numeric',
]);

export const JSON_LIKE_FIELD_TYPES = new Set(['JSON']);

export const DATE_LIKE_FIELD_TYPES = new Set(['Date']);

export const DATETIME_LIKE_FIELD_TYPES = new Set(['DateTime']);

export const DATE_OR_DATETIME_FIELD_TYPES = new Set([
  ...DATE_LIKE_FIELD_TYPES,
  ...DATETIME_LIKE_FIELD_TYPES,
]);

export const TIME_LIKE_FIELD_TYPES = new Set(['Time']);

export const BOOLEAN_LIKE_FIELD_TYPES = new Set(['Boolean']);

export const INTEGER_LIKE_FIELD_TYPES = new Set(['BigInteger', 'Integer', 'SmallInteger']);

export const NUMBER_LIKE_FIELD_TYPES = new Set([...INTEGER_LIKE_FIELD_TYPES, 'Float', 'Numeric']);

export const TEXT_LIKE_FIELD_TYPES = new Set(['Text']);

export const MANY_RELATION_FIELD_TYPES = new Set(['ManyToManyField', 'BackwardFKRelation']);

export const SINGLE_RELATION_FIELD_TYPES = new Set(['ForeignKeyField', 'OneToOneField']);

declare global {
  interface FilterCondition {
    field: string;
    symbol: string;
    value: any;
  }

  type FilterGroup = [] | ['and' | 'or', ...(FilterCondition | FilterGroup)[]];

  type FilterElement = [] | FilterCondition | FilterGroup;

  interface Paginator {
    curr_page: number;
    page_size: number;
    order_by: any[];
    filters: any[];
  }

  interface FatchManageParams {
    action: string;
    field_name: string;
    label: boolean;
    id?: number | string;
    paginator: Paginator;
    m2m_ids: Recordable;
  }
}
