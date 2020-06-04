<template>
  <div class="container">
    <section>
        <PackageSearchControl/>
    </section>
    <section>
      <div class="table-container">
        <table class="table is-bordered is-striped is-narrow is-hoverable is-fullwidth">
          <thead>
            <tr>
              <th>
                Package Name
              </th>
              <th v-for="label in labels" :key="label">
                {{ label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="row.repo_url">
              <td>
                {{ row.package_name }}
              </td>
              <td v-for="label in labels" :key="label">
                <a v-if="badges(row)[label]" target="_blank" :href="badges(row)[label]['anchor']">
                  <img :src="badges(row)[label]['src']" :alt="row.package_name"/>
                </a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script>
import * as R from 'ramda';
// import { LOAD_REPOS } from '../store/action-types';
import { mapState } from 'vuex';
import PackageSearchControl from '../components/PackageSearchControl'

export default {
  components: {
    PackageSearchControl
  },
  computed: {
    ...mapState({
      rows: (state) => R.pathOr([], ['repos'], state),
      filteredRows: (state) => R.pathOr([], ['filteredRows'], state).slice(0, 100)
    }),
    labels: {
      get () {
        let idx = 0;
        const labels = [];
        for (idx; idx < this.rows.length; idx++) {
          let value = this.rows[idx];
          let bdx = 0;
          for (bdx; bdx < value.badges.length; bdx++) {
            let badge = value.badges[bdx];
            if (labels.indexOf(badge.name) < 0) {
              labels.push(badge.name)
            }
          }
        }
        return labels;
      }
    }
  },
  data () {
    return {
      badges (row) {
        const badges = {};
        let idx = 0;
        for (idx; idx < row.badges.length; idx++) {
          let value = row.badges[idx];
          badges[value.name] = {
            'src': value.src,
            'anchor': value.anchor
          }
        }
        return badges
      }
    }
  },
  mounted () {
    // this.$nextTick(() => {
    //   if (this.rows.length === 0) {
    //     this.$store.dispatch(LOAD_REPOS).then((rows) => {
    //       /* eslint-disable no-debugger */
    //       debugger
    //     })
    //   } else {
    //     /* eslint-disable no-debugger */
    //     debugger
    //   }
    //   // this.$store.dispatch(LOAD_REPO_LIST)
    //   /* eslint-disable no-debugger */
    //   // debugger
    // })
  }
}
</script>
<style scoped>
.table-container {
  padding: 4rem 0 1.5rem 0 !important;
}
</style>