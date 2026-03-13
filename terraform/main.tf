module "vpc" {
  source       = "./modules/vpc"
  project_name = var.project_name # (Root Var -> VPC Var)
}

module "rds" {
  source               = "./modules/rds"
  db_username          = var.db_username # (Root Var -> RDS Var)
  # (VPC Output -> RDS Var) - This is the "Glue"
  db_subnet_group_name = module.vpc.database_subnet_group_name 
}

module "eks" {
  source             = "./modules/eks"
  # (VPC Output -> EKS Var)
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnets
}