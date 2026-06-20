variable "project_id" {
  type    = string
  default = "zg-url-shortener-2026"
}

variable "project_number" {
  type    = string
  default = "933601426694"
}

variable "region" {
  type    = string
  default = "southamerica-east1"
}

variable "github_repository" {
  type    = string
  default = "Castrozan/.dotfiles"
}

variable "lucaszanoni_web_github_repository" {
  type    = string
  default = "Castrozan/lucaszanoni-web"
}

variable "usage_dashboard_image" {
  type    = string
  default = "southamerica-east1-docker.pkg.dev/zg-url-shortener-2026/dotfiles-apps/usage-dashboard:latest"
}

variable "reports_image" {
  type    = string
  default = "southamerica-east1-docker.pkg.dev/zg-url-shortener-2026/dotfiles-apps/reports:latest"
}
