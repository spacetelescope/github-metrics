<template>
  <div class="container">
    <section>
      <h1 class="title has-text-left">
        {{ name }}
      </h1>
      <!-- <slider type="success" size="large" :value="value" :max="max" steps="1" is-fullwidth @change="updateSlider" /> -->
    </section>
    <div class="page-container">
      <article v-if="this.repo === undefined" class="message is-link">
        <div class="message-header">
          <p> {{ name }} pkg is not found </p>
        </div>
        <div class="message-body">
          Package {{name}} is not a known package
          <br/>
          {{ this.repo.package_name }}
        </div>
      </article>
    </div>
    <section if-else class="page-container columns">
      <div class="column is-one-third is-full-mobile">
        <IssueGraph :labels="labels" :opened="issuesOpened" :closed="issuesClosed" />
      </div>
      <div class="column is-one-third is-full-mobile">
        <PullRequestGraph :labels="labels" :opened="pullRequestsOpened" :closed="pullRequestsClosed" />
      </div>
      <div class="column is-one-third is-full-mobile">
        <CommitsGraph :labels="labels" :commits="commits" />
      </div>
    </section>
    <!-- <p> Repo drilldown and aggregate stats are still being built </p> -->
  </div>
</template>
<style scoped>
.page-container {
  padding: 4rem 0 1.5rem 0 !important;
}
</style>
<script>
// import Slider from './../components/Slider';
import IssueGraph from './../components/IssueGraph';
import PullRequestGraph from './../components/PullRequestGraph';
import CommitsGraph from './../components/CommitsGraph';
import { mapState } from 'vuex';
import router from '../router';
import * as R from 'ramda';
import { LOAD_REPO_LAST_WEEK_STATS, LOAD_REPO_DATA } from '../store/action-types';

export default {
  mounted () {
    this.$nextTick(() => {
      this.owner = this.$router.currentRoute.params.owner;
      this.name = this.$router.currentRoute.params.pkgName;
      this.$store.dispatch(LOAD_REPO_DATA, {owner: this.owner, name: this.name});
      this.$store.dispatch(LOAD_REPO_LAST_WEEK_STATS, {owner: this.owner, name: this.name});
    });
  },
  computed: {
    // filteredRows: (state) => R.pathOr([], ['filteredRows'], state)
    ...mapState({
      // repos: (state) => R.pathOr([], ['repos'], state),
      lastWeekStats: (state) => R.pathOr([], ['lastWeekStats', router.currentRoute.params.owner, router.currentRoute.params.pkgName], state),
      repo: (state) => R.pathOr({}, ['repoData', router.currentRoute.params.owner, router.currentRoute.params.pkgName], state),
    }),
    labels: {
      get: function () {
        return this.lastWeekStats.reduce((acc, value) => {
          acc.push(value['start']);
          return acc;
        }, []);
      }
    },
    issuesOpened: {
      get: function () {
        return this.lastWeekStats.reduce((acc, value) => {
          acc.push(value['issues_opened']);
          return acc;
        }, []);
      },
    },
    issuesClosed: {
      get: function () {
        return this.lastWeekStats.reduce((acc, value) => {
          acc.push(value['issues_closed']);
          return acc;
        }, []);
      },
    },
    pullRequestsOpened: {
      get: function () {
        return this.lastWeekStats.reduce((acc, value) => {
          acc.push(value['pull_requests_opened']);
          return acc;
        }, []);
      },
    },
    pullRequestsClosed: {
      get: function () {
        return this.lastWeekStats.reduce((acc, value) => {
          acc.push(value['pull_requests_closed']);
          return acc;
        }, []);
      },
    },
    commits: {
      get: function () {
        return this.lastWeekStats.reduce((acc, value) => {
          acc.push(value['commits']);
          return acc;
        }, []);
      },
    },
  },
  components: {
    // Slider
    IssueGraph,
    PullRequestGraph,
    CommitsGraph,
  },
  data () {
    return {
      name: undefined,
      owner: undefined,
      // Silder
      value: '50',
      max: 100,
      updateSlider: () => {
        // eslint-disable-next-line
        console.log('awesome')
      }
    }
  }
}
</script>