module "vpc" {
  source       = "./modules/vpc"
}

# Call the EKS Module and pass VPC data
module "eks" {
  source             = "./modules/eks"
}

# Call the Monitoring Module
module "monitoring" {
  source       = "./modules/monitoring"
  depends_on   = [module.eks] # Wait for EKS to be ready
}