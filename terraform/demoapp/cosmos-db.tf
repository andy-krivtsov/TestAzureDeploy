resource "azurerm_cosmosdb_account" "db_account" {
  name                = "${var.containerappName}-db-${random_id.deploy_id.hex}"
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
  name                = "${var.containerappName}-db"
  resource_group_name = data.azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.db_account.name
}

resource "azurerm_cosmosdb_sql_container" "appDbContainer" {
  name                  = "demoapp-container"
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
