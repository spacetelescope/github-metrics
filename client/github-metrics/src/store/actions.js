import AxiosClient from './axios-client'
import { LOAD_REPOS } from './action-types'
import { UPDATE_REPOS } from './mutation-types'

export default {
    // no-unused-vars
    [LOAD_REPOS]: ({commit}) => {
        return new Promise((resolve, reject) => {
            AxiosClient.get('https://github-metrics-stsci-edu-prod.s3.amazonaws.com/timeseries/latest.json').then((response) => {
                commit(UPDATE_REPOS, response.data)
                resolve(response.data)
            }).catch((error) => {
                reject(error)
            })
        })
    }
}