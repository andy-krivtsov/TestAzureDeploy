locals {
    # Only dev env
    revision_suffix       = "xx01234"

    name_prefix           = "demoapp"

    hostname_suffix       = "-dev"
    custom_domain         = "az.mechlab.net"

    app_display_name      = "Azure Demo App Dev"
    app_description       = "Azure demo application registration Local Dev(created by Terraform)"

    resource_group        = "AzureLearnDev"

    shared_resource_group = "AzureLearn"
    acr_registry          = "akazureregistry"
    app_image             = "learn/demoapp"

    cert_keyvault         = "ak-certs-vault"
    cert_keyvault_rg      = "ssl-certs"
    cert_keyvault_key     = "wildcard-az-mechlab-net"

    front_service_url     = "https://front${local.hostname_suffix}.${local.custom_domain}"
    front_local_url       = "http://localhost:8000"

    back_service_url      = "https://back${local.hostname_suffix}.${local.custom_domain}"

    pubsub_handler_path   = "/notifications/events"
    logout_path           = "/logout"
    redirect_path         = "/token"
}