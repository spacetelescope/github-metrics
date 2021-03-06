import Vue from 'vue'
import App from './App.vue'
import store from './store'
import router from './router'
import VueTour from 'vue-tour'
import VueCookies from 'vue-cookies'

require('vue-tour/dist/vue-tour.css')

// https://github.com/FortAwesome/vue-fontawesome#installation
import { library } from '@fortawesome/fontawesome-svg-core'
import { faTimesCircle, faCheck, faExternalLinkAlt, faEdit, faSearch } from '@fortawesome/free-solid-svg-icons'
// import { faFontAwesome } from '@fortawesome/free-brands-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

library.add(faSearch)
library.add(faEdit)
library.add(faCheck)
library.add(faTimesCircle)
library.add(faExternalLinkAlt)
Vue.component('font-awesome-icon', FontAwesomeIcon)
Vue.use(require('vue-moment'))
Vue.use(VueTour)
Vue.use(VueCookies)

Vue.config.productionTip = false

new Vue({
  router,
  store,
  render: h => h(App),
}).$mount('#app')
