variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for resource names"
  type        = string
  default     = "cmis-external"
}

variable "company_list_api_url" {
  description = "Team Howdy Company List API base URL (optional; stub if not available)"
  type        = string
  default     = ""
}

variable "cors_allow_origins" {
  description = "CORS allowed origins for API (e.g. frontend URL)"
  type        = list(string)
  default     = ["*"]
}

variable "tags" {
  description = "Tags for all resources"
  type        = map(string)
  default     = {}
}
