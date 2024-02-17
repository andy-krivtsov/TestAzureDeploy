acr_registry_rg       = "AzureLearn"
acr_registry          = "akazureregistry"

cert_keyvault_rg      = "ssl-certs"
cert_keyvault         = "ak-certs-vault"
cert_keyvault_key     = "wildcard-az-mechlab-net"

con_app_env           = "demoapp-env"
con_app_env_cert      = "wildcard-az-mechlab-net"
con_app_env_identity  = "demoapp-identity"
con_app_env_log       = "demoapp-log"

keyvault              = "demoapp-vault"
keyvault_prefix       = "demoapp-"

servicebus_namespace        = "demoapp-namespace"
servicebus_orders_topic     = "orders"
servicebus_status_topic     = "status"
servicebus_front_status_sub = "front-status"
servicebus_back_orders_sub  = "back-orders"

db_account              = "demoapp-db"
db_database             = "app-db"
db_orders_container     = "orders"
db_processing_container = "processing"

app_insight           = "demoapp-appinsights"

web_pubsub            = "demoapp-pubsub"
web_pubsub_front_hub  = "front"

storage_account       = "demoappstor"
storage_container     = "appdata"