import AxiosClient from './axios-client'
import { LOAD_REPOS, LOAD_REPO_LIST, LOAD_LAST_WEEK_REPOS, LOAD_REPO_STATS, LOAD_REPO_LAST_WEEK_STATS, LOAD_REPO_DATA } from './action-types'
import { UPDATE_REPOS, UPDATE_REPO_LIST, UPDATE_LAST_WEEK_REPOS, UPDATE_REPO_STATS, UPDATE_REPO_LAST_WEEK_STATS, UPDATE_REPO_DATA } from './mutation-types'
import * as R from 'ramda';
import store from './index';

export default {
    // no-unused-vars
    [LOAD_REPOS]: ({commit}) => {
        return new Promise((resolve, reject) => {
            AxiosClient.get('/timeseries/latest.json').then((response) => {
                commit(UPDATE_REPOS, response.data)
                resolve(response.data)
            }).catch((error) => {
                reject(error)
            });
        });
    },
    [LOAD_REPO_LIST]: ({commit}) => {
        return new Promise((resolve, reject) => {
            AxiosClient.get('/release/repos.json').then((response) => {
                commit(UPDATE_REPO_LIST, response.data)
                resolve(response.data)
            }).catch((error) => {
                reject(error)
            });
        });
    },
    [LOAD_LAST_WEEK_REPOS]: ({commit}) => {
        return new Promise((resolve, reject) => {
            AxiosClient.get('/timeseries/last-week-entries.json').then((response) => {
                commit(UPDATE_LAST_WEEK_REPOS, response.data)
                resolve(response.data)
            }).catch((error) => {
                reject(error)
            });
        });
    },
    [LOAD_REPO_STATS]: ({commit}, {owner, name}) => {
        return new Promise((resolve, reject) => {
            AxiosClient.get(`/timeseries/last-week-stats/${owner}/${name}.json`).then((response) => {
                const data = response.data;
                data['owner'] = owner
                data['name'] = name
                data['found'] = true
                commit(UPDATE_REPO_STATS, owner, name, data);
                resolve(data);
            }).catch((error) => {
                const data = {};
                data['owner'] = owner;
                data['name'] = name;
                data['found'] = false;
                commit(UPDATE_REPO_STATS, owner, name, data);
                if (error.response.status !== 403) {
                    reject(error);
                }
            });
        });
    },
    [LOAD_REPO_LAST_WEEK_STATS]: ({commit}, {owner, name}) => {
        return new Promise((resolve, reject) => {
            AxiosClient.get(`/timeseries/last-week-stats/${owner}/${name}.json`).then((response) => {
                const stats = response.data;
                stats['owner'] = owner;
                stats['name'] = name;
                stats['found'] = true;
                commit(UPDATE_REPO_LAST_WEEK_STATS, {stats, owner, name});
                resolve(stats);
            }).catch((error) => {
                const stats = {};
                stats['owner'] = owner;
                stats['name'] = name;
                stats['found'] = true;
                if (error.response.status !== 403) {
                    reject(error);
                } else {
                    commit(UPDATE_REPO_LAST_WEEK_STATS, {stats, owner, name});
                    resolve(stats);
                }
            });
        });
    },
    [LOAD_REPO_DATA]: ({commit}, {owner, name}) => {
        return new Promise((resolve, reject) => {
            const repoData = R.pathOr('none', ['repoData', owner, name], store.state);
            if (repoData !== 'none') {
                resolve(repoData);
                return repoData
            }
            store.dispatch(LOAD_REPOS).then((repos) => {
                let idx = 0;
                for(idx; idx < repos.length; idx++) {
                    const repo = repos[idx];
                    if (repo.owner === owner && repo.package_name === name) {
                        commit(UPDATE_REPO_DATA, {data: repo, owner, name});
                        resolve(repo);
                        return repo;
                    }
                }
                reject();
            }).catch((error) => {
                // eslint-disable-next-line
                console.error(error)
            });
        });
    }
}