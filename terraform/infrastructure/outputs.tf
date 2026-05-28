output "cluster_name" {
  value = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.url_shortener.name
}

output "app_url" {
  value = "https://${var.app_subdomain}.${var.domain_name}"
}

output "cost_reminder" {
  value = "⚠️  Remember to run terraform destroy when done to stop billing"
}