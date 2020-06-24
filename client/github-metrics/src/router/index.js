import Vue from 'vue';
import VueRouter from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import RepoList from '../views/RepoList.vue';
import Builds from '../views/Builds.vue';
import Repo from '../views/Repo';
import Downloads from '../views/Downloads.vue';
import MetricsCollected from '../views/MetricsCollected.vue';

Vue.use(VueRouter);

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/repo-list',
    name: 'Repo List',
    component: RepoList
  },
  {
    path: '/repo-list/:owner/:pkgName',
    name: 'Repo',
    component: Repo
  },
  {
    path: '/builds',
    name: 'Builds',
    component: Builds
  },
  {
    path: '/downloads',
    name: 'Downloads',
    component: Downloads
  },
  {
    path: '/metrics-collected',
    name: 'Metrics Collected',
    component: MetricsCollected
  }
];

const router = new VueRouter({
  // mode: 'history',
  mode: 'hash',
  base: process.env.BASE_URL,
  routes,
});

export default router;
