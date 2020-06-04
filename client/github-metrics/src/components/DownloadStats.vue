<script>
import { HorizontalBar } from 'vue-chartjs'
import Chart from 'chart.js'
import { mapState } from 'vuex';
import * as R from 'ramda';

export default {
  extends: HorizontalBar,
  computed: {
    ...mapState({
      filteredRows: (state) => R.pathOr([], ['filteredRows'], state)
    })
  },
  watch: {
    filteredRows () {
      this.$data.rebuildData()
      this.$data._chart.update()  
    }
  },
  data () {
    return {
      rebuildData: () => {
        const labels = []
        const github = {
          label: 'Github Downloads',
          borderWidth: 1,
          data: [],
          backgroundColor: 'rgba(255, 99, 132, 0.2)'
        };
        const astroconda = {
          label: 'Astroconda Channel',
          borderWidth: 1,
          data: [],
          backgroundColor: 'rgba(54, 162, 235, 0.2)'
        };
        const astrocondaEtc = {
          label: 'Astroconda ETC Channel',
          borderWidth: 1,
          data: [],
          backgroundColor: 'rgba(255, 159, 64, 0.2)'
        };
        let idx = 0;
        for (idx; idx < this.filteredRows.length; idx++) {
          let value = this.filteredRows[idx];
          labels.push(value.package_name);
          github['data'].push(parseInt(Math.random() * 1000));
          astroconda['data'].push(parseInt(Math.random() * 1000));
          astrocondaEtc['data'].push(parseInt(Math.random() * 1000));
        }
        this.chartData.labels = labels;
        this.chartData.datasets = [github, astroconda, astrocondaEtc];
      },
      chartData: {
        labels: [],
        datasets: [],
      }
    }
  },
  mounted () {
    const options = {
      responsive: true,
      type: 'horizontalBar',
      legend: {
        position: 'right',
      },
      title: {
        display: true,
        text: 'Downloads by Channel'
      },
      tooltips: {
        enabled: false,
      },
      hover: {
        animationDuration: 0
      },
      animation: {
        onComplete: function () {
          var chartInstance = this.chart,
          ctx = chartInstance.ctx;
          ctx.font = Chart.helpers.fontString(Chart.defaults.global.defaultFontSize, Chart.defaults.global.defaultFontStyle, Chart.defaults.global.defaultFontFamily);
          ctx.textAlign = 'center';
          ctx.textBaseline = 'bottom';
          this.data.datasets.forEach(function (dataset, i) {
              var meta = chartInstance.controller.getDatasetMeta(i);
              meta.data.forEach(function (bar, index) {
                  var data = dataset.data[index];                            
                  ctx.fillText(data, bar._model.x, bar._model.y - 5);
              });
          });
        }
      }
    };
    this.rebuildData();
    /* eslint-disable no-debugger */
    // debugger
    this.renderChart(this.chartData, options);
    this.$data._chart.update();
  }
}
</script>