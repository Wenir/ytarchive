# ---------------------------------------------------------------------------- #
# app

variable "glacier_vault_name" {
  type     = string
  nullable = false
}

variable "data_key" {
  type     = string
  nullable = false
}

variable "data_iv" {
  type     = string
  nullable = false
}

variable "src_playlist" {
  type     = string
  nullable = false
}

variable "tg_bot_token" {
  type     = string
  nullable = false
}

variable "tg_chat_id" {
  type     = string
  nullable = false
}

# ---------------------------------------------------------------------------- #
# state

variable "state_access_key" {
  type     = string
  nullable = false
}

variable "state_secret_key" {
  type     = string
  nullable = false
}

variable "state_bucket_name" {
  type     = string
  nullable = false
}

# ---------------------------------------------------------------------------- #
# scaleway

variable "scaleway_access_key" {
  type     = string
  nullable = false
}

variable "scaleway_secret_key" {
  type     = string
  nullable = false
}

variable "scaleway_organization_id" {
  type     = string
  nullable = false
}

variable "scaleway_project_id" {
  type     = string
  nullable = false
}
