# DNS records for the application
resource "azurerm_dns_a_record" "dns-record" {
  name                = "${var.containerappName}${var.hostnameSuffix}"
  zone_name           = var.customDnsZone
  resource_group_name = var.customDnsZoneRG
  ttl                 = 60
  records             = [var.containerappEnvIpAddress]
}

resource "azurerm_dns_txt_record" "dns-record" {
  name                = "asuid.${var.containerappName}${var.hostnameSuffix}"
  zone_name           = var.customDnsZone
  resource_group_name = var.customDnsZoneRG
  ttl                 = 60

  record {
    value = var.customDomainVerificationId
  }
}

resource "time_sleep" "wait_dns" {
  depends_on = [
    azurerm_dns_a_record.dns-record,
    azurerm_dns_txt_record.dns-record
  ]

  create_duration = "10s"
}

