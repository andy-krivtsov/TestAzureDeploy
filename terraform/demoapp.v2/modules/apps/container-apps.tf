module "app_dns_records" {
  source   = "./modules/dns_app_record"
  for_each = var.app_list

  app_hostname           = "${each.key}${var.hostname_suffix}"
  app_ip_address         = data.azurerm_container_app_environment.app_env.static_ip_address
  domain_verification_id = local.domain_verification_id
  custom_dns_zone        = var.custom_domain
  custom_dns_zone_rg     = var.custom_dns_zone_rg
}

module "container_app" {
  source     = "./modules/container-app"
  for_each   = module.app_dns_records

  app_name = each.key

  con_app_env_id           = data.azurerm_container_app_environment.app_env.id
  con_app_env_rg           = var.con_app_env_rg
  con_app_user_identity_id = data.azurerm_user_assigned_identity.con_app.id
  con_app_env_cert_id      = data.azurerm_container_app_environment_certificate.app_env_cert.id

  app_hostname  = "${each.key}${var.hostname_suffix}"
  custom_domain = var.custom_domain

  registry_server = data.azurerm_container_registry.app_registry.login_server

  revision_suffix = var.revision_suffix != "" ? var.revision_suffix : random_id.random_suffix.hex
  full_image_name = local.full_image_name
  container_args  = each.value["args"]
  secrets         = local.app_secrets
  envs_secrets    = { for k, v in local.app_secrets : upper(replace(k, "-", "_")) => k }
  envs            = merge(var.app_global_env, each.value["envs"])
}

