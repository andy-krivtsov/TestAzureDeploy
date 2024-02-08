# DNS records for the application
resource "azurerm_dns_a_record" "dns-record" {
  name                = var.app_hostname
  zone_name           = var.custom_domain
  resource_group_name = var.custom_dns_zone_rg
  ttl                 = 60
  records             = [var.con_app_ip_address]
}

resource "azurerm_dns_txt_record" "dns-record" {
  name                = "asuid.${var.app_hostname}"
  zone_name           = var.custom_domain
  resource_group_name = var.custom_dns_zone_rg
  ttl                 = 60

  record {
    value = var.domain_verification_id
  }
}

resource "time_sleep" "wait_dns" {
  depends_on = [
    azurerm_dns_a_record.dns-record,
    azurerm_dns_txt_record.dns-record
  ]

  create_duration = "10s"
}

