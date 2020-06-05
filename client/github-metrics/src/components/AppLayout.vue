<template>
<div class="container">
  <section class="hero">
    <!-- <h1 class="header"> Github Metrics </h1> -->
    <div class="hero-body">
      <div class="container has-text-left">
        <h1 class="title">
          Github Metrics
          <span class="subtitle"> [beta] </span>
        </h1>
        <h2 class="subtitle">
          monitor opensource contributions
        </h2>
      </div>
    </div>
  </section>
  <section class="row">
    <div id="container" class="columns">
      <div class="column is-one-quarter">
        <aside class="menu">
          <p class="menu-label">
          </p>
          <ul class="menu-list has-text-left">
            <li>
              <router-link active-class="is-active" to="/dashboard"> Dashboard Overview </router-link>
            </li>
            <li>
              <router-link data-v-tour="1" active-class="is-active" to="/repo-list"> Repo List </router-link>
            </li>
            <li>
              <router-link active-class="is-active" to="/builds"> Build List </router-link>
            </li>
            <li>
              <router-link active-class="is-active" to="/downloads"> Download List </router-link> 
            </li>
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
        <router-view/>
      </div>
    </div>
  </section>
  <v-tour name="myTour" :steps="steps" :callbacks="myCallbacks"></v-tour>
</div>
</template>

<script>
export default {
  mounted () {
    this.$nextTick(() => {
      const sessionData = this.$cookies.get(this.sessionDataKey) || {};
      // eslint-disable-next-line no-console
      // console.log(sessionData)
      /* eslint-disable no-debugger */
      // debugger
      if (!Object.prototype.hasOwnProperty.call(sessionData, 'tourComplete')) {
        this.$tours['myTour'].start()
      } else if (sessionData.tourComplete !== true) {
        this.$tours['myTour'].start()
      }
    })
  },
  data () {
    return {
      sessionDataKey: 'userSessionDataInsecure',
      setTourComplete: () => {
        // https://www.npmjs.com/package/vue-cookies#set-other-arguments
        // keyName, value, expireTimes, path, domain, secure, sameSite
        // this.$cookies.set(this.sessionDataKey, {'tourComplete': true}, null, null, null, true, null)
        // TODO: Make this secure
        this.$cookies.set(this.sessionDataKey, {'tourComplete': true})
      },
      myCallbacks: {
        onSkip: () => {
          this.setTourComplete()
        },
        onFinish: () => {
          this.setTourComplete()
        }
      },
      steps: [
        {
          target: '[data-v-tour="0"]',
          header: {
            title: 'Search by Package Name'
          },
          content: 'Begin by typing "hstcal" or "drizzlepac"'
        },
        {
          target: '[data-v-tour="1"]',
          header: {
            title: 'Repo List'
          },
          content: 'With "hstcal" or "drizzlepac" inserted into the search, click "Repo List" to see stats for that Repository'
        }
      ]
    }
  }
}
</script>
<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.list-align {
  text-align: left;
}
</style>
