import { UPDATE_REPOS } from './mutation-types'

export default {
    [UPDATE_REPOS](state, repos) {
        state['repos'] = repos
    }
}