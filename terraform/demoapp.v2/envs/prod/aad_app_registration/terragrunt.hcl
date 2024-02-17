terraform {
  source = "../../../modules/aad_app_registration"
}

# Load common config - backend generator, tflint hook, tf options
include "root" {
  path = find_in_parent_folders()
}

locals {
  data = merge(
    jsondecode(read_tfvars_file(find_in_parent_folders("common.tfvars"))),
    jsondecode(read_tfvars_file(find_in_parent_folders("env.tfvars")))
  )

  front_service_url     = "https://${local.data.front_service_name}${local.data.hostname_suffix}.${local.data.custom_domain}"
}

inputs = {
  display_name = local.data.app_display_name
  description  = local.data.app_description
  homepage_url = local.front_service_url
  logout_url   = "${local.front_service_url}${local.data.logout_path}"
  redirect_uris = [
    "${local.front_service_url}${local.data.redirect_path}",
    "${local.data.front_local_url}${local.data.redirect_path}"
  ]
}

