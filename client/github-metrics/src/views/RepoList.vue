<template>
  <div class="container">
    <section>
        <PackageSearchControl/>
    </section>
    <section>
      <div v-for="row in filteredRows" :key="row.key">
        <section class="hero">
          <div class="hero-body">
            <div class="container">
              <h1 class="title has-text-left">
                <router-link class="repo-router-link" :to="{name: 'Repo', params: {owner: row.owner, pkgName: row.package_name}}">
                  {{ row.package_name }}
                </router-link>
              </h1>
              <h2 class="subtitle has-text-left">
                  {{ row.description }}
              </h2>
            </div>
          </div>
        </section>
        <div class="tile is-ancestor">
          <div class="tile is-parent">
            <div class="tile is-child box">
              <p class="title"> Life-time Stats </p>
              <LifeTimeStats :row="row" />
            </div>
          </div>
          <div class="tile is-5 is-vertical is-parent">
            <div class="tile is-child box">
              <p class="title"> Last Weeks Activity </p>
              <p v-if="lastWeekStats(row) === false" class="subtitle"> Repo has not seen a new Issue, Peer Request, or Commit this week </p>
              <table v-if="lastWeekStats(row) !== false" class="table is-bordered is-striped is-narrow is-hoverable is-fullwidth">
                <thead>
                  <tr>
                    <th> Field </th>
                    <th> Value </th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td> Commits </td>
                    <td> {{ lastWeekStats(row).commits }} </td>
                  </tr>
                  <tr>
                    <td> Issues Opened </td>
                    <td> {{ lastWeekStats(row).issues_opened }} </td>
                  </tr>
                  <tr>
                    <td> Issues Closed </td>
                    <td> {{ lastWeekStats(row).issues_closed }} </td>
                  </tr>
                  <tr>
                    <td> Pull Requests Opened </td>
                    <td> {{ lastWeekStats(row).pull_requests_opened }} </td>
                  </tr>
                  <tr>
                    <td> Pull Requests Closed </td>
                    <td> {{ lastWeekStats(row).pull_requests_closed }} </td>
                  </tr>
                </tbody>
                <tfoot></tfoot>
              </table>
            </div>
            <div class="tile is-child box">
              <p class="title"> Build Status </p>
              <table class="table is-bordered is-striped is-narrow is-hoverable is-fullwidth">
                <thead>
                  <tr>
                    <th> Field </th>
                    <th> Value </th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td> Commit </td>
                    <td>
                      <a target="_blank" :href="lastCommit(row).url">
                        <span> {{ lastCommit(row).date |moment("dddd, MMMM Do YYYY") }} </span>
                      </a>
                    </td>
                  </tr>
                  <tr v-for="badge in row.badges" :key="badge.name">
                    <td> {{ badge.name }} </td>
                    <td>
                      <a target="_blank" :href="badge.anchor">
                        <img :src="badge.src" :alt="`${badge.name} success`" />
                      </a>
                    </td>
                  </tr>
                </tbody>
                <tfoot></tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
// https://github.com/jeancroy/fuzz-aldrin-plus
// https://alligator.io/vuejs/vue-client-side-search/
import * as R from 'ramda';
import { mapState } from 'vuex';
import PackageSearchControl from '../components/PackageSearchControl';
import LifeTimeStats from '../components/LifeTimeStats';
import { LOAD_LAST_WEEK_REPOS } from '../store/action-types';

export default {
    computed: {
        ...mapState({
            filteredRows: (state) => R.pathOr([], ['filteredRows'], state).slice(0, 3),
            filteredLastWeekReposMap: (state) => R.pathOr({}, ['filteredLastWeekReposMap'], state)
        })
    },
    components: {
      PackageSearchControl,
      LifeTimeStats
    },
    data () {
        return {
          lastCommit (row) {
            return {
              'date': new Date(row.last_commit_date),
              'url': `${row.repo_url}commit/${row.last_commit_hash}`
            }
          },
          lastWeekStats (row) {
            if (Object.keys(this.filteredLastWeekReposMap).indexOf(row.package_name) < 0) {
              return false
            }
            /* eslint-disable no-debugger */
            // debugger
            let value = this.filteredLastWeekReposMap[row.package_name];
            return {
              'commits': value.commits_weekly,
              'issues_opened': value.issues_opened_weekly,
              'issues_closed': value.issues_closed_weekly,
              'pull_requests_opened': value.pull_requests_opened_weekly,
              'pull_requests_closed': value.pull_requests_closed_weekly,
            }
          },
          row: {}
        }
    },
    mounted () {
      this.$nextTick(() => {
        this.$store.dispatch(LOAD_LAST_WEEK_REPOS)
      })
    }
}
</script>
<style scoped>
.hero-body {
  padding: 4rem 1.5rem 1.5rem 1.5rem !important;
}
.center-number {
    text-align: center;
}
.center-icon {
    text-align: center;
    vertical-align: middle;
}
.repo-router-link {
  color: #3273dc;
}
</style>