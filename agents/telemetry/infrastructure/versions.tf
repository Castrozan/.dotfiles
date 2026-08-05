terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  backend "gcs" {
    bucket = "zg-url-shortener-2026-terraform-state"
    prefix = "dotfiles-usage-dashboard"
  }
}
