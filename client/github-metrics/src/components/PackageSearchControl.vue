<template>
    <div class="content">
        <h1 class="header has-text-left"> Search by Package Name </h1>
        <div class="control">
            <input class="input is-rounded" v-model="query" type="text" placeholder="hstcal">
        </div>
    </div>
</template>

<script>
// https://github.com/jeancroy/fuzz-aldrin-plus
// https://alligator.io/vuejs/vue-client-side-search/
import fz from 'fuzzaldrin-plus';
import * as R from 'ramda';
import { LOAD_REPOS } from '../store/action-types';
import { UPDATE_FILTERED_ROWS, UPDATE_FILTERED_ROWS_QUERY, UPDATE_FILTERED_LAST_WEEK_REPOS } from '../store/mutation-types';
import { mapState } from 'vuex';

export default {
    computed: {
        ...mapState({
            rows: (state) => R.pathOr([], ['repos'], state),
            lastWeekRepos: (state) => R.pathOr([], ['lastWeekRepos'], state),
            filteredRowsQuery: (state) => state.filteredRowsQuery,
            filteredLastWeekRepos: (state) => state.filteredLastWeekRepos
        }),
        query: {
            get () {
                return this.filteredRowsQuery || ''
            },
            set (val) {
                this.$store.commit(UPDATE_FILTERED_ROWS_QUERY, val)
                this.queryForResults()
            }
        }
        
    },
    mounted () {
        if (this.rows.length === 0) {
            this.$nextTick(() => {
                this.$store.dispatch(LOAD_REPOS).then(() => {
                    this.queryForResults()
                })
            });
        }
    },
    data () {
        return {
            queryForResults: () => {
                /* eslint no-console: ["error", { allow: ["warn","log"] }] */
                // console.log('filteredRowsQuery', this.filteredRowsQuery)
                if(!this.filteredRowsQuery) {
                    this.$store.commit(UPDATE_FILTERED_ROWS, this.rows);
                    this.$store.commit(UPDATE_FILTERED_LAST_WEEK_REPOS, this.lastWeekRepos)
                    return this.rows;
                }

                const preparedQuery = fz.prepareQuery(this.filteredRowsQuery);
                const scores = {};
                const filteredRows = this.rows
                    .map((option) => {
                        const fields = [
                            option.package_name
                        ].map(toScore => fz.score(toScore, this.filteredRowsQuery, { preparedQuery }))
                        scores[option.repo_url] = Math.max(...fields)
                        /* eslint no-console: ["error", { allow: ["warn","log"] }] */
                        // console.log(scores[option.repo_url], option.package_name)
                        return option;
                    })
                    .filter(option => scores[option.repo_url] > 1)
                    .sort((a, b) => scores[b.repo_url] - scores[a.repo_url]);
                this.$store.commit(UPDATE_FILTERED_ROWS, filteredRows)

                const preparedQuery_LastWeekRepos = fz.prepareQuery(this.filteredRowsQuery);
                const scores_LastWeekRepos = {};
                const filteredRows_LastWeekRepos = this.lastWeekRepos
                    .map((option) => {
                        const fields = [
                            option.package_name
                        ].map(toScore => fz.score(toScore, this.filteredRowsQuery, { preparedQuery_LastWeekRepos }))
                        scores_LastWeekRepos[option.repo_url] = Math.max(...fields);
                        return option;
                    })
                    .filter(option => scores_LastWeekRepos[option.repo_url] > 1)
                    .sort((a, b) => scores_LastWeekRepos[b.repo_url] - scores_LastWeekRepos[a.repo_url]);
                this.$store.commit(UPDATE_FILTERED_LAST_WEEK_REPOS, filteredRows_LastWeekRepos)
                return []
            },
        }
    }
}
</script>