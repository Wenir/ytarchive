# ---------------------------------------------------------------------------- #
# job user

resource "scaleway_iam_application" "job" {
  name = "job"
}

resource "scaleway_iam_api_key" "job_key" {
  application_id     = scaleway_iam_application.job.id
  default_project_id = var.scaleway_project_id
  #description = "a description"
}

# ---------------------------------------------------------------------------- #
# jobs

resource "scaleway_job_definition" "playlist-app" {
  name         = "playlist-app"
  cpu_limit    = 140
  memory_limit = 512
  image_uri    = "${scaleway_registry_namespace.main.endpoint}/playlist-app:latest"
  timeout      = "10m"
  region       = "nl-ams"

  secret_reference {
    secret_id = scaleway_secret.job_environment.id
    file      = "/.env"
  }

  cron {
    schedule = "0 0 * * *"
    timezone = "UTC"
  }
}

resource "scaleway_job_definition" "download-app" {
  name         = "download-app"
  cpu_limit    = 560
  memory_limit = 512
  image_uri    = "${scaleway_registry_namespace.main.endpoint}/download-app:latest"
  timeout      = "10m"
  region       = "nl-ams"

  secret_reference {
    secret_id = scaleway_secret.job_environment.id
    file      = "/.env"
  }

  cron {
    schedule = "1 1 * * *"
    timezone = "UTC"
  }
}

# ---------------------------------------------------------------------------- #
# secret

resource "scaleway_secret" "job_environment" {
  name        = "job_environment"
  description = "barr"
  region      = "nl-ams"
}

resource "scaleway_secret_version" "v1" {
  region      = "nl-ams"
  description = "version"
  secret_id   = scaleway_secret.job_environment.id
  data        = <<-EOT
    ACCESS_KEY="${scaleway_iam_api_key.job_key.access_key}"
    SECRET_KEY="${scaleway_iam_api_key.job_key.secret_key}"
    BUCKET_ENDPOINT="${scaleway_object_bucket.main.endpoint}"
    BUCKET_NAME="${scaleway_object_bucket.main.name}"
    TESTS_BUCKET_NAME="${scaleway_object_bucket.tests.name}"
    REGION="${scaleway_object_bucket.main.region}"
    API_ENDPOINT="${scaleway_object_bucket.main.api_endpoint}"
    DB_ACCESS="${local.database_connection_string}"
    TESTS_DB_ACCESS="${local.tests_database_connection_string}"
    DATA_KEY="${var.data_key}"
    DATA_IV="${var.data_iv}"
    SRC_PLAYLIST="${var.src_playlist}"
    TG_BOT_TOKEN="${var.tg_bot_token}"
    TG_CHAT_ID="${var.tg_chat_id}"
    EOT
}

# ---------------------------------------------------------------------------- #

output "job-environment" {
  value     = scaleway_secret_version.v1.data
  sensitive = true
}