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

variable "hostnameSuffix" {
  default  = ""
  type     = string
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

variable "localDev" {
  default  = false
  type     = bool
}

variable "deployApps" {
  default  = true
  type     = bool
}

