<script>
import { Line } from 'vue-chartjs';
import Chart from 'chart.js'

export default {
  extends: Line,
  props: ['labels', 'opened', 'closed'],
  watch: {
    labels: function () {
      this.render();
    }
  },
  mounted () {
    this.render();
  },
  methods: {
    render: function () {
      const options = {
        responsive: true,
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Pull Requests Opened / Closed'
        },
        tooltips: {
          // enabled: false,
        },
        hover: {
          animationDuration: 0,
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
          },
        },
      };
      const data = {
        labels: this.labels,
        datasets: [{
          fill: true,
          label: 'Closed Pull Requests',
          borderWidth: 4,
          backgroundColor: 'hsl(141, 53%, 53%, 0.6)',
          data: this.$props.closed,
        }, {
          fill: true,
          label: 'Opened Pull Requests',
          borderWidth: 1,
          backgroundColor: 'hsl(348, 100%, 61%, 0.6)',
          data: this.$props.opened,
        }],
      };
      this.renderChart(data, options);
    }
  }
}
</script>