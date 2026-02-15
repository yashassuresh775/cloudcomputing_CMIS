# CMIS Engagement Platform

Monorepo for the CMIS Engagement Platform (ISTM 665). This folder contains **Section 3: Team Gig 'Em — External Core**.

## Section 3: External Core (Team Gig 'Em)

Implements:

- **External Auth:** Email/password login via AWS Cognito User Pool.

- **Role Logic Engine:** On registration, assigns PARTNER (email domain in Company List), FORMER_STUDENT (former student box + class year), or FRIEND.
- **Graduation Handover:** Flow to link a new external account to an old Student UIN, transferring history and changing primary role to FORMER_STUDENT.

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
| POST | `/graduation-handover` | Link external account to Student UIN, transfer history, set role to FORMER_STUDENT (auth required; body: `uin`, optional `classYear`) |
| GET | `/graduation-handover/claim?token=...` | Validate magic-link token; returns `email`, `uin`, `classYear` |
| POST | `/graduation-handover/claim` | Complete claim with `token` and `password` (creates account, links UIN) |

### Graduation handover automation

An EventBridge rule runs monthly (1st at 08:00 UTC) to:

1. Scan the **students** DynamoDB table for `account_status = STUDENT` and `grad_date <= today`
2. Generate time-limited magic-link tokens (7-day TTL)
3. Deliver magic links via **SES email** (if configured) or log to CloudWatch (dev)

#### Email notifications (SES)

To send magic links by email:

1. **Verify a sender in SES**
   - AWS Console → **SES** → **Verified identities** → **Create identity**
   - Choose **Email address** and enter an address you control (e.g. `noreply@yourdomain.com` or your Gmail)
   - Confirm via the verification email

2. **Apply Terraform with the sender**
   ```bash
   terraform apply -var="ses_verified_sender=your-verified@email.com"
   ```
   Or add to `terraform.tfvars`:
   ```hcl
   ses_verified_sender = "your-verified@email.com"
   ```

3. **SES sandbox**  
   In sandbox mode, SES can only send to verified addresses. Either:
   - Verify recipient emails in SES (Verified identities → Create → Email address), or
   - Use your verified email as `personal_email` in the students table so you receive the magic link

#### Testing with dummy data

```bash
# After terraform apply, seed students (includes test record for yashassuresh775@gmail.com)
./scripts/seed-students.sh

# Trigger scan manually (simulates EventBridge)
aws lambda invoke --function-name cmis-external-external-service \
  --cli-binary-format raw-in-base64-out \
  --payload '{"source":"aws.events","detail-type":"Scheduled Event"}' out.json && cat out.json
```

- **With SES:** Check the recipient inbox for the magic link.
- **Without SES:** Magic links are logged in CloudWatch (`/aws/lambda/cmis-external-external-service`). Copy the URL and open in the browser (e.g. `http://localhost:5173/#claim?token=...`).

#### Automated tests

```bash
./scripts/test-graduation.sh
```

Optional: set `CLAIM_TOKEN` to test the valid-token flow (get token from CloudWatch logs).

### Repo structure (per project spec)

```
/frontend          — Shared Svelte app
/services/external-service  — Team Gig 'Em (this section)
/infrastructure    — Terraform (shared + external resources)
```
