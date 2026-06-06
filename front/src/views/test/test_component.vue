<template>
  <n-space vertical>
    <n-form :model="formData">
      <n-form-item>
        <n-input v-model:value="formData['aa']" placeholder="璇疯緭鍏ュ悕绉?" />
      </n-form-item>
      <n-form-item>
        <!-- 鏄剧ず UdTransferList缁勪欢-->
        <M2m
          v-model:value="formData['bb']"
          :onLeftSearch="onLeftSearch"
          :onRightSearch="onRightSearch"
        />
      </n-form-item>
      <n-button type="primary" @click="handleSubmit()" size="small">娴嬭瘯</n-button>
    </n-form>
  </n-space>
</template>

<script lang="ts" setup>
  import { reactive, ref, toRaw } from 'vue';
  // import UdTransferList from '@/components/TransferList/UdTransferList.vue';
  import M2m from '@/components/UdFormItem/M2m.vue';
  import { RelManage } from '@/api/crud/models';

  const formData = ref({});
  const field = {
    field_name: 'permissions',
    app_name: 'udadmin',
    model_name: 'Role',
  };

  function getFetchManageParams(): FatchManageParams {
    return {
      action: 'list',
      field_name: '',
      label: true,
      id: 1,
      paginator: {
        curr_page: 1,
        page_size: 10,
        order_by: [],
        filters: [],
      },
      m2m_ids: [],
    };
  }
  const onLeftSearch = async (search: string) => {
    //TODO 鎼滅储瀛楁鍚庣闇€瑕佹敮鎸?
    const search_fields = ['id'];
    const querys: FilterGroup = [
      'or',
      ...search_fields.map((item) => ({
        field: item,
        symbol: 'icontains',
        value: search,
      })),
    ];
    const params = getFetchManageParams();
    params.field_name = field.field_name;
    params.action = 'query';
    params.paginator.filters = querys;
    const { data } = await RelManage(field.app_name, field.model_name, params);
    return data.map((item: any) => ({ label: item.label, value: item.value.id }));
  };
  const onRightSearch = async (search: string) => {
    //TODO 鎼滅储瀛楁鍚庣闇€瑕佹敮鎸?
    const search_fields = ['id'];
    const querys: FilterGroup = [
      'or',
      ...search_fields.map((item) => ({
        field: item,
        symbol: 'icontains',
        value: search,
      })),
    ];
    const params = getFetchManageParams();
    params.field_name = field.field_name;
    params.action = 'list';
    params.paginator.filters = querys;
    const { data } = await RelManage(field.app_name, field.model_name, params);
    return data.map((item: any) => ({ label: item.label, value: item.value.id }));
  };

  function handleSubmit() {
    console.log(formData.value);
  }
</script>
