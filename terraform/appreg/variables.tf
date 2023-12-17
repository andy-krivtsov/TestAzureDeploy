variable "azureadAppDisplayName" {
  default  = "testdemoapp"
  type     = string
}

variable "homepageUrl" {
  default  = "https://front.az.mechlab.net"
  type     = string
}

variable "logoutUrl" {
  default  = "https://front.az.mechlab.net/logout"
  type     = string
}

variable "redirectUris" {
  default  = ["https://front.az.mechlab.net/token", "http://localhost:8000/token"]
  type     = list(string)
}
