<template>
  <div id="app">
    <AppLayout />
  </div>
</template>

<script>
import AppLayout from './components/AppLayout.vue'
import './../node_modules/bulma/css/bulma.min.css'
// import './../node_modules/font-awesome/css/font-awesome.min.css'

export default {
  name: 'app',
  components: {
    AppLayout
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
