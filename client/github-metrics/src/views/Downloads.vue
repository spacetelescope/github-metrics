<template>
  <div class="container">
    <section>
        <PackageSearchControl/>
    </section>
    <section>
      <div class="download-container">
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