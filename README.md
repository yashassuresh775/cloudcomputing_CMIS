# CMIS Engagement Platform

Monorepo for the CMIS Engagement Platform (ISTM 665). This folder contains **Section 3: Team Gig 'Em — External Core**.

## Section 3: External Core (Team Gig 'Em)

Implements:

- **External Auth:** Email/password login via AWS Cognito User Pool.

- **Role Logic Engine:** On registration, assigns PARTNER (email domain in Company List), FORMER_STUDENT (former student box + class year), or FRIEND.
- **Graduation Handover:** Flow to link a new external account to an old Student UIN and set role to FORMER_STUDENT.

### Stack

- **Infrastructure:** Terraform (Cognito, DynamoDB, Lambda, API Gateway HTTP API)
- **Backend:** Python 3.12 Lambda (`/services/external-service`)
- **Frontend:** Svelte + Vite (`/frontend`), themed with CSS variables

### Quick start

1. **Infrastructure (Terraform)**

   ```bash
   cd infrastructure
   terraform init
   terraform plan
   terraform apply
   ```

   Then set `VITE_API_BASE` in `frontend/.env` to the API Gateway URL from `terraform output api_gateway_url`.

2. **Frontend (local dev)**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   For local API testing without Terraform, use a local Lambda (e.g. SAM or a small Flask/FastAPI proxy) or point `VITE_API_BASE` at a deployed API.

3. **Company List (Team Howdy)**

   Role logic expects an optional Company List API. If `COMPANY_LIST_API_URL` is not set, the Lambda uses a stub list (`acme.com`, `partner.org`, `example.com`). Set the env var in Terraform (`variables.tf` / `terraform.tfvars`) when Howdy's API is available.

### API (External Service)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/signup` | Register (body: `email`, `password`, `formerStudent`, `classYear`) |
| POST | `/auth/signin` | Sign in (body: `email`, `password`) |
| GET | `/me` | Current user (header: `Authorization: Bearer <accessToken>`) |
| POST | `/graduation-handover` | Link UIN (auth required; body: `uin`, optional `classYear`) |

### Repo structure (per project spec)

```
/frontend          — Shared Svelte app
/services/external-service  — Team Gig 'Em (this section)
/infrastructure    — Terraform (shared + external resources)
```
