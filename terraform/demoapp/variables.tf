variable "namePrefix" {
  default  = "demoapp"
  nullable = false
  type     = string
}

variable "azureadAppRegistration" {
  type = object({
    displayName = string,
    description = string,
    homepageUrl = string,
    logoutUrl = string,
    redirectUris = list(string)
  })
  default = {
    displayName = "Azure Demo App"
    description = "Azure demo application registration (created by Terraform)"
    homepageUrl = "https://front.az.mechlab.net"
    logoutUrl   = "https://front.az.mechlab.net/logout"
    redirectUris = [
      "https://front.az.mechlab.net/token",
      "http://localhost:8000/token"
    ]
  }
}


variable "resourceGroupName" {
  default  = "AzureLearn"
  nullable = false
  type     = string
}

variable "registry" {
  default  = "akazureregistry"
  type     = string
}

variable "registryRG" {
  default  = "AzureLearn"
  type     = string
}

variable "containerImage" {
  default  = "learn/demoapp"
  nullable = false
  type     = string
}

variable "containerTag" {
  default  = "dev"
  nullable = false
  type     = string
}

variable "revisionSuffix" {
  default = ""
  type    = string
}

variable "customDnsZone" {
  default  = "az.mechlab.net"
  nullable = false
  type     = string
}

variable "customDnsZoneRG" {
  default  = "AzureLearn"
  nullable = false
  type     = string
}

variable "certKeyVaultName" {
  default  = "ak-certs-vault"
  nullable = false
  type     = string
}

variable "certKeyVaultRG" {
  default  = "ssl-certs"
  nullable = false
  type     = string
}

variable "certKeyVaultKey" {
  default  = "wildcard-az-mechlab-net"
  nullable = false
  type     = string
}

variable "secretsKeyVaultName" {
  default = "ak-learn-vault"
  type    = string
}

variable "secretsKeyVaultRG" {
  default = "AzureLearn"
  type    = string
}

variable "appKeyvaultSecrets" {
  type = map(string)
  default = {
    auth-client-id     = "demoapp-client-id"
    auth-client-secret = "demoapp-client-secret"
    auth-tenant-id     = "demoapp-tenant-id"
    auth-session-key   = "demoapp-session-key"
  }
}
