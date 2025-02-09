# ---------------------------------------------------------------------------- #
# setup

terraform {
  required_providers {
    scaleway = {
      source = "scaleway/scaleway"
    }
  }
  required_version = ">= 0.13"
  backend "s3" {
    bucket                      = var.state_bucket_name
    key                         = "ytarchive_v2.tfstate"
    region                      = "pl-waw"
    endpoint                    = "https://s3.pl-waw.scw.cloud"
    access_key                  = var.state_access_key
    secret_key                  = var.state_secret_key
    skip_credentials_validation = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
  }
}

provider "scaleway" {
  access_key      = var.scaleway_access_key
  secret_key      = var.scaleway_secret_key
  organization_id = var.scaleway_organization_id
  project_id      = var.scaleway_project_id
  region          = "nl-ams"
}

# ---------------------------------------------------------------------------- #
# grafana

resource "scaleway_cockpit_grafana_user" "main" {
  login = "main"
  role  = "editor"
}

# ---------------------------------------------------------------------------- #