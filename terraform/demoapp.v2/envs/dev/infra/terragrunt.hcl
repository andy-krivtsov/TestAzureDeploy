terraform {
  source = "../../../modules/infra"
}

include "root" {
  path = find_in_parent_folders()
}

dependency "aad" {
  config_path = "../aad_app_registration"

  mock_outputs = {
    client_id            = "b9c6db5c-45a7-437b-9ba3-4eca0109e431"
    client_secret        = "secret"
    service_principal_id = "2652e4e8-8c0a-4e9f-850c-1975b2ef7e33"
    tenant_id            = "5cad7af3-948c-4ac3-8073-41b016d17cf8"
  }

  mock_outputs_allowed_terraform_commands = ["validate"]
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
  name_prefix              = local.cmn.name_prefix
  resource_group           = local.cmn.resource_group
  acr_registry             = local.cmn.acr_registry
  acr_registry_rg          = local.cmn.shared_resource_group
  cert_keyvault            = local.cmn.cert_keyvault
  cert_keyvault_rg         = local.cmn.cert_keyvault_rg
  cert_keyvault_key        = local.cmn.cert_keyvault_key
  pubsub_handlers          = {
    "front"       = "${local.cmn.front_service_url}${local.cmn.pubsub_handler_path}"
    "front_local" = "tunnel://${local.cmn.pubsub_handler_path}"
  }
  app_client_id            = dependency.aad.outputs.client_id
  app_client_secret        = dependency.aad.outputs.client_secret
  app_service_principal_id = dependency.aad.outputs.service_principal_id
  app_tenant_id            = dependency.aad.outputs.tenant_id
}

