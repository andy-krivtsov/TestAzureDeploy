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

locals {
  infra = jsondecode(read_tfvars_file(find_in_parent_folders("common-infra.tfvars")))

  data = merge(
    jsondecode(read_tfvars_file(find_in_parent_folders("common.tfvars"))),
    jsondecode(read_tfvars_file(find_in_parent_folders("env.tfvars")))
  )

  front_service_url = "https://${local.data.front_service_name}${local.data.hostname_suffix}.${local.data.custom_domain}"
}

inputs = merge(
  local.infra,
  {
    resource_group           = local.data.resource_group
    name_suffix              = local.data.name_suffix

    pubsub_handlers          = {
      "front"       = "${local.front_service_url}${local.data.pubsub_handler_path}"
      "front_local" = "tunnel://${local.data.pubsub_handler_path}"
    }

    app_client_id            = dependency.aad.outputs.client_id
    app_client_secret        = dependency.aad.outputs.client_secret
    app_service_principal_id = dependency.aad.outputs.service_principal_id
    app_tenant_id            = dependency.aad.outputs.tenant_id
  }
)