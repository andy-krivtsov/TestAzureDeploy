generate "backend" {
  path      = "backend.tf"
  if_exists = "overwrite_terragrunt"
  contents = <<EOF
terraform {
  required_version = ">= 1.6"

  backend "azurerm" {
    resource_group_name  = "Terraform"
    storage_account_name = "aktfstate"
    container_name       = "tfstate"
    key                  = "dev/${path_relative_to_include()}/terraform.tfstate"
  }
}
EOF
}

terraform {
  before_hook "before_hook" {
    commands     = ["apply", "plan", "validate"]
    execute      = ["tflint", "--terragrunt-external-tflint"]
  }

  extra_arguments "retry_lock" {
    commands  = get_terraform_commands_that_need_locking()
    arguments = ["-lock-timeout=5m"]
  }
}