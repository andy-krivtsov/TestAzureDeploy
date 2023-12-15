
# UserContainer Apps

locals {
  app_secrets = {
    auth-client-id     = data.azurerm_key_vault_secret.vaultSecrets["auth-client-id"].value
    auth-client-secret = data.azurerm_key_vault_secret.vaultSecrets["auth-client-secret"].value
    auth-tenant-id     = data.azurerm_key_vault_secret.vaultSecrets["auth-tenant-id"].value
    auth-session-key   = data.azurerm_key_vault_secret.vaultSecrets["auth-session-key"].value
  }

  app_env_secrets = {
    AUTH_CLIENT_ID     = "auth_client_id"
    AUTH_CLIENT_SECRET = "auth_client_secret"
    AUTH_TENANT_ID     = "auth_tenant_id"
    AUTH_SESSION_KEY   = "auth_session_key"
  }

  app_env = {
    SERVICEBUS_NAMESPACE    = "${azurerm_servicebus_namespace.busNamespace.name}.servicebus.windows.net"
    SERVICEBUS_TOPIC        = azurerm_servicebus_topic.data_topic.name
    SERVICEBUS_STATUS_QUEUE = azurerm_servicebus_queue.status_queue.name
    DB_URL                  = azurerm_cosmosdb_account.db_account.endpoint
    DB_DATABASE             = azurerm_cosmosdb_sql_database.appDb.name
    DB_CONTAINER            = azurerm_cosmosdb_sql_container.appDbContainer.name
    STORAGE_URL             = azurerm_storage_account.stor.primary_blob_endpoint
    STORAGE_CONTAINER       = azurerm_storage_container.stor_container.name
  }

  app_list = {
    "front" = {
      args = [ "--host", "0.0.0.0", "demoapp.front:app" ]
      envs = { SERVICEBUS_SUBSCRIPTION = "" }
    }
    "backdb" = {
      args = [ "--host", "0.0.0.0", "demoapp.back_db:app" ]
      envs = { SERVICEBUS_SUBSCRIPTION = azurerm_servicebus_subscription.db_sub.name }
    }
    "backstor" = {
      args = [ "--host", "0.0.0.0", "demoapp.back_storage:app" ]
      envs = { SERVICEBUS_SUBSCRIPTION = azurerm_servicebus_subscription.stor_sub.name }
    }
  }
}

module "container_app" {
  source = "./modules/container-app"

  for_each = local.app_list

  containerappName = each.key

  containerappEnvId          = azurerm_container_app_environment.conapp_env.id
  resourceGroupName          = data.azurerm_resource_group.rg.name
  userAssignedIdentityId     = data.azurerm_user_assigned_identity.appIdentity.id
  customDnsZone              = var.customDnsZone
  customDnsZoneRG            = var.customDnsZoneRG
  envCertificateId           = azurerm_container_app_environment_certificate.appCert.id
  registryName               = var.registryName
  revisionSuffix             = var.revisionSuffix
  fullImageName              = local.fullImageName
  containerappEnvIpAddress   = azurerm_container_app_environment.conapp_env.static_ip_address
  customDomainVerificationId = jsondecode(data.azapi_resource.conapp_env_api.output).properties.customDomainConfiguration.customDomainVerificationId

  container_args = each.value["args"]

  secrets      = local.app_secrets
  envs_secrets = { for k, v in local.app_secrets : upper(replace(k,"-","_")) => k }
  envs         = merge(local.app_env, each.value["envs"])
}

