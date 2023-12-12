# DNS records for the application
resource "azurerm_dns_a_record" "dns-record" {
  name                = var.containerappName
  zone_name           = var.customDnsZone
  resource_group_name = var.customDnsZoneRG
  ttl                 = 60
  records             = [azurerm_container_app_environment.conapp_env.static_ip_address]
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

