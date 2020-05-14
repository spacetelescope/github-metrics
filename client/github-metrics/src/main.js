import Vue from 'vue'
import App from './App.vue'
import store from './store'

// https://github.com/FortAwesome/vue-fontawesome#installation
import { library } from '@fortawesome/fontawesome-svg-core'
import { faTimesCircle, faCheck, faExternalLinkAlt, faEdit } from '@fortawesome/free-solid-svg-icons'
// import { faFontAwesome } from '@fortawesome/free-brands-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

library.add(faEdit)
library.add(faCheck)
library.add(faTimesCircle)
library.add(faExternalLinkAlt)
Vue.component('font-awesome-icon', FontAwesomeIcon)

Vue.config.productionTip = false

new Vue({
  render: h => h(App),
  store
}).$mount('#app')
