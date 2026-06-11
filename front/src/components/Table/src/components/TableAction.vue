<template>
  <div class="tableAction">
    <div class="table-action-list">
      <template v-for="(action, index) in getActions" :key="`${index}-${action.label}`">
        <n-button v-bind="action" class="table-action-button">
          {{ action.label }}
          <template #icon v-if="action.hasOwnProperty('icon')">
            <n-icon :component="action.icon" />
          </template>
        </n-button>
      </template>
      <n-dropdown
        v-if="dropDownActions && getDropdownList.length"
        trigger="hover"
        :options="getDropdownList"
        @select="select"
      >
        <slot name="more"></slot>
        <n-button v-bind="getMoreProps" class="mx-1" v-if="!$slots.more" icon-placement="right">
          <div class="flex items-center">
            <span>更多</span>
            <n-icon size="14" class="ml-1">
              <DownOutlined />
            </n-icon>
          </div>
          <!--          <template #icon>-->
          <!--            -->
          <!--          </template>-->
        </n-button>
      </n-dropdown>
    </div>
  </div>
</template>

<script lang="ts">
  import { defineComponent, PropType, computed, toRaw } from 'vue';
  import { ActionItem } from '@/components/Table';
  import { usePermission } from '@/hooks/web/usePermission';
  import { isBoolean, isFunction } from '@/utils/is';
  import { DownOutlined } from '@vicons/antd';

  export default defineComponent({
    name: 'TableAction',
    components: { DownOutlined },
    props: {
      actions: {
        type: Array as PropType<ActionItem[]>,
        default: null,
        required: true,
      },
      dropDownActions: {
        type: Array as PropType<ActionItem[]>,
        default: null,
      },
      style: {
        type: String as PropType<String>,
        default: 'button',
      },
      select: {
        type: Function as PropType<Function>,
        default: () => {},
      },
    },
    setup(props) {
      const { hasPermission } = usePermission();

      const actionType =
        props.style === 'button' ? 'default' : props.style === 'text' ? 'primary' : 'default';
      const actionText =
        props.style === 'button' ? undefined : props.style === 'text' ? true : undefined;

      const getMoreProps = computed(() => {
        return {
          text: actionText,
          type: actionType,
          size: 'small',
        };
      });

      const getDropdownList = computed(() => {
        return (toRaw(props.dropDownActions) || [])
          .filter((action) => {
            return hasPermission(action.auth as string[]) && isIfShow(action);
          })
          .map((action) => {
            const { popConfirm } = action;
            return {
              size: 'small',
              secondary: props.style === 'button',
              round: props.style === 'button',
              text: actionText,
              type: actionType,
              ...action,
              ...popConfirm,
              onConfirm: popConfirm?.confirm,
              onCancel: popConfirm?.cancel,
            };
          });
      });

      function isIfShow(action: ActionItem): boolean {
        const ifShow = action.ifShow;

        let isIfShow = true;

        if (isBoolean(ifShow)) {
          isIfShow = ifShow;
        }
        if (isFunction(ifShow)) {
          isIfShow = ifShow(action);
        }
        return isIfShow;
      }

      const getActions = computed(() => {
        return (toRaw(props.actions) || [])
          .filter((action) => {
            return hasPermission(action.auth as string[]) && isIfShow(action);
          })
          .map((action) => {
            const { popConfirm } = action;
            //需要展示什么风格，自己修改一下参数
            return {
              size: 'small',
              text: actionText,
              type: actionType,
              ...action,
              ...(popConfirm || {}),
              onConfirm: popConfirm?.confirm,
              onCancel: popConfirm?.cancel,
              enable: !!popConfirm,
            };
          });
      });

      return {
        getActions,
        getDropdownList,
        getMoreProps,
      };
    },
  });
</script>

<style lang="less" scoped>
  .tableAction {
    display: inline-flex;
    justify-content: center;
    width: max-content;
    max-width: 100%;
    white-space: normal;

    .table-action-list {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      gap: 4px;
      width: max-content;
      max-width: 100%;
      min-width: 0;
      padding: 2px 0;
      box-sizing: border-box;
    }

    :deep(.table-action-button) {
      flex: 0 0 auto;
      min-width: 0;
      padding: 0 8px;
      font-weight: 600;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
      transition: transform 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease;

      &:hover {
        transform: translateY(-1px);
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.12), 0 4px 10px rgba(0, 0, 0, 0.12);
      }

      &:active {
        transform: translateY(0);
      }

      .n-button__icon {
        margin-right: 3px;
      }
    }
  }
  :global(.n-dropdown-menu .n-dropdown-option .n-dropdown-option-body::before) {
    top: 2px !important;
    bottom: 2px !important;
  }
</style>
