locals {
    revision_suffix       = ""

    name_prefix           = "demoapp"

    hostname_suffix       = ""
    custom_domain         = "az.mechlab.net"

    app_display_name      = "Azure Demo App"
    app_description       = "Azure demo application registration (created by Terraform)"

    resource_group        = "AzureLearn"

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