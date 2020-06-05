<script>
import { Bar } from 'vue-chartjs'
import Chart from 'chart.js'

export default {
  extends: Bar,
  props: ['row'],
  mounted () {
    const options = {
      responsive: true,
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `${this.row.package_name} Stats`
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
    const data = {
      labels: [
        'Commits',
        'Issues',
        'Pull Requests',
        'Contributors',
        'Contents',
        'Tags',
        'Forks',
        'Watchers',
        'Stars'
      ],
      datasets: [{
        label: this.row.package_name,
        borderWidth: 1,
        backgroundColor: 'rgba(255, 99, 132, 0.4)',
        data: [
          this.row.count_commits,
          this.row.count_issues,
          this.row.count_pull_requests,
          this.row.count_contributors,
          this.row.count_contents,
          this.row.count_tags,
          this.row.count_forks,
          this.row.count_watchers,
          this.row.count_stars,
        ]
      }]
    };
    this.renderChart(data, options);
  }
}
</script>