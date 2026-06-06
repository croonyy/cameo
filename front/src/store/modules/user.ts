import { defineStore } from 'pinia';
import { store } from '@/store';
import { ACCESS_TOKEN, REFRESH_TOKEN, CURRENT_USER, IS_SCREENLOCKED } from '@/store/mutation-types';
// import { ResultEnum } from '@/enums/httpEnum';

import {
  getUserInfo as getUserInfoApi,
  login as loginApi,
  refresh as refreshApi,
} from '@/api/system/user';
import { storage } from '@/utils/Storage';
// import { PageEnum } from '@/enums/pageEnum';

export type UserInfoType = {
  // TODO: add your own data
  username: string;
  email: string;
  [key: string]: any; // 其他字段可选，类型为 any 或更具体的类型
};

export interface IUserState {
  token: string;
  username: string;
  welcome: string;
  avatar: string;
  permissions: any[];
  info: UserInfoType;
}

export const useUserStore = defineStore({
  id: 'app-user',
  state: (): IUserState => ({
    token: storage.get(ACCESS_TOKEN, ''),
    username: '',
    welcome: '',
    avatar: '',
    permissions: [],
    info: storage.get(CURRENT_USER, {}),
    // info: getInfo(),
  }),
  getters: {
    getToken(): string {
      return this.token;
    },
    getAvatar(): string {
      return this.avatar;
    },
    getNickname(): string {
      return this.username;
    },
    getPermissions(): [any][] {
      return this.permissions;
    },
    getUserInfo(): UserInfoType {
      return this.info;
    },
  },
  actions: {
    setToken(token: string) {
      this.token = token;
    },
    setAvatar(avatar: string) {
      this.avatar = avatar;
    },
    setPermissions(permissions) {
      this.permissions = permissions;
    },
    setUserInfo(info: any) {
      this.info = info;
    },
    async setAuthStorage(data: any) {
      const exp: Date = new Date(data.exp * 1000 - 2000); // 提前2秒过期
      const refresh_exp: Date = new Date(data.refresh_exp * 1000 - 2000); // 提前2秒过期
      const now: Date = new Date();
      const exp_gap = (exp.getTime() - now.getTime()) / 1000;
      const refresh_exp_gap = (refresh_exp.getTime() - now.getTime()) / 1000;
      // console.log(exp/3600)
      storage.set(ACCESS_TOKEN, data.access_token, exp_gap);
      storage.set(REFRESH_TOKEN, data.refresh_token, refresh_exp_gap);
      this.setToken(data.access_token);
      // 这里有问题，因为getUserInfoApi依赖refreshToken刷新。
      // 而refreshToken依赖setAuth，setAuth又调用getUserInfoApi所以会陷入死循环
      // const info = await getUserInfoApi();
      // storage.set(CURRENT_USER, info.data, exp_gap);
      // this.setUserInfo(info.data);
    },

    // 登录
    async login(params: any) {
      const response = await loginApi(params);
      if (response.code >= 2000 && response.code < 3000) {
        await this.setAuthStorage(response.data);
        const info = await getUserInfoApi();
        storage.set(CURRENT_USER, info.data, 60 * 60 * 24 * 365 * 100);
        this.setUserInfo(info.data);
      }
      return response;
    },

    // 刷新token
    async refreshToken() {
      console.log('@@@refresh_token');
      const refresh_token = storage.get(REFRESH_TOKEN);
      if (!refresh_token) {
        console.log('@@@refresh_token fail. refresh_token is invalid in storage.');
        // throw new Error('登录的刷新凭证已失效，请重新登录!');
        return false;
      } else {
        const response = await refreshApi({ refresh_token });
        if (response.code >= 2000 && response.code < 3000) {
          console.log('@@@refresh_token success.');
          await this.setAuthStorage(response.data);
          return true;
        } else {
          console.log('@@@refresh_token fail. response.code:', response.code);
          this.logout();
          // throw new Error('登录凭证刷新失败，请重新登录!');
          return false;
        }
      }
    },
    // 获取用户信息
    async getInfo() {
      if (this.info?.id != null) return this.info;
      const ret = await getUserInfoApi();
      console.log(ret);
      this.setUserInfo(ret.data);
      return ret.data;
    },

    // 登出
    async logout() {
      this.setPermissions([]);
      this.setUserInfo(undefined);
      storage.remove(ACCESS_TOKEN);
      storage.remove(REFRESH_TOKEN);
      storage.remove(CURRENT_USER);
      storage.remove(IS_SCREENLOCKED);
    },
  },
});

// Need to be used outside the setup
export function useUser() {
  return useUserStore(store);
}
