import logoImage from '@/assets/images/logo.svg';

export const websiteConfig = Object.freeze({
  // title: '接口平台',
  title: import.meta.env.VITE_GLOB_APP_TITLE || 'Default Title',
  logo: logoImage,
  loginImage: logoImage,
  loginDesc: '',
});
