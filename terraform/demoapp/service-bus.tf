# Service bus
resource "azurerm_servicebus_namespace" "busNamespace" {
  name                = "${var.containerappName}-namespace"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  sku                 = "Standard"
}

resource "azurerm_servicebus_topic" "data_topic" {
  name                = "${var.containerappName}-data-topic"
  namespace_id        = azurerm_servicebus_namespace.busNamespace.id
  default_message_ttl = "PT8H"
}

resource "azurerm_servicebus_subscription" "db_sub" {
  name               =  "${var.containerappName}-db-sub"
  topic_id           = azurerm_servicebus_topic.data_topic.id
  max_delivery_count = 1
}

resource "azurerm_servicebus_subscription" "stor_sub" {
  name               =  "${var.containerappName}-stor-sub"
  topic_id           = azurerm_servicebus_topic.data_topic.id
  max_delivery_count = 1
}

resource "azurerm_servicebus_queue" "status_queue" {
  name                = "${var.containerappName}-queue-status"
  namespace_id        = azurerm_servicebus_namespace.busNamespace.id
  default_message_ttl = "PT8H"
}

resource "azurerm_role_assignment" "topic_admin" {
  scope                = azurerm_servicebus_topic.data_topic.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = data.azuread_service_principal.appServicePrincipal.object_id
}

resource "azurerm_role_assignment" "db_sub_admin" {
  scope                = azurerm_servicebus_subscription.db_sub.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = data.azuread_service_principal.appServicePrincipal.object_id
}

resource "azurerm_role_assignment" "stor_sub_admin" {
  scope                = azurerm_servicebus_subscription.stor_sub.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = data.azuread_service_principal.appServicePrincipal.object_id
}

resource "azurerm_role_assignment" "status_queue_admin" {
  scope                = azurerm_servicebus_queue.status_queue.id
  role_definition_name = "Azure Service Bus Data Owner"
  principal_id         = data.azuread_service_principal.appServicePrincipal.object_id
}
