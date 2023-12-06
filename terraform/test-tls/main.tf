terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">=3.80.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = ">=4.0.5"
    }
    external = {
      source  = "hashicorp/external"
      version = ">=2.3.2"
    }
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

data "azurerm_key_vault_certificate_data" "keyVaultAppCert" {
  name         = var.certKeyVaultKey
  key_vault_id = data.azurerm_key_vault.certVault.id
}

data "azurerm_key_vault_certificate" "appCert" {
  name         = var.certKeyVaultKey
  key_vault_id = data.azurerm_key_vault.certVault.id
}

data "azurerm_key_vault_secret" "certSecret" {
  name         = element(reverse(split("/",data.azurerm_key_vault_certificate.appCert.secret_id)),1)
  key_vault_id = data.azurerm_key_vault.certVault.id
}


data "azurerm_resource_group" "rg" {
  name = var.resourceGroupName
}

data "azurerm_user_assigned_identity" "appIdentity" {
  name                = var.identityName
  resource_group_name = data.azurerm_resource_group.rg.name
}

data "tls_certificate" "appCert" {
  content = "${data.azurerm_key_vault_certificate_data.keyVaultAppCert.pem}\n${data.azurerm_key_vault_certificate_data.keyVaultAppCert.key}"
}

data "external" "appCertPem" {
  program = ["bash", "${path.module}/process-cert.sh"]

  query = {
    certBase64 = data.azurerm_key_vault_certificate.appCert.certificate_data_base64
  }
}

output "count" {
  value = length(data.tls_certificate.appCert.certificates)
}

output "cert01" {
  value = data.tls_certificate.appCert.certificates[0]
}

output "sourceData" {
  value = "${data.azurerm_key_vault_certificate_data.keyVaultAppCert.pem}\n${data.azurerm_key_vault_certificate_data.keyVaultAppCert.key}"
  sensitive = true
}

output "certificatePem" {
  value =  data.external.appCertPem.result.certPem
}

output "certFromSecret" {
  value =  data.azurerm_key_vault_secret.certSecret.value
  sensitive = true
}
