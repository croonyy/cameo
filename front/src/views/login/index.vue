<template>
  <div class="view-account">
    <div class="view-account-header"></div>
    <div class="view-account-container">
      <div class="view-account-top">
        <div class="view-account-top-logo">
          <img :src="websiteConfig.loginImage" alt="" />
          <span class="view-account-top-logo-title">{{ websiteConfig.title }}</span>
        </div>
        <div class="view-account-top-desc">{{ websiteConfig.loginDesc }}</div>
      </div>
      <div class="view-account-form">
        <n-form
          ref="formRef"
          label-placement="left"
          size="large"
          :model="formInline"
          :rules="rules"
          @keydown.enter="handleSubmit"
        >
          <!-- @submit.prevent="handleSubmit" -->
          <n-form-item path="username">
            <n-input v-model:value="formInline.username" :placeholder="t('auth.usernamePlaceholder')">
              <template #prefix>
                <n-icon size="18" color="#83f7ff">
                  <PersonOutline />
                </n-icon>
              </template>
            </n-input>
          </n-form-item>
          <n-form-item path="password">
            <n-input
              v-model:value="formInline.password"
              type="password"
              showPasswordOn="click"
              :placeholder="t('auth.passwordPlaceholder')"
            >
              <template #prefix>
                <n-icon size="18" color="#83f7ff">
                  <LockClosedOutline />
                </n-icon>
              </template>
            </n-input>
          </n-form-item>
          <n-form-item class="default-color">
            <div class="flex justify-between">
              <div class="flex-initial">
                <n-checkbox v-model:checked="autoLogin">{{ t('auth.autoLogin') }}</n-checkbox>
              </div>
              <!-- <div class="flex-initial order-last">
                <a href="javascript:">忘记密码</a>
              </div> -->
            </div>
          </n-form-item>
          <n-form-item>
            <n-button type="primary" @click="handleSubmit" size="large" :loading="loading" block>
              {{ t('auth.login') }}
            </n-button>
          </n-form-item>
        </n-form>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
  import { reactive, ref } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { useUserStore } from '@/store/modules/user';
  import { useMessage } from 'naive-ui';
  // import { ResultEnum } from '@/enums/httpEnum';
  import { PersonOutline, LockClosedOutline } from '@vicons/ionicons5';
  import { PageEnum } from '@/enums/pageEnum';
  import { websiteConfig } from '@/config/website.config';
  import { t } from '@/i18n';

  interface FormState {
    username: string;
    password: string;
  }

  const formRef = ref();
  const message = useMessage();
  const loading = ref(false);
  const autoLogin = ref(true);
  const LOGIN_NAME = PageEnum.BASE_LOGIN_NAME;

  const formInline = reactive({
    username: 'admin',
    password: 'admin',
    isCaptcha: true,
  });

  const rules = {
    username: { required: true, message: t('auth.usernameRequired'), trigger: 'blur' },
    password: { required: true, message: t('auth.passwordRequired'), trigger: 'blur' },
  };

  const userStore = useUserStore();
  const router = useRouter();
  const route = useRoute();

  const handleSubmit = (e) => {
    e.preventDefault();
    formRef.value.validate(async (errors) => {
      if (!errors) {
        const { username, password } = formInline;
        // message.loading('登录中...');
        loading.value = true;

        const params: FormState = {
          username,
          password,
        };

        try {
          const { code, msg } = await userStore.login(params);
          message.destroyAll();
          if (code == 2000) {
            const toPath = decodeURIComponent((route.query?.redirect || '/') as string);
            message.success(t('auth.loginSuccess'));
            if (route.name === LOGIN_NAME) {
              router.replace('/');
            } else router.replace(toPath);
          } else {
            message.info(msg || t('auth.loginFailed'));
          }
        } catch (error: any) {
          loading.value = false;
          console.log('@@@login error', error);
          message.error(`${t('auth.loginFailed')}: ${error.message}`);
        } finally {
          loading.value = false;
        }
      } else {
        message.error('请填写完整信息。');
      }
    });
  };
</script>
<style lang="less" scoped>
  .view-account {
    display: flex;
    flex-direction: column;
    justify-content: center;
    height: 100vh;
    overflow: auto;
    background: radial-gradient(circle at 18% 20%, rgba(0, 245, 255, 0.14), transparent 28%),
      radial-gradient(circle at 82% 28%, rgba(255, 0, 170, 0.12), transparent 30%),
      linear-gradient(135deg, #07111f 0%, #0a0f1d 45%, #0c1730 100%);
    background-attachment: fixed;
    color: #f7fbff;

    &-container {
      position: relative;
      z-index: 1;
      width: 384px;
      padding: 34px 32px 28px;
      max-width: calc(100vw - 32px);
      min-width: 320px;
      margin-left: auto;
      margin-right: clamp(32px, 12vw, 180px);
      border: 1px solid rgba(0, 245, 255, 0.2);
      border-radius: var(--radius-sm);
      background: rgba(7, 17, 31, 0.2);
      box-shadow: 0 28px 80px rgba(0, 0, 0, 0.36), 0 0 48px rgba(0, 245, 255, 0.12);
      backdrop-filter: blur(16px);
    }

    &-top {
      padding: 0 0 28px;
      text-align: center;

      &-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        width: 100%;

        img {
          width: 46px;
          height: 46px;
          object-fit: contain;
          filter: drop-shadow(0 0 12px rgba(0, 245, 255, 0.42));
        }

        &-title {
          color: #ffffff;
          font-size: 30px;
          font-weight: 700;
          line-height: 1;
          text-shadow: 0 0 18px rgba(0, 245, 255, 0.28);
        }
      }

      &-desc {
        font-size: 14px;
        color: rgba(206, 232, 255, 0.72);
      }
    }

    &-other {
      width: 100%;
    }

    &-form {
      :deep(.n-form-item-feedback-wrapper) {
        min-height: 20px;
      }

      :deep(.n-form-item-feedback__line) {
        color: #ff6bcf;
      }
    }

    .default-color {
      color: rgba(230, 242, 255, 0.86);

      :deep(.n-checkbox__label) {
        color: rgba(230, 242, 255, 0.86);
      }
    }

    &::before {
      position: fixed;
      inset: 0;
      z-index: 0;
      pointer-events: none;
      content: '';
      background-image: url('../../assets/images/login.svg');
      background-repeat: no-repeat;
      background-position: 50% 50%;
      background-size: cover;
      opacity: 1;
    }

    &::after {
      position: fixed;
      inset: 0;
      z-index: 0;
      pointer-events: none;
      content: '';
      background: linear-gradient(
          90deg,
          rgba(7, 17, 31, 0) 0%,
          rgba(7, 17, 31, 0) 36%,
          rgba(7, 17, 31, 0) 100%
        ),
        linear-gradient(180deg, rgba(7, 17, 31, 0.04), rgba(7, 17, 31, 0.22));
    }
  }

  .n-input {
    --n-color: rgba(8, 20, 38, 0.72) !important;
    --n-color-focus: rgba(8, 20, 38, 0.9) !important;
    --n-color-disabled: rgba(8, 20, 38, 0.48) !important;
    --n-border: 1px solid rgba(0, 245, 255, 0.26) !important;
    --n-border-hover: 1px solid rgba(0, 245, 255, 0.62) !important;
    --n-border-focus: 1px solid #00f5ff !important;
    --n-box-shadow-focus: 0 0 0 2px rgba(0, 245, 255, 0.14) !important;
    --n-caret-color: #00f5ff !important;
    --n-text-color: #f7fbff !important;
    --n-placeholder-color: rgba(206, 232, 255, 0.48) !important;
    --n-placeholder-color-disabled: rgba(206, 232, 255, 0.28) !important;
    --n-icon-color: #83f7ff !important;
    --n-icon-color-disabled: rgba(131, 247, 255, 0.45) !important;
    border: 1px solid rgba(0, 245, 255, 0.26);
    border-radius: var(--radius-sm) !important;
    color: #f7fbff !important;
    background-color: rgba(8, 20, 38, 0.72) !important;
  }

  :deep(.n-input .n-input__input-el),
  :deep(.n-input .n-input__placeholder),
  :deep(.n-input .n-input__textarea-el) {
    color: #f7fbff;
  }

  :deep(.n-input .n-input__placeholder) {
    color: rgba(206, 232, 255, 0.48);
  }

  :deep(.n-input .n-input__input-el:-webkit-autofill),
  :deep(.n-input .n-input__input-el:-webkit-autofill:hover),
  :deep(.n-input .n-input__input-el:-webkit-autofill:focus),
  :deep(.n-input .n-input__input-el:-webkit-autofill:active) {
    box-shadow: 0 0 0 1000px rgba(8, 20, 38, 0.9) inset !important;
    -webkit-text-fill-color: #f7fbff !important;
    caret-color: #00f5ff !important;
    transition: background-color 9999s ease-out 0s;
  }

  :deep(.n-input:hover),
  :deep(.n-input.n-input--focus) {
    border-color: #00f5ff;
    box-shadow: 0 0 0 2px rgba(0, 245, 255, 0.12);
  }

  :deep(.n-button--primary-type) {
    --n-color: transparent !important;
    --n-color-hover: transparent !important;
    --n-color-pressed: transparent !important;
    --n-color-focus: transparent !important;
    --n-color-disabled: rgba(83, 117, 140, 0.48) !important;
    --n-border: 0 !important;
    --n-border-hover: 0 !important;
    --n-border-pressed: 0 !important;
    --n-border-focus: 0 !important;
    --n-border-disabled: 0 !important;
    --n-text-color: #06101d !important;
    --n-text-color-hover: #06101d !important;
    --n-text-color-pressed: #06101d !important;
    --n-text-color-focus: #06101d !important;
    --n-ripple-color: rgba(0, 245, 255, 0.28) !important;
    font-weight: 600;
    background: linear-gradient(90deg, #00c8ff 0%, #00f5ff 52%, #ff2ac6 100%) !important;
    box-shadow: 0 12px 28px rgba(0, 245, 255, 0.22);
  }

  :deep(.n-button--primary-type:hover),
  :deep(.n-button--primary-type:focus) {
    filter: brightness(1.08);
    box-shadow: 0 14px 30px rgba(0, 245, 255, 0.26), 0 0 18px rgba(255, 42, 198, 0.18);
  }

  :deep(.n-button--primary-type:active) {
    filter: brightness(0.94);
  }

  :deep(.n-checkbox) {
    --n-color: rgba(8, 20, 38, 0.72) !important;
    --n-color-checked: #00f5ff !important;
    --n-color-disabled: rgba(8, 20, 38, 0.42) !important;
    --n-color-disabled-checked: rgba(0, 245, 255, 0.28) !important;
    --n-border: 1px solid rgba(206, 232, 255, 0.3) !important;
    --n-border-checked: 1px solid #00f5ff !important;
    --n-border-focus: 1px solid #00f5ff !important;
    --n-border-disabled: 1px solid rgba(206, 232, 255, 0.18) !important;
    --n-border-disabled-checked: 1px solid rgba(0, 245, 255, 0.28) !important;
    --n-box-shadow-focus: 0 0 0 2px rgba(0, 245, 255, 0.14) !important;
    --n-check-mark-color: #06101d !important;
    --n-text-color: rgba(230, 242, 255, 0.86) !important;
  }

  @media (max-width: 767px) {
    .view-account {
      justify-content: flex-start;

      &-container {
        margin: 28px auto;
      }

      &::before {
        background-position: 50% 50%;
        background-size: cover;
        opacity: 1;
      }

      &::after {
        background: rgba(7, 17, 31, 0.34);
      }
    }
  }
</style>
