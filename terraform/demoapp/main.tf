terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">=3.80.0"
    }

    azapi = {
      source = "Azure/azapi"
      version = ">=1.10.0"
    }

    time = {
      source = "hashicorp/time"
      version = ">=0.9.2"
    }
  }

  backend "azurerm" {
    resource_group_name  = "Terraform"
    storage_account_name = "aktfstate"
    container_name       = "tfstate"
    key                  = "container-demoapp.tfstate"
  }
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

data "azurerm_key_vault" "certVault" {
  name                = var.certKeyVaultName
  resource_group_name = var.certKeyVaultRG
}

data "azurerm_key_vault_certificate" "keyVaultAppCert" {
  name         = var.certKeyVaultKey
  key_vault_id = data.azurerm_key_vault.certVault.id
}

data "azurerm_key_vault_secret" "appCertSecret" {
  name         = element(reverse(split("/",data.azurerm_key_vault_certificate.keyVaultAppCert.secret_id)),1)
  key_vault_id = data.azurerm_key_vault.certVault.id
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
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "conapp_env" {
  name                       = var.environmentName
  resource_group_name        = data.azurerm_resource_group.rg.name
  location                   = data.azurerm_resource_group.rg.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
}

resource "azurerm_container_app_environment_certificate" "appCert" {
  name                         = var.certKeyVaultKey
  container_app_environment_id = azurerm_container_app_environment.conapp_env.id
  certificate_blob_base64      = data.azurerm_key_vault_secret.appCertSecret.value
  certificate_password         = ""
}

resource "azurerm_container_app_environment_storage" "conapp_env_stor" {
  name                         = "azurefiles"
  container_app_environment_id = azurerm_container_app_environment.conapp_env.id
  account_name                 = azurerm_storage_account.stor.name
  share_name                   = azurerm_storage_share.stor_share.name
  access_key                   = azurerm_storage_account.stor.primary_access_key
  access_mode                  = "ReadWrite"
}

data "azapi_resource" "conapp_env_api" {
  resource_id = azurerm_container_app_environment.conapp_env.id
  type        = "Microsoft.App/managedEnvironments@2022-11-01-preview"

  response_export_values = ["properties.customDomainConfiguration.customDomainVerificationId"]
}

resource "azurerm_dns_a_record" "dns-record" {
  name = var.containerappName
  zone_name = var.customDnsZone
  resource_group_name = var.customDnsZoneRG
  ttl = 60
  records = [ azurerm_container_app_environment.conapp_env.static_ip_address ]
}

resource "azurerm_dns_txt_record" "dns-record" {
  name                = "asuid.${var.containerappName}"
  zone_name           = var.customDnsZone
  resource_group_name = var.customDnsZoneRG
  ttl                 = 60

  record {
    value = jsondecode(data.azapi_resource.conapp_env_api.output).properties.customDomainConfiguration.customDomainVerificationId
  }
}

resource "time_sleep" "wait_dns" {
  depends_on = [
    azurerm_dns_a_record.dns-record,
    azurerm_dns_txt_record.dns-record
  ]

  create_duration = "10s"
}


resource "azurerm_container_app" "conapp" {
  name                         = var.containerappName
  container_app_environment_id = azurerm_container_app_environment.conapp_env.id
  resource_group_name          = data.azurerm_resource_group.rg.name
  revision_mode                = "Single"

  depends_on = [
    time_sleep.wait_dns
  ]

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
    custom_domain {
        certificate_binding_type = "SniEnabled"
        certificate_id = azurerm_container_app_environment_certificate.appCert.id
        name = "${var.containerappName}.${var.customDnsZone}"
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

