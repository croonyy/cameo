<template>
  <h2>主页</h2>
  <!-- <n-button @click="get_info">Info</n-button> -->
  <n-button @click="test">test</n-button>
  <title></title>
  <h3>mode: {{ mode }}</h3>
</template>
<script lang="ts" setup>
  import { getUserInfo } from '@/api/system/user';
  // import { createAlova } from 'alova';
  // import adapterFetch from 'alova/fetch';

  // const alovaInstance = createAlova({
  //   requestAdapter: adapterFetch(),
  //   responded: (response) => response.json(),
  // });

  // async function get_info() {
  //   try {
  //     // let info = await getUserInfo(); // 一个网络请求
  //     // let info = await Test(); // 一个网络请求

  //     let info = await alovaInstance.Get('https://alovajs.dev/user/profile');

  //     console.log('getUserInfo ret', info);
  //   } catch (error) {
  //     console.log('getUserInfo error', error);
  //   }
  // }
  async function test() {
    let info = await getUserInfo(); // 一个网络请求
    console.log('test', info);
  }

  const mode = import.meta.env.MODE;
</script>
<style lang="less" scoped></style>
