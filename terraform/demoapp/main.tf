terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">=3.80.0"
    }
  }

  backend "azurerm" {}
}

provider "azurerm" {
  skip_provider_registration = true
  features {}
}

locals {
  fullImageName = "${var.registryName}/${var.containerImage}:${var.containerTag}"
}

resource "random_id" "deploy_id" {
  keepers     = {
    rg_name = var.resourceGroupName
  }
  byte_length = 4
}

data "azurerm_resource_group" "rg" {
  name = var.resourceGroupName
}

data "azurerm_user_assigned_identity" "appIdentity" {
  name                = var.identityName
  resource_group_name = data.azurerm_resource_group.rg.name
}

resource "azurerm_storage_account" "stor" {
  name                     = "${var.storageAccountPrefix}${random_id.deploy_id.hex}"
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = data.azurerm_resource_group.rg.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = "LRS"
  access_tier              = "Hot"
}

resource "azurerm_storage_share" "stor_share" {
  name                 = "containerapps"
  storage_account_name = azurerm_storage_account.stor.name
  quota                = 10
}

resource "azurerm_log_analytics_workspace" "logs" {
  name                = "${var.logWorkspacePrefix}${random_id.deploy_id.hex}"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = data.azurerm_resource_group.rg.location
  sku                 = "PerGB2018"
  retention_in_days   = 15
}

resource "azurerm_container_app_environment" "conapp_env" {
  name                       = var.environmentName
  resource_group_name        = data.azurerm_resource_group.rg.name
  location                   = data.azurerm_resource_group.rg.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
}

resource "azurerm_container_app_environment_storage" "conapp_env_stor" {
  name                         = "azurefiles"
  container_app_environment_id = azurerm_container_app_environment.conapp_env.id
  account_name                 = azurerm_storage_account.stor.name
  share_name                   = azurerm_storage_share.stor_share.name
  access_key                   = azurerm_storage_account.stor.primary_access_key
  access_mode                  = "ReadWrite"
}

resource "azurerm_container_app" "conapp" {
  name                         = var.containerappName
  container_app_environment_id = azurerm_container_app_environment.conapp_env.id
  resource_group_name          = data.azurerm_resource_group.rg.name
  revision_mode                = "Single"

  identity {
    type  = "UserAssigned"
    identity_ids = [
      data.azurerm_user_assigned_identity.appIdentity.id
    ]
  }

  ingress {
    external_enabled = true
    target_port = 8000
    allow_insecure_connections = false
    transport = "auto"
    traffic_weight {
      latest_revision = true
      percentage = 100
    }
  }

  registry {
    server = var.registryName
    identity = data.azurerm_user_assigned_identity.appIdentity.id
  }

  template {
    revision_suffix = var.revisionSuffix
    min_replicas = 0
    max_replicas = 1
    container {
      name   = var.containerappName
      image  = local.fullImageName
      cpu    = 0.25
      memory = "0.5Gi"
      liveness_probe {
        transport = "HTTP"
        path = "/"
        port = 8000
        initial_delay = 10
        interval_seconds = 3
      }
    }
  }
}
