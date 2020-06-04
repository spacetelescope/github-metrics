<template>
    <div class="container">
        <section>
            <PackageSearchControl/>
        </section>
        <section>
            <div class="table-container">
                <table class="table is-bordered is-striped">
                    <thead>
                        <tr>
                            <th> Package Name </th>
                            <th> Organization </th>
                            <th> Archived </th>
                            <th> Astroconda Contrib Repo </th>
                            <th> Version </th>
                            <th> Top Contributors </th>
                            <th> Open Pull Requests </th>
                            <th> Pull Requests CLosed Last Week </th>
                            <th> Open Issues </th>
                            <th> Issues Closed Last Week </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="row in filteredRows" :key="row.key">
                            <td>
                                <a :href="row.repo_url" target="_blank">
                                    <font-awesome-icon icon="external-link-alt"/>
                                </a>
                                {{ row.package_name }}
                            </td>
                            <td> {{ row.owner }} </td>
                            <td class="center-icon">
                                <font-awesome-icon v-if="!row.archived" icon="times-circle"/>
                                <font-awesome-icon v-if="row.archived" icon="check"/> 
                            </td>
                            <td class="center-icon">
                                <font-awesome-icon v-if="!row.astroconda_contrib_repo" icon="times-circle"/> 
                                <font-awesome-icon v-if="row.astroconda_contrib_repo" icon="check"/>
                            </td>
                            <td>
                                <a :href="row.rtcname_url" target="_blank">
                                    <font-awesome-icon icon="external-link-alt"/>
                                </a>
                                &nbsp; {{ row.rtcname }}
                            </td>
                            <td class="center-number">
                                {{ row.top_contributor }}
                            </td>
                            <td class="center-number"> 
                                <a :href="row.pull_requests_open_url" target="_blank">
                                    <font-awesome-icon icon="external-link-alt"/>
                                </a>
                                {{ row.pull_requests_open }}
                            </td>
                            <td class="center-number"> 
                                {{ row.pull_requests_closed_last_week }}
                            </td>
                            <td class="center-number"> 
                                <a :href="row.issues_open_url" target="_blank">
                                    <font-awesome-icon icon="external-link-alt"/>
                                </a>
                                {{ row.issues_open }}
                            </td>
                            <td class="center-number"> 
                                {{ row.issues_closed_last_week }}
                            </td>
                        </tr>
                    </tbody>
                    <tfoot>
                    </tfoot>
                </table>
            </div>
        </section>
    </div>
</template>

<script>
import * as R from 'ramda';
import { mapState } from 'vuex';
import PackageSearchControl from '../components/PackageSearchControl.vue';

export default {
    components: {
        PackageSearchControl
    },
    computed: {
        ...mapState({
            filteredRows: (state) => R.pathOr([], ['filteredRows'], state),
            filteredRowsQuery: (state) => state.filteredRowsQuery
        })
    },
    data () {
        return {
            row: {}
        }
    }
}
</script>
<style scoped>
.center-number {
    text-align: center;
}
.center-icon {
    text-align: center;
    vertical-align: middle;
}
.table-container {
  padding: 4rem 0 1.5rem 0 !important;
}
</style>