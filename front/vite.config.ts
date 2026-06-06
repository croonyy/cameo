import type { UserConfig, ConfigEnv } from 'vite';
import { loadEnv } from 'vite';
import { resolve } from 'path';
import { wrapperEnv } from './build/utils';
import { createVitePlugins } from './build/vite/plugin';
import { OUTPUT_DIR } from './build/constant';
import { createProxy } from './build/vite/proxy';
import pkg from './package.json';
import { format } from 'date-fns';
const { dependencies, devDependencies, name, version } = pkg;

const __APP_INFO__ = {
  pkg: { dependencies, devDependencies, name, version },
  lastBuildTime: format(new Date(), 'yyyy-MM-dd HH:mm:ss'),
};

function pathResolve(dir: string) {
  return resolve(process.cwd(), '.', dir);
}

export default ({ command, mode }: ConfigEnv): UserConfig => {
  const root = process.cwd();
  const env = loadEnv(mode, root);
  const viteEnv = wrapperEnv(env);
  const { VITE_PUBLIC_PATH, VITE_PORT, VITE_PROXY } = viteEnv;
  const isBuild = command === 'build';
  return {
    base: VITE_PUBLIC_PATH,
    esbuild: {},
    resolve: {
      alias: [
        {
          find: /\/#\//,
          replacement: pathResolve('types') + '/',
        },
        {
          find: '@',
          replacement: pathResolve('src') + '/',
        },
      ],
      dedupe: ['vue'],
    },
    plugins: createVitePlugins(viteEnv, isBuild),
    define: {
      __APP_ENV__: JSON.stringify(env.APP_ENV),
      __APP_INFO__: JSON.stringify(__APP_INFO__),
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false,
    },
    server: {
      host: true,
      port: VITE_PORT,
      proxy: createProxy(VITE_PROXY),
    },
    optimizeDeps: {
      // 预构建常用依赖，提升开发模式性能
      include: [
        'vue',
        'vue-router',
        'pinia',
        'naive-ui',
        '@vueuse/core',
        'lodash-es',
        'dayjs',
        'alova',
        'qs',
      ],
      exclude: ['vue-demi'],
    },
    build: {
      target: 'es2015',
      cssTarget: 'chrome80',
      outDir: OUTPUT_DIR,
      emptyOutDir: true,
      reportCompressedSize: false,
      chunkSizeWarningLimit: 2000,
      // 启用 CSS 代码分割
      cssCodeSplit: true,
      rollupOptions: {
        output: {
          // 代码分割配置
          // manualChunks: {
          //   // 将所有 node_modules 中的依赖打包到 vendor 文件中
          //   'vendor': [...Object.keys(dependencies), ...Object.keys(devDependencies)],
          //   // 也可以更精细地分割
          //   // 'react-vendor': ['react', 'react-dom'],
          //   // 'ui-vendor': ['antd', 'element-plus'],
          // },
          // Keep Rollup's default chunk graph. A previous manual split separated
          // circular Vue-related dependencies and caused TDZ runtime errors.
          chunkFileNames: 'js/[name]_[hash].js',
          entryFileNames: 'js/[name]_[hash].js',
          // assetFileNames: 'assets/[ext]/[name].[hash].[ext]'
          // 静态资源（CSS/图片）通过 assetFileNames 分类
          assetFileNames(assetInfo) {
            // 获取第一个名称（如果存在），否则回退到默认名称
            const primaryName = assetInfo.names?.[0] ?? '[name]';
            if (primaryName.endsWith('.css')) {
              return 'css/[name]-[hash][extname]';
            }
            if (/\.(png|jpe?g|gif|svg|webp)$/.test(primaryName)) {
              return 'img/[name]-[hash][extname]';
            }
            return 'assets/source/[name]_[hash].[ext]';
          },
        },
      },
    },
  };
};
