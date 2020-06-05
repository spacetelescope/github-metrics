<template>
  <div class="container">
    <section>
      <PackageSearchControl/>
      <article class="message is-link">
        <div class="message-header">
          <p> Datasource not connected </p>
        </div>
        <div class="message-body">
          The data that which fills this chart is randomly generated. Real Data will be installed sometime in the next couple of weeks
        </div>
      </article>
    </section>
    <section>
      <div class="download-container">
        <p class="subtitle">
          Data displayed here is gathered from Github, Astroconda Channel, and Astroconda ETC Channel. Logs are parsed and the count of downloads tallied and displayed
        </p>
        <DownloadStats />
      </div>
    </section>
  </div>
</template>

<script>
import * as R from 'ramda';
// import { LOAD_REPO_LIST } from '../store/action-types';
import { mapState } from 'vuex';
import PackageSearchControl from '../components/PackageSearchControl'
import DownloadStats from '../components/DownloadStats.vue'

export default {
  components: {
    PackageSearchControl,
    DownloadStats
  },
  computed: {
    ...mapState({
      // orgs: (state) => R.pathOr([], ['repoList'], state),
      filteredRows: (state) => R.pathOr([], ['filteredRows'], state).slice(0, 100)
    })
  },
  mounted () {
    this.$nextTick(() => {
      // this.$store.dispatch(LOAD_REPO_LIST)
    })
  }
}
</script>
<style scoped>
.download-container {
  padding: 4rem 0 1.5rem 0 !important;
}
</style>