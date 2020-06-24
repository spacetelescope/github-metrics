import {
    UPDATE_REPOS,
    UPDATE_REPO_LIST,
    UPDATE_FILTERED_ROWS,
    UPDATE_FILTERED_ROWS_QUERY,
    UPDATE_LAST_WEEK_REPOS,
    UPDATE_FILTERED_LAST_WEEK_REPOS,
    UPDATE_REPO_STATS,
    UPDATE_REPO_LAST_WEEK_STATS,
    UPDATE_REPO_DATA,
} from './mutation-types'

export default {
    [UPDATE_REPOS](state, repos) {
        state['repos'] = repos
    },
    [UPDATE_REPO_LIST](state, repos) {
        state.repo_list = repos
    },
    [UPDATE_FILTERED_ROWS](state, filteredRows) {
        state.filteredRows = filteredRows
    },
    [UPDATE_FILTERED_ROWS_QUERY](state, query) {
        state.filteredRowsQuery = query
    },
    [UPDATE_LAST_WEEK_REPOS](state, lastWeekRepos) {
        state.lastWeekRepos = lastWeekRepos
    },
    [UPDATE_FILTERED_LAST_WEEK_REPOS](state, filteredLastWeekRepos) {
        state.filteredLastWeekRepos = filteredLastWeekRepos
        state.filteredLastWeekReposMap = {}
        let idx = 0;
        for (idx; idx < filteredLastWeekRepos.length; idx++) {
            let value = filteredLastWeekRepos[idx];
            state.filteredLastWeekReposMap[value.package_name] = value;
        }
    },
    [UPDATE_REPO_STATS](state, stats) {
        // eslint-disable-next-line
        if (!Object.prototype.hasOwnProperty.call(state['stats'], stats.owner)) {
          state['stats'][stats.owner] = {};
        }
        state['stats'][stats.owner][stats.name] = stats;
    },
    // eslint-disable-next-line
    [UPDATE_REPO_LAST_WEEK_STATS](state, {stats, owner, name}) {
        const lastWeekStats = { ...state.lastWeekStats } || {};
        lastWeekStats[owner] = lastWeekStats[owner] || {};
        lastWeekStats[owner][name] = stats;
        state.lastWeekStats = lastWeekStats;
    },
    [UPDATE_REPO_DATA](state, {data, owner, name}) {
        if (!Object.prototype.hasOwnProperty.call(state['repoData'], owner)) {
            state['repoData'][owner] = {};
        }
        state['repoData'][owner][name] = data;
    }
}