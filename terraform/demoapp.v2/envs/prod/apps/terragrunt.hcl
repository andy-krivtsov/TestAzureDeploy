terraform {
  source = "../../../modules/apps"
}

include "root" {
  path = find_in_parent_folders()
}

dependency "infra" {
  config_path = "../infra"

  mock_outputs = {
    servicebus = ""
    cosmosdb = ""
    storage = ""
    appinsights = ""
    web_pubsub = ""
    conapp_env = {
      name    = "testenv"
      cert    = "testcert"
    }
    conapp_identity = {
      name    = "testid"
    }
    keyvault = {
      key_prefix = "demo-"
    }
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
  cmn     = include.env.locals
  deploy  = jsondecode(file(find_in_parent_folders("deploy-vars.json")))
}

inputs = {
  app_tag               = local.deploy.app_tag
  con_app_env           = dependency.infra.outputs.conapp_env.name
  con_app_env_rg        = local.cmn.resource_group
  con_app_env_cert      = dependency.infra.outputs.conapp_env.cert
  con_app_user_identity = dependency.infra.outputs.conapp_identity.name
  hostname_suffix       = local.cmn.hostname_suffix
  custom_domain         = local.cmn.custom_domain
  custom_dns_zone_rg    = local.cmn.shared_resource_group
  revision_suffix       = local.cmn.revision_suffix
  app_image             = local.cmn.app_image
  acr_registry          = local.cmn.acr_registry
  acr_registry_rg       = local.cmn.shared_resource_group
  keyvault_prefix       = dependency.infra.outputs.keyvault.key_prefix
  keyvault              = dependency.infra.outputs.keyvault.name
  keyvault_rg           = local.cmn.resource_group

  app_global_env        = {
    SERVICEBUS_NAMESPACE                 = dependency.infra.outputs.servicebus.hostname
    SERVICEBUS_ORDERS_TOPIC              = dependency.infra.outputs.servicebus.topics.orders
    SERVICEBUS_STATUS_TOPIC              = dependency.infra.outputs.servicebus.topics.status
    DB_URL                               = dependency.infra.outputs.cosmosdb.endpoint
    DB_DATABASE                          = dependency.infra.outputs.cosmosdb.name
    STORAGE_URL                          = dependency.infra.outputs.storage.endpoint
    STORAGE_CONTAINER                    = dependency.infra.outputs.storage.container
    APP_INSIGHTS_CONSTR                  = dependency.infra.outputs.appinsights.connection_string
    WEB_PUBSUB_ENDPOINT                  = dependency.infra.outputs.web_pubsub.endpoint
    OTEL_RESOURCE_ATTRIBUTES             = "service.namespace=demoapp"
    OTEL_TRACES_SAMPLER_ARG              = 1
    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS = "azure_app_service"
    OTEL_PYTHON_EXCLUDED_URLS            = "/health/*"
  }

  # Can be overrited in CLI with -var 'app_list={}' parameter to deploy without applications themselves
  app_list              = {
    "front" = {
      args = ["--host", "0.0.0.0", "demoapp.orders_front:app"]
      envs = {
        OTEL_SERVICE_NAME     = "Front"
        SERVICEBUS_STATUS_SUB = dependency.infra.outputs.servicebus.sub.front_status
        SERVICEBUS_ORDERS_SUB = ""
        DB_CONTAINER          = dependency.infra.outputs.cosmosdb.containers.orders
        AUTH_PUBLIC_URL       = local.cmn.front_service_url
        WEB_PUBSUB_HUB        = dependency.infra.outputs.web_pubsub.front_hub
      }
    }

    "back" = {
      args = ["--host", "0.0.0.0", "demoapp.orders_back:app"]
      envs = {
        OTEL_SERVICE_NAME     = "Back"
        SERVICEBUS_STATUS_SUB = ""
        SERVICEBUS_ORDERS_SUB = dependency.infra.outputs.servicebus.sub.back_orders
        DB_CONTAINER          = dependency.infra.outputs.cosmosdb.containers.processing
        AUTH_PUBLIC_URL       = local.cmn.back_service_url
      }
    }
  }
}

