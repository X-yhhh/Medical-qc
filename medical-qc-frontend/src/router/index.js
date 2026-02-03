// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // 登录页（无需认证）
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { public: true }
  },

  // 后台布局（需认证）
  {
    path: '/',
    component: () => import('@/views/layout/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      {
        path: '/dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { requiresAuth: true }
      },
      // 四大质控分类
      {
        path: '/head',
        component: () => import('@/views/quality/Head.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/chest-non-contrast',
        component: () => import('@/views/quality/ChestNonContrast.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/chest-contrast',
        component: () => import('@/views/quality/ChestContrast.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/coronary-cta',
        component: () => import('@/views/quality/CoronaryCTA.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/hemorrhage',
        component: () => import('@/views/quality/Hemorrhage.vue'),
        meta: { requiresAuth: true }
      },
      // 异常汇总
      {
        path: '/issues',
        component: () => import('@/views/summary/index.vue'),
        meta: { requiresAuth: true }
      }
    ]
  },

  // 404 重定向
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：检查登录状态
router.beforeEach((to, from, next) => {
  const token = sessionStorage.getItem('access_token')

  // 判断是否需要认证：优先看 meta.requiresAuth，其次看是否为公开页面
  const requiresAuth = to.meta.requiresAuth !== false && !to.meta.public

  if (requiresAuth && !token) {
    // 需要认证但未登录 → 跳登录
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    // 已登录用户访问登录/注册页 → 跳首页
    next('/')
  } else {
    next()
  }
})

export default router
