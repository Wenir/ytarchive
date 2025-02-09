# ---------------------------------------------------------------------------- #
# s3

resource "scaleway_object_bucket" "main"{
  name = "${var.glacier_vault_name}-main"
  region = "nl-ams"

  lifecycle_rule {
    id = "archive_id"
    enabled = true

    tags = {
      "archive" = "true"
    }

    transition {
      days = 1
      storage_class = "GLACIER"
    }
  }

  lifecycle_rule {
    enabled = true
    abort_incomplete_multipart_upload_days = 30
  }
}

# ---------------------------------------------------------------------------- #
# job user

resource "scaleway_iam_application" "job" {
  name = "job"
}

resource "scaleway_iam_api_key" "job_key" {
  application_id = scaleway_iam_application.job.id
  default_project_id = var.scaleway_project_id
  #description = "a description"
}

resource scaleway_iam_policy "s3_access" {
  name = "s3_access"
  description = "gives app access to object storage in project"
  application_id = scaleway_iam_application.job.id
  rule {
    project_ids = [ var.scaleway_project_id ]
    permission_set_names = [ "ObjectStorageFullAccess" ]
  }
}

# ---------------------------------------------------------------------------- #
# jobs

resource "scaleway_job_definition" playlist-app {
  name = "playlist-app"
  cpu_limit = 140
  memory_limit = 512
  image_uri = "${scaleway_registry_namespace.main.endpoint}/playlist-app:latest"
  timeout = "10m"

  env = {
    foo: "bar"
  }

  cron {
    schedule = "0 0 * * *"
    timezone = "UTC"
  }
}

resource "scaleway_job_definition" download-app {
  name = "download-app"
  cpu_limit = 140
  memory_limit = 512
  image_uri = "${scaleway_registry_namespace.main.endpoint}/download-app:latest"
  timeout = "10m"

  env = {
    foo: "bar"
  }

  cron {
    schedule = "1 1 * * *"
    timezone = "UTC"
  }
}

resource "scaleway_secret" "job_environment" {
  name        = "job_environment"
  description = "barr"
}

resource "scaleway_secret_version" "v1" {
  description = "version"
  secret_id   = scaleway_secret.job_environment.id
  data        = <<-EOT
    ACCESS_KEY="${scaleway_iam_api_key.job_key.access_key}"
    SECRET_KEY="${scaleway_iam_api_key.job_key.secret_key}"
    BUCKET_ENDPOINT="${scaleway_object_bucket.main.endpoint}"
    BUCKET_NAME="${scaleway_object_bucket.main.name}"
    REGION="${scaleway_object_bucket.main.region}"
    API_ENDPOINT="${scaleway_object_bucket.main.api_endpoint}"
    DATA_KEY="${var.data_key}"
    DATA_IV="${var.data_iv}"
    SRC_PLAYLIST="${var.src_playlist}"
    EOT
}

# ---------------------------------------------------------------------------- #

output "job-environment" {
  value = scaleway_secret_version.v1.data
  sensitive = true
}