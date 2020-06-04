import AxiosClient from './axios-client'
import { LOAD_REPOS, LOAD_REPO_LIST, LOAD_LAST_WEEK_REPOS } from './action-types'
import { UPDATE_REPOS, UPDATE_REPO_LIST, UPDATE_LAST_WEEK_REPOS } from './mutation-types'

export default {
    // no-unused-vars
    [LOAD_REPOS]: ({commit}) => {
        return new Promise((resolve, reject) => {
            AxiosClient.get('/timeseries/latest.json').then((response) => {
                commit(UPDATE_REPOS, response.data)
                resolve(response.data)
            }).catch((error) => {
                reject(error)
            })
        })
    },
    [LOAD_REPO_LIST]: ({commit}) => {
        return new Promise((resolve, reject) => {
            AxiosClient.get('/release/repos.json').then((response) => {
                commit(UPDATE_REPO_LIST, response.data)
                resolve(response.data)
            }).catch((error) => {
                reject(error)
            })
        })
    },
    [LOAD_LAST_WEEK_REPOS]: ({commit}) => {
        return new Promise((resolve, reject) => {
            AxiosClient.get('/timeseries/last-week-entries.json').then((response) => {
                commit(UPDATE_LAST_WEEK_REPOS, response.data)
                resolve(response.data)
            }).catch((error) => {
                reject(error)
            })
        })
    }
}