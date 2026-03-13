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
resource "helm_release" "aws_lb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"

    set = [ {
        name  = "clusterName"
        value = var.cluster_name
        },
        {
        name  = "serviceAccount.create"
        value = "true"
        }
    ]

    # Note: Requires an IAM Role for Service Accounts (IRSA) to manage ALBs
}
