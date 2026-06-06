<template>
  <div
    :class="{ onLockLogin: showLogin }"
    class="lockscreen"
    @keyup="onLockLogin(true)"
    @mousedown.stop
    @contextmenu.prevent
  >
    <template v-if="!showLogin">
      <div class="lock-box">
        <div class="lock">
          <span class="lock-icon" :title="t('lock.unlockScreen')" @click="onLockLogin(true)">
            <n-icon>
              <lock-outlined />
            </n-icon>
          </span>
        </div>
      </div>
      <!-- 充电-->
      <!-- <recharge
        :battery="battery"
        :battery-status="batteryStatus"
        :calc-discharging-time="calcDischargingTime"
        :calc-charging-time="calcChargingTime"
      /> -->

      <div class="local-time">
        <div class="time">{{ hour }}:{{ minute }}</div>
        <div class="date">{{ t('lock.dateText', { month, day, week }) }}</div>
      </div>
      <div class="computer-status">
        <span :class="{ offline: !online }" class="network">
          <wifi-outlined class="network" />
        </span>
        <api-outlined />
      </div>
    </template>

    <!--登录-->
    <template v-if="showLogin">
      <div class="login-box">
        <n-avatar :size="128">
          <n-icon>
            <user-outlined />
          </n-icon>
        </n-avatar>
        <div class="username">{{ loginParams.username }}</div>
        <n-input
          class="lock-password-input"
          type="password"
          autofocus
          v-model:value="loginParams.password"
          @keyup.enter="onLogin"
          :placeholder="t('lock.passwordPlaceholder')"
        >
          <template #suffix>
            <n-icon @click="onLogin" style="cursor: pointer">
              <LoadingOutlined v-if="loginLoading" />
              <arrow-right-outlined v-else />
            </n-icon>
          </template>
        </n-input>

        <div class="flex w-full" v-if="isLoginError">
          <span class="text-red-500">{{ errorMsg }}</span>
        </div>

        <div class="flex justify-around w-full mt-1">
          <!-- <n-button type="info" @click="showLogin">返回</n-button>
          <n-button type="info" @click="goLogin">重新登录</n-button>
          <n-button type="info" @click="onLogin">进入系统</n-button> -->
          <div class="lock-a"><a @click="showLogin = false">{{ t('lock.back') }}</a></div>
          <div class="lock-a"><a @click="goLogin">{{ t('lock.relogin') }}</a></div>
          <div class="lock-a"><a @click="onLogin">{{ t('lock.enterSystem') }}</a></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script lang="ts">
  import { defineComponent, reactive, toRefs } from 'vue';
  import { ResultEnum } from '@/enums/httpEnum';
  import recharge from './Recharge.vue';
  import {
    LockOutlined,
    LoadingOutlined,
    UserOutlined,
    ApiOutlined,
    ArrowRightOutlined,
    WifiOutlined,
  } from '@vicons/antd';

  import { useRouter, useRoute } from 'vue-router';
  import { useOnline } from '@/hooks/useOnline';
  import { useTime } from '@/hooks/useTime';
  import { useBattery } from '@/hooks/useBattery';
  import { useScreenLockStore } from '@/store/modules/screenLock';
  import { UserInfoType, useUserStore } from '@/store/modules/user';
  import { string } from 'vue-types';
  import { t } from '@/i18n';

  export default defineComponent({
    name: 'ScreenLock',
    components: {
      LockOutlined,
      LoadingOutlined,
      UserOutlined,
      ArrowRightOutlined,
      ApiOutlined,
      WifiOutlined,
      // recharge,
    },
    setup() {
      const useScreenLock = useScreenLockStore();
      const userStore = useUserStore();

      // 获取时间
      const { month, day, hour, minute, second, week } = useTime();
      const { online } = useOnline();

      const router = useRouter();
      const route = useRoute();

      const { battery, batteryStatus, calcDischargingTime, calcChargingTime } = useBattery();
      const userInfo: UserInfoType = userStore.getUserInfo || {};
      const username = userInfo['username'] || '';
      const state = reactive({
        showLogin: false,
        loginLoading: false, // 正在登录
        isLoginError: false, //密码错误
        errorMsg: t('lock.passwordError'),
        loginParams: {
          username: username || '',
          password: '',
        },
      });

      // 解锁登录
      const onLockLogin = (value: boolean) => (state.showLogin = value);

      // 登录
      const onLogin = async () => {
        if (!state.loginParams.password.trim()) {
          return;
        }
        const params = {
          isLock: true,
          ...state.loginParams,
        };
        state.loginLoading = true;
        try {
          const { code, msg } = await userStore.login(params);
          if (code >= 2000 && code < 3000) {
            onLockLogin(false);
            useScreenLock.setLock(false);
          } else {
            state.errorMsg = msg as string;
            state.isLoginError = true;
          }
        } catch (error) {
          state.errorMsg = error as string;
          state.isLoginError = true;
        }

        state.loginLoading = false;
      };

      //重新登录
      const goLogin = () => {
        onLockLogin(false);
        useScreenLock.setLock(false);
        router.replace({
          path: '/login',
          query: {
            redirect: route.fullPath,
          },
        });
      };

      return {
        ...toRefs(state),
        online,
        month,
        day,
        hour,
        minute,
        second,
        week,
        battery,
        batteryStatus,
        calcDischargingTime,
        calcChargingTime,
        onLockLogin,
        onLogin,
        goLogin,
        t,
      };
    },
  });
</script>

<style lang="less" scoped>
  .lockscreen {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    right: 0;
    display: flex;
    background: #000;
    color: white;
    overflow: hidden;
    z-index: 9999;

    &.onLockLogin {
      background-color: rgba(25, 28, 34, 0.88);
      backdrop-filter: blur(7px);
    }

    .login-box {
      position: absolute;
      top: 45%;
      left: 50%;
      transform: translate(-50%, -50%);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;

      > * {
        margin-bottom: 14px;
      }

      .username {
        font-size: 30px;
      }

      :deep(.lock-password-input) {
        --n-color: #080c12 !important;
        --n-color-focus: #080c12 !important;
        --n-text-color: #fff !important;
        --n-caret-color: #fff !important;

        background-color: #080c12 !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        color: #fff !important;
      }

      :deep(.lock-password-input.n-input--focus) {
        background-color: #080c12 !important;
      }

      :deep(.lock-password-input .n-input__input),
      :deep(.lock-password-input .n-input__input-el),
      :deep(.lock-password-input .n-input__suffix) {
        background-color: #080c12 !important;
        color: #fff !important;
      }

      :deep(.lock-password-input .n-input__placeholder) {
        color: rgba(255, 255, 255, 0.52) !important;
      }

      :deep(.lock-password-input .n-input__input-el:-webkit-autofill),
      :deep(.lock-password-input .n-input__input-el:-webkit-autofill:hover),
      :deep(.lock-password-input .n-input__input-el:-webkit-autofill:focus) {
        -webkit-text-fill-color: #fff !important;
        caret-color: #fff !important;
        box-shadow: 0 0 0 1000px #080c12 inset !important;
        transition: background-color 9999s ease-out 0s;
      }
    }

    .lock-box {
      position: absolute;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      font-size: 34px;
      z-index: 100;

      .tips {
        color: white;
        cursor: text;
      }

      .lock {
        display: flex;
        justify-content: center;

        .lock-icon {
          cursor: pointer;

          .anticon-unlock {
            display: none;
          }

          &:hover .anticon-unlock {
            display: initial;
          }

          &:hover .anticon-lock {
            display: none;
          }
        }
      }
    }

    .local-time {
      position: absolute;
      bottom: 60px;
      left: 60px;
      font-family: helvetica;

      .time {
        font-size: 70px;
      }

      .date {
        font-size: 40px;
      }
    }

    .computer-status {
      position: absolute;
      bottom: 60px;
      right: 60px;
      font-size: 24px;

      > * {
        margin-left: 14px;
      }

      .network {
        position: relative;

        &.offline::before {
          content: '';
          position: absolute;
          left: 50%;
          top: 50%;
          width: 2px;
          height: 28px;
          transform: translate(-50%, -50%) rotate(45deg);
          background-color: red;
          z-index: 10;
        }
      }
    }
  }
  .lock-a:hover {
    cursor: pointer !important;
    color: aqua;
  }
</style>
