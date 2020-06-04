import {
    UPDATE_REPOS,
    UPDATE_REPO_LIST,
    UPDATE_FILTERED_ROWS,
    UPDATE_FILTERED_ROWS_QUERY,
    UPDATE_LAST_WEEK_REPOS,
    UPDATE_FILTERED_LAST_WEEK_REPOS
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
    }
}