/**
 * Apex Global Inventory - Dashboard Charts Initialization
 */

document.addEventListener('DOMContentLoaded', function () {
  const salesCanvas = document.getElementById('salesTrendChart');
  const catCanvas = document.getElementById('categoryDoughnutChart');
  const moveCanvas = document.getElementById('movementBarChart');

  if (!salesCanvas && !catCanvas && !moveCanvas) return;

  fetch('/dashboard/chart-data')
    .then(res => res.json())
    .then(data => {
      // 1. Sales Trend Area Chart
      if (salesCanvas && data.sales_trend) {
        const ctx = salesCanvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(79, 70, 229, 0.35)');
        gradient.addColorStop(1, 'rgba(79, 70, 229, 0.0)');

        new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.sales_trend.labels,
            datasets: [{
              label: 'Daily Revenue (₹)',
              data: data.sales_trend.data,
              borderColor: '#4f46e5',
              backgroundColor: gradient,
              borderWidth: 2.5,
              pointBackgroundColor: '#4f46e5',
              pointBorderColor: '#ffffff',
              pointBorderWidth: 2,
              pointRadius: 4,
              pointHoverRadius: 6,
              fill: true,
              tension: 0.35
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: function (context) {
                    return ` Revenue: ₹${context.parsed.y.toFixed(2)}`;
                  }
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                grid: { color: '#f1f5f9' },
                ticks: {
                  callback: function (val) {
                    return '₹' + val;
                  }
                }
              },
              x: {
                grid: { display: false }
              }
            }
          }
        });
      }

      // 2. Category Distribution Doughnut Chart
      if (catCanvas && data.category_distribution) {
        const ctx = catCanvas.getContext('2d');
        const colorsList = ['#4f46e5', '#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];

        new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: data.category_distribution.labels,
            datasets: [{
              data: data.category_distribution.data,
              backgroundColor: colorsList.slice(0, data.category_distribution.labels.length),
              borderWidth: 2,
              borderColor: '#ffffff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: { boxWidth: 12, padding: 12, font: { size: 11 } }
              }
            },
            cutout: '72%'
          }
        });
      }

      // 3. Stock Movement Bar Chart
      if (moveCanvas && data.movement_breakdown) {
        const ctx = moveCanvas.getContext('2d');
        new Chart(ctx, {
          type: 'bar',
          data: {
            labels: data.movement_breakdown.labels,
            datasets: [{
              label: 'Transaction Count',
              data: data.movement_breakdown.data,
              backgroundColor: '#6366f1',
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false }
            },
            scales: {
              y: {
                beginAtZero: true,
                grid: { color: '#f1f5f9' },
                ticks: { stepSize: 1 }
              },
              x: {
                grid: { display: false }
              }
            }
          }
        });
      }
    })
    .catch(err => console.error('Error fetching dashboard chart data:', err));
});
