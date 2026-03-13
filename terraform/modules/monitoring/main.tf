resource "helm_release" "grafana_stack" {
    name             = "lgtm"
    repository       = "https://grafana.github.io/helm-charts"
    chart            = "loki-stack"
    namespace        = "monitoring"
    create_namespace = true

    set = [
        {
            name  = "grafana.enabled"
            value = "true"
        },
        {
            name  = "prometheus.enabled"
            value = "true"
        }
    ]
}
