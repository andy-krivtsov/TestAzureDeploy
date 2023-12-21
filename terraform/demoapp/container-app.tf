
# UserContainer Apps

locals {
  app_secrets = {
    auth-client-id     = azurerm_key_vault_secret.clientId.value
    auth-client-secret = azurerm_key_vault_secret.clientSecret.value
    auth-tenant-id     = azurerm_key_vault_secret.tenantId.value
    auth-session-key   = azurerm_key_vault_secret.sessionKey.value
  }

  app_env = {
    SERVICEBUS_NAMESPACE                 = "${azurerm_servicebus_namespace.busNamespace.name}.servicebus.windows.net"
    SERVICEBUS_TOPIC                     = azurerm_servicebus_topic.data_topic.name
    SERVICEBUS_STATUS_QUEUE              = azurerm_servicebus_queue.status_queue.name
    DB_URL                               = azurerm_cosmosdb_account.db_account.endpoint
    DB_DATABASE                          = azurerm_cosmosdb_sql_database.appDb.name
    DB_CONTAINER                         = azurerm_cosmosdb_sql_container.appDbContainer.name
    STORAGE_URL                          = azurerm_storage_account.stor.primary_blob_endpoint
    STORAGE_CONTAINER                    = azurerm_storage_container.stor_container.name
    APP_INSIGHTS_CONSTR                  = azurerm_application_insights.appinsights.connection_string
    OTEL_RESOURCE_ATTRIBUTES             = "service.namespace=demoapp"
    OTEL_TRACES_SAMPLER_ARG              = 1
    OTEL_EXPERIMENTAL_RESOURCE_DETECTORS = "azure_app_service"
    OTEL_PYTHON_EXCLUDED_URLS            = "/health/*"
  }

  app_list = {
    "front" = {
      args = ["--host", "0.0.0.0", "demoapp.front:app"]
      envs = {
        SERVICEBUS_SUBSCRIPTION = ""
        OTEL_SERVICE_NAME="Front"
        AUTH_PUBLIC_URL="https://front${var.hostnameSuffix}.${var.customDnsZone}"
      }
    }
    "backdb" = {
      args = ["--host", "0.0.0.0", "demoapp.back_db:app"]
      envs = {
        OTEL_SERVICE_NAME="BackDB"
        SERVICEBUS_SUBSCRIPTION = azurerm_servicebus_subscription.db_sub.name
      }
    }
    "backstor" = {
      args = ["--host", "0.0.0.0", "demoapp.back_storage:app"]
      envs = {
        OTEL_SERVICE_NAME="BackStorage"
        SERVICEBUS_SUBSCRIPTION = azurerm_servicebus_subscription.stor_sub.name
      }
    }
  }
}

module "container_app" {
  source = "./modules/container-app"

  for_each = var.deployApps ? local.app_list : {}

  containerappName = each.key

  containerappEnvId          = azurerm_container_app_environment.conapp_env.id
  resourceGroupName          = data.azurerm_resource_group.rg.name
  userAssignedIdentityId     = azurerm_user_assigned_identity.conapp.id
  customDnsZone              = var.customDnsZone
  customDnsZoneRG            = var.customDnsZoneRG
  hostnameSuffix             = var.hostnameSuffix
  envCertificateId           = azurerm_container_app_environment_certificate.appCert.id
  registryName               = data.azurerm_container_registry.appRegistry.login_server
  revisionSuffix             = var.revisionSuffix != "" ? var.revisionSuffix : random_id.random_suffix.hex
  fullImageName              = local.fullImageName
  containerappEnvIpAddress   = azurerm_container_app_environment.conapp_env.static_ip_address
  customDomainVerificationId = jsondecode(data.azapi_resource.conapp_env_api.output).properties.customDomainConfiguration.customDomainVerificationId

  container_args = each.value["args"]

  secrets      = local.app_secrets
  envs_secrets = { for k, v in local.app_secrets : upper(replace(k, "-", "_")) => k }
  envs         = merge(local.app_env, each.value["envs"])
}

