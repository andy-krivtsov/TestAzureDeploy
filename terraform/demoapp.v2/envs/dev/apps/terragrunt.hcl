terraform {
  source = "../../../modules/apps"
}

include "root" {
  path = find_in_parent_folders()
}

locals {
  data = merge(
    jsondecode(read_tfvars_file(find_in_parent_folders("common-infra.tfvars"))),
    jsondecode(read_tfvars_file(find_in_parent_folders("common.tfvars"))),
    jsondecode(read_tfvars_file(find_in_parent_folders("env.tfvars"))),
    jsondecode(file(find_in_parent_folders("deploy-vars.json")))
  )

  front_service_url = "https://${local.data.front_service_name}${local.data.hostname_suffix}.${local.data.custom_domain}"
  back_service_url  = "https://${local.data.back_service_name}${local.data.hostname_suffix}.${local.data.custom_domain}"

  servicebus_namespace = "${local.data.servicebus_namespace}-${local.data.name_suffix}.servicebus.windows.net"
  db_url               = "https://${local.data.db_account}-${local.data.name_suffix}.documents.azure.com:443/"
  storage_url          = "https://${local.data.storage_account}${local.data.name_suffix}.blob.core.windows.net/"
  pubsub_url           = "https://${local.data.web_pubsub}-${local.data.name_suffix}.webpubsub.azure.com"

}

inputs = {
  # infra
  con_app_env           = local.data.con_app_env
  con_app_env_rg        = local.data.resource_group
  con_app_env_cert      = local.data.con_app_env_cert
  con_app_user_identity = local.data.con_app_env_identity
  acr_registry          = local.data.acr_registry
  acr_registry_rg       = local.data.acr_registry_rg
  keyvault_prefix       = local.data.keyvault_prefix
  keyvault              = "${local.data.keyvault}-${local.data.name_suffix}"
  keyvault_rg           = local.data.resource_group
  hostname_suffix       = local.data.hostname_suffix
  custom_domain         = local.data.custom_domain
  custom_dns_zone_rg    = local.data.custom_dns_zone_rg
  revision_suffix       = local.data.revision_suffix

  app_image = local.data.app_image
  app_tag   = local.data.app_tag

  app_global_env = {
    SERVICEBUS_NAMESPACE                 = local.servicebus_namespace
    SERVICEBUS_ORDERS_TOPIC              = local.data.servicebus_orders_topic
    SERVICEBUS_STATUS_TOPIC              = local.data.servicebus_status_topic
    DB_URL                               = local.db_url
    DB_DATABASE                          = local.data.db_database
    STORAGE_URL                          = local.storage_url
    STORAGE_CONTAINER                    = local.data.storage_container
    WEB_PUBSUB_ENDPOINT                  = local.pubsub_url
    OTEL_RESOURCE_ATTRIBUTES             = "service.namespace=demoapp"
    OTEL_TRACES_SAMPLER_ARG              = 1
    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS = "azure_app_service"
    OTEL_PYTHON_EXCLUDED_URLS            = "/health/*"
  }

  keyvault_secrets = [
    "auth-client-id",
    "auth-client-secret",
    "auth-tenant-id",
    "auth-session-key",
    "app-insights-constr"
  ]

  # Can be overrited in CLI with -var 'app_list={}' parameter to deploy without applications themselves
  app_list = {
    "${local.data.front_service_name}" = {
      args = ["--host", "0.0.0.0", "demoapp.orders_front:app"]
      envs = {
        OTEL_SERVICE_NAME     = "Front"
        SERVICEBUS_STATUS_SUB = local.data.servicebus_front_status_sub
        SERVICEBUS_ORDERS_SUB = ""
        DB_CONTAINER          = local.data.db_orders_container
        AUTH_PUBLIC_URL       = local.front_service_url
        WEB_PUBSUB_HUB        = local.data.web_pubsub_front_hub
      }
    }

    "${local.data.back_service_name}" = {
      args = ["--host", "0.0.0.0", "demoapp.orders_back:app"]
      envs = {
        OTEL_SERVICE_NAME     = "Back"
        SERVICEBUS_STATUS_SUB = ""
        SERVICEBUS_ORDERS_SUB = local.data.servicebus_back_orders_sub
        DB_CONTAINER          = local.data.db_processing_container
        AUTH_PUBLIC_URL       = local.back_service_url
      }
    }
  }
}

