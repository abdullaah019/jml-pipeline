# JML Pipeline — Automated Identity Management

An automated **Joiner-Mover-Leaver (JML)** pipeline that reads live HR data from Google Sheets, detects employee changes, and automatically provisions or deprovisions Google Workspace accounts. Runs every night at midnight via GitHub Actions with zero manual intervention.

> 📸 **[Screenshot: GitHub Actions showing scheduled run]**

---

## What It Does

| Event | Trigger | Action |
|---|---|---|
| **Joiner** | New employee row in Google Sheet | Creates Google Workspace account, assigns to department group |
| **Mover** | Department or role change | Updates profile, moves to new department group |
| **Leaver** | Status set to `terminated` | Suspends account, removes group memberships, notifies manager |

---

## Architecture

```
Google Sheets (HR data)
        ↓
GitHub Actions (runs daily at midnight via cron)
        ↓
Python Detection Engine (compares current vs previous state)
        ↓
Handler (Joiner / Mover / Leaver)
        ↓
Google Apps Script Webhook
        ↓
Google Workspace Admin SDK (provisions/deprovisions users)
```

> 📸 **[Screenshot: Architecture diagram or pipeline logs showing end-to-end flow]**

---

## Project Structure

```
jml-pipeline/
├── .github/
│   └── workflows/
│       └── jml.yml          # GitHub Actions cron workflow
├── data/
│   └── employees.csv        # Local CSV (backup/dev use)
├── src/
│   ├── auth.py              # Google auth helper
│   ├── detector.py          # Change detection engine
│   ├── joiner.py            # New employee handler
│   ├── mover.py             # Role change handler
│   └── leaver.py            # Termination handler
├── state/
│   └── snapshot.json        # Previous run state (auto-updated)
├── main.py                  # Pipeline entry point
└── requirements.txt         # Python dependencies
```

---

## Prerequisites

- Python 3.11+
- Git + GitHub account
- Google Workspace account (admin access)
- Google Cloud Platform account
- Google Apps Script access

---

## Setup Guide

### Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/jml-pipeline.git
cd jml-pipeline
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
google-auth>=2.29.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.125.0
requests>=2.31.0
gspread>=6.0.0
```

---

### Step 3 — Set Up the Google Sheet

1. Go to [sheets.google.com](https://sheets.google.com) and create a new spreadsheet
2. Name it `JML Pipeline - HR Data`
3. Add these exact column headers in row 1:

```
employee_id | name | email | department | role | status | manager_email | start_date
```

4. Add your employee data starting from row 2. Example:

```
E001 | John Smith | john.smith@yourcompany.com | Engineering | Software Engineer | active | manager@yourcompany.com | 2024-01-15
E002 | Jane Doe | jane.doe@yourcompany.com | HR | HR Manager | active | ceo@yourcompany.com | 2023-06-01
```

5. Click **Share** → **Change to anyone with the link** → **Viewer** → **Done**

> 📸 **[Screenshot: Google Sheet with employee data]**

6. Copy your Sheet ID from the URL:
```
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit
```

---

### Step 4 — Create Google Workspace Groups

In [Google Workspace Admin](https://admin.google.com) → **Directory** → **Groups**, create a group for each department:

| Group Name | Email |
|---|---|
| Engineering | engineering@yourcompany.com |
| HR | hr@yourcompany.com |
| Sales | sales@yourcompany.com |
| Finance | finance@yourcompany.com |
| Marketing | marketing@yourcompany.com |
| Operations | operations@yourcompany.com |

For each group:
- **Labels:** Check both Mailing and Security
- **Access type:** Restricted
- **Who can join:** Only invited users

> 📸 **[Screenshot: Google Workspace Groups list]**

---

### Step 5 — Create the Google Apps Script Webhook

This script runs inside your Google Workspace and handles the actual user provisioning via the Admin SDK — no GCP credentials required.

1. Go to [script.google.com](https://script.google.com)
2. Click **New project** and name it `JML Webhook`
3. Replace the default code with:

```javascript
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var action = data.action;
    var employee = data.employee;
    
    if (action === "joiner") {
      createUser(employee);
    } else if (action === "mover") {
      updateUser(employee);
    } else if (action === "leaver") {
      suspendUser(employee);
    }
    
    return ContentService
      .createTextOutput(JSON.stringify({status: "success", action: action, email: employee.email}))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch(err) {
    return ContentService
      .createTextOutput(JSON.stringify({status: "error", message: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function createUser(employee) {
  var nameParts = employee.name.split(" ");
  AdminDirectory.Users.insert({
    primaryEmail: employee.email,
    name: {givenName: nameParts[0], familyName: nameParts[1] || ""},
    password: Math.random().toString(36).slice(-12),
    changePasswordAtNextLogin: true,
    orgUnitPath: "/" + employee.department
  });
  addToGroup(employee.email, employee.department);
}

function updateUser(employee) {
  AdminDirectory.Users.patch({
    orgUnitPath: "/" + employee.department,
    organizations: [{title: employee.role, department: employee.department, primary: true}]
  }, employee.email);
  addToGroup(employee.email, employee.department);
}

function suspendUser(employee) {
  AdminDirectory.Users.patch({suspended: true}, employee.email);
}

function addToGroup(email, department) {
  var groupEmail = department.toLowerCase() + "@yourcompany.com";
  try {
    AdminDirectory.Members.insert({email: email, role: "MEMBER"}, groupEmail);
  } catch(e) {
    Logger.log("Group add failed: " + e.toString());
  }
}
```

> ⚠️ Replace `yourcompany.com` with your actual domain throughout the script.

4. Click **Services** (left sidebar) → **+** → find **Admin SDK API** → **Add**
5. Click **Deploy** → **New deployment**
6. Set:
   - **Type:** Web app
   - **Execute as:** Me
   - **Who has access:** Anyone
7. Click **Deploy** → **Authorize access** → follow prompts
8. Copy the **Web app URL** — you'll need this as a GitHub secret

> 📸 **[Screenshot: Apps Script execution log showing doPost Completed]**

---

### Step 6 — Set Up GitHub Repository

1. Create a new public repository on GitHub named `jml-pipeline`
2. Push the project code:

```bash
git remote add origin https://github.com/YOUR_USERNAME/jml-pipeline.git
git branch -M main
git push -u origin main
```

---

### Step 7 — Add GitHub Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value |
|---|---|
| `GOOGLE_SHEET_ID` | Your Sheet ID from Step 3 |
| `APPS_SCRIPT_WEBHOOK_URL` | Your webhook URL from Step 5 |

> 📸 **[Screenshot: GitHub Actions secrets page (values hidden)]**

---

### Step 8 — GitHub Actions Workflow

The workflow file `.github/workflows/jml.yml` runs the pipeline automatically:

```yaml
name: JML Pipeline

on:
  schedule:
    - cron: "0 0 * * *"    # Runs every night at midnight UTC
  workflow_dispatch:         # Also allows manual triggering

jobs:
  run-pipeline:
    name: Run JML Pipeline
    runs-on: ubuntu-latest

    permissions:
      contents: write
      id-token: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Run JML pipeline
        run: python main.py
        env:
          GOOGLE_SHEET_ID: ${{ secrets.GOOGLE_SHEET_ID }}
          APPS_SCRIPT_WEBHOOK_URL: ${{ secrets.APPS_SCRIPT_WEBHOOK_URL }}

      - name: Commit updated snapshot
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add state/snapshot.json
          git diff --cached --quiet || git commit -m "chore: update snapshot [$(date -u +%Y-%m-%dT%H:%M:%SZ)]"
          git pull --rebase origin main && git push
```

---

### Step 9 — Enable GitHub Actions Write Permission

1. Go to your repo → **Settings** → **Actions** → **General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Click **Save**

---

## How It Works

### The CSV / Google Sheet

The Google Sheet is the source of truth. Each row is an employee. The `status` column drives everything:

- `active` — no action needed
- `terminated` — fires the Leaver handler
- `mover` — fires the Mover handler
- New row not in previous snapshot — fires the Joiner handler

### The State Snapshot

After every run the pipeline saves `state/snapshot.json` — a snapshot of the current employee data. On the next run it compares the new sheet data against this snapshot to detect what changed.

```json
{
  "run_timestamp": "2026-05-08T00:00:00Z",
  "employees": {
    "E001": {
      "name": "John Smith",
      "email": "john.smith@yourcompany.com",
      "department": "Engineering",
      "role": "Software Engineer",
      "status": "active",
      "manager_email": "manager@yourcompany.com"
    }
  }
}
```

### Change Detection Logic

```python
for emp_id, emp in current.items():
    if emp_id not in previous:
        # New employee → JOINER
    elif emp["status"] == "terminated" and previous[emp_id]["status"] != "terminated":
        # Status changed to terminated → LEAVER
    elif emp["department"] != previous[emp_id]["department"]:
        # Department changed → MOVER

for emp_id in previous:
    if emp_id not in current:
        # Row deleted from sheet → LEAVER
```

### Webhook Payload

Each handler sends a POST request to the Apps Script webhook:

```json
{
  "action": "leaver",
  "employee": {
    "employee_id": "E001",
    "name": "John Smith",
    "email": "john.smith@yourcompany.com",
    "department": "Engineering",
    "role": "Software Engineer",
    "status": "terminated",
    "manager_email": "manager@yourcompany.com"
  }
}
```

---

## Testing the Pipeline

### Test a Joiner

1. Add a new row to your Google Sheet with a real `@yourcompany.com` email and status `active`
2. Make sure that `employee_id` does not exist in `state/snapshot.json`
3. Trigger a manual run in GitHub Actions
4. Check Google Workspace Admin → Users for the new account

### Test a Leaver

1. Change an existing employee's status to `terminated` in the sheet
2. Trigger a manual run
3. Check Google Workspace Admin → Users — the account should be suspended

### Trigger a Manual Run

1. Go to your GitHub repo → **Actions** tab
2. Click **JML Pipeline** in the left sidebar
3. Click **Run workflow** → green **Run workflow** button

> 📸 **[Screenshot: GitHub Actions showing successful runs including a scheduled run]**

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` on Google Sheet | Sheet is not public | Share sheet as "Anyone with the link can view" |
| `Webhook response: 4xx` | Apps Script not deployed correctly | Redeploy as Web app with "Anyone" access |
| `No changes detected` | Snapshot already matches sheet | Modify an employee status in the sheet |
| `No license available` | Google Workspace user limit reached | Upgrade your Workspace plan |
| Push rejected in Actions | Remote has newer commits | Add `git pull --rebase` before push in workflow |

---

## Key Design Decisions

**Why Google Apps Script instead of direct Admin SDK?**
GCP org policies can block service account key creation (`iam.disableServiceAccountKeyCreation`). Google Apps Script runs natively inside Google Workspace with full Admin SDK access — no GCP credentials needed.

**Why a snapshot file instead of a database?**
The snapshot lives in the repo itself. GitHub Actions commits it back after every run. Zero external dependencies, full audit trail in git history.

**Why GitHub Actions instead of a server?**
Free, serverless, and the cron scheduling is built in. The entire infrastructure cost is $0.

---

## What's Next

- [ ] Add Google Workspace license management
- [ ] Add Slack/Teams notifications for joiners and movers
- [ ] Connect to a real HR system API (Workday, BambooHR) instead of Google Sheets
- [ ] Add Cloud Logging for audit trail
- [ ] Build a dashboard showing provisioning history

---

## Tech Stack

- **Python 3.11** — pipeline logic
- **GitHub Actions** — scheduling and CI/CD
- **Google Sheets API** — HR data source
- **Google Apps Script** — Workspace provisioning webhook
- **Google Workspace Admin SDK** — user and group management
- **requests** — HTTP client for webhook calls

---

## License

MIT<img width="1571" height="791" alt="F2" src="https://github.com/user-attachments/assets/41d2a5a7-60a3-4714-ac59-e1a70053ebbd" />
