<template>
<div class="container">
  <div id="container" class="columns">
    <div class="column is-one-quarter">
      <aside class="menu">
        <p class="menu-label">
          Github Metrics
        </p>
        <ul class="menu-list">
          <li><a class="is-active">Dashboard</a></li>
          <!-- <li><a>Customers</a></li> -->
        </ul>
        <!-- <p class="menu-label">
          Administration
        </p>
        <ul class="menu-list">
          <li><a>Team Settings</a></li>
          <li>
            <a class="is-active">Manage Your Team</a>
            <ul>
              <li><a>Members</a></li>
              <li><a>Plugins</a></li>
              <li><a>Add a member</a></li>
            </ul>
          </li>
          <li><a>Invitations</a></li>
          <li><a>Cloud Storage Environment Settings</a></li>
          <li><a>Authentication</a></li>
        </ul>
        <p class="menu-label">
          Transactions
        </p>
        <ul class="menu-list">
          <li><a>Payments</a></li>
          <li><a>Transfers</a></li>
          <li><a>Balance</a></li>
        </ul> -->
      </aside>
    </div>
    <div class="column is-three-quarters">
        <header>
          <ul class="list-align">
            <li>
              If there hasn't been any github release or tag then the information is taken from the last commit to that repository
            </li>
            <li>
              The issues count includes PRs becuase the API doesn't separate them, the avg open issue time has been corrected for this.
            </li>
            <li>
              Top contributors are listed for maintenance reference, no relation to quality or size of commits
            </li>
            <li>
              RTD-latest: guesses that the docs are named in RTD using the package name, 'unknown', most likely means the RTD docs, if they exist, are not using the GitHub package name 
            </li>
            <li>
              <strong> Updated Daily: </strong>
              <a target="_blank" href="https://github-metrics-stsci-edu-prod.s3.amazonaws.com/timeseries/github-metrics.csv"> download timeseries CSV </a>
            </li>
          </ul>
        </header>
        <CSVTable/>
        <footer>
          footer
        </footer>
    </div>
  </div>
  </div>
</template>

<script>
import CSVTable from './CSVTable'

export default {
  components: {
    CSVTable
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.list-align {
  text-align: left;
}
</style>
