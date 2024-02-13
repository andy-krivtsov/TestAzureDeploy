terraform {
  source = "../../../modules/aad_app_registration"
}

# Load common config - backend generator, tflint hook, tf options
include "root" {
  path = find_in_parent_folders()
}

# Load common locals variables
include "env" {
  path           = find_in_parent_folders("env-vars.hcl")
  expose         = true
  merge_strategy = "no_merge"
}

locals {
  cmn = include.env.locals
}

inputs = {
  display_name = local.cmn.app_display_name
  description  = local.cmn.app_description
  homepage_url = local.cmn.front_service_url
  logout_url   = "${local.cmn.front_service_url}${local.cmn.logout_path}"
  redirect_uris = [
    "${local.cmn.front_service_url}${local.cmn.redirect_path}",
    "${local.cmn.front_local_url}${local.cmn.redirect_path}"
  ]
}

