output "servicebus" {
  value = {
    hostname = "${azurerm_servicebus_namespace.app_ns.name}.servicebus.windows.net"
    topics = {
      orders = azurerm_servicebus_topic.orders_topic.name
      status = azurerm_servicebus_topic.status_topic.name
    }
    sub = {
      front_status = azurerm_servicebus_subscription.front_status_sub.name
      back_orders  = azurerm_servicebus_subscription.back_orders_sub.name
    }
  }
}

output "cosmosdb" {
  value = {
    endpoint = azurerm_cosmosdb_account.db_account.endpoint
    name     = azurerm_cosmosdb_sql_database.app_db.name
    containers = {
      orders     = azurerm_cosmosdb_sql_container.orders.name
      processing = azurerm_cosmosdb_sql_container.processing.name
    }
  }
}

output "storage" {
  value = {
    endpoint  = azurerm_storage_account.stor.primary_blob_endpoint
    container = azurerm_storage_container.stor_container.name
  }
}

output "appinsights" {
  value = {
    connection_string = azurerm_application_insights.appinsights.connection_string
  }
  sensitive = true
}

output "web_pubsub" {
  value = {
    endpoint  = "https://${azurerm_web_pubsub.pubsub.hostname}"
    front_hub = azurerm_web_pubsub_hub.front.name
  }
}

output "current_user" {
  value = {
    current_user_obj_id = data.azurerm_client_config.current.object_id
  }
}

output "keyvault" {
  value = {
    name       = azurerm_key_vault.secrets_vault.name
    key_prefix = "${var.name_prefix}-auth-"
  }
}

output "conapp_env" {
  value = {
    name    = azurerm_container_app_environment.conapp_env.name
    id      = azurerm_container_app_environment.conapp_env.id
    cert    = azurerm_container_app_environment_certificate.app_cert.name
    cert_id = azurerm_container_app_environment_certificate.app_cert.id
  }
}

output "conapp_identity" {
  value = {
    name = azurerm_user_assigned_identity.conapp.name
    id   = azurerm_user_assigned_identity.conapp.id
  }
}
