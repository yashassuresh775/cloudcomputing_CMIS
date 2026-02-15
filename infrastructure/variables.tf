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

variable "frontend_base_url" {
  description = "Frontend base URL for magic-link claim (e.g. https://app.example.com or http://localhost:5173)"
  type        = string
  default     = "http://localhost:5173"
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
