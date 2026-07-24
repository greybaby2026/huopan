import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { title: '登录', public: true },
    },
    {
      path: '/',
      component: () => import('../layouts/MainLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue'),
          meta: { title: '数据控制台' },
        },
        {
          path: 'products',
          name: 'products',
          component: () => import('../views/ProductsView.vue'),
          meta: { title: '产品库' },
        },
        {
          path: 'customers',
          name: 'customers',
          component: () => import('../views/CustomersView.vue'),
          meta: { title: '客户管理' },
        },
        {
          path: 'catalogs',
          name: 'catalogs',
          component: () => import('../views/CatalogsView.vue'),
          meta: { title: '货盘管理' },
        },
        {
          path: 'spreadsheet',
          name: 'spreadsheet',
          component: () => import('../views/SpreadsheetView.vue'),
          meta: { title: '货盘排版' },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('../views/UsersView.vue'),
          meta: { title: '用户管理' },
        },
        {
          path: 'logs',
          name: 'logs',
          component: () => import('../views/LogsView.vue'),
          meta: { title: '操作日志' },
        },
        {
          path: 'dicts',
          name: 'dicts',
          component: () => import('../views/DictsView.vue'),
          meta: { title: '品类尺码' },
        },
      ],
    },
  ],
})

// 路由守卫: 未登录跳转登录页
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('huopan_token')
  if (!to.meta.public && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
