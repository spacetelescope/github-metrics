import Vue from 'vue';
import Vuex from 'vuex';

import mutations from './mutations';
import actions from './actions';

Vue.use(Vuex);

export default new Vuex.Store({
    state: {
        repos: [],
        repo_list: {},
        filteredRows: [],
        filteredRowsQuery: '',
        lastWeekRepos: [],
        filteredLastWeekRepos: [],
        filteredLastWeekReposMap: {},
        stats: {},
        lastWeekStats: {},
        repoData: {},
    },
    mutations,
    actions
})