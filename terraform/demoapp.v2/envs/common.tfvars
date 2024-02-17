name_suffix           = ""
resource_group        = ""
revision_suffix       = ""

custom_dns_zone_rg    = "AzureLearn"
custom_domain         = "az.mechlab.net"
hostname_suffix       = ""

app_display_name      = "Azure Demo App"
app_description       = "Azure demo application registration (created by Terraform)"

app_image             = "learn/demoapp"

front_service_name    = "front"
back_service_name     = "back"

pubsub_handler_path   = "/notifications/events"
logout_path           = "/logout"
redirect_path         = "/token"

front_local_url       = "http://localhost:8000"