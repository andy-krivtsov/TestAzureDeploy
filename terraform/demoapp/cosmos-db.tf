resource "azurerm_cosmosdb_account" "db_account" {
  name                = "${var.namePrefix}-db-${random_id.deploy_id.hex}"
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  enable_automatic_failover = true
  enable_free_tier          = false

  capabilities {
    name = "EnableServerless"
  }

  backup {
    type = "Continuous"
  }

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = data.azurerm_resource_group.rg.location
    failover_priority = 0
  }
}

resource "azurerm_cosmosdb_sql_database" "appDb" {
  name                = "app-db"
  resource_group_name = data.azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.db_account.name
}

resource "azurerm_cosmosdb_sql_container" "appDbContainer" {
  name                  = "app-container"
  resource_group_name   = data.azurerm_resource_group.rg.name
  account_name          = azurerm_cosmosdb_account.db_account.name
  database_name         = azurerm_cosmosdb_sql_database.appDb.name
  partition_key_path    = "/sessionId"
  partition_key_version = 1

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

data "azurerm_cosmosdb_sql_role_definition" "data_contibutor" {
  resource_group_name = data.azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.db_account.name
  role_definition_id  = "00000000-0000-0000-0000-000000000002"
}

resource "azurerm_role_assignment" "db_admin" {
  scope                = azurerm_cosmosdb_account.db_account.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.azuread_app.object_id
}

resource "azurerm_cosmosdb_sql_role_assignment" "db_data_admin" {
  resource_group_name = data.azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.db_account.name
  role_definition_id  = data.azurerm_cosmosdb_sql_role_definition.data_contibutor.id
  principal_id        = azuread_service_principal.azuread_app.object_id
  scope               = azurerm_cosmosdb_account.db_account.id
}
