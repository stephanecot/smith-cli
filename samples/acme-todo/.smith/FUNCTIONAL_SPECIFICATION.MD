# Acme Todo — Functional specification

## 1. Mission

A small team-collaboration todo manager used by ~30 engineers at Acme.
Each user owns a list of tasks ; tasks can be shared with teammates and
grouped into projects. The product exists to replace the dispersion of
todo lists across personal note apps with a single, audited backlog.

## 2. Personas

- **Engineer** — creates and edits their own todos ; comments on shared todos.
- **Tech lead** — reviews the team's open todos, prioritises, reassigns.
- **Engineering manager** — read-only access to all projects ; runs weekly digests.
- **System admin** — manages users, projects, and integration tokens.

## 3. User stories

### Todo basics
- As an engineer, I want to create a todo with title + description, so that I capture work to do later.
- As an engineer, I want to mark a todo as done, so that my list stays tidy.
- As an engineer, I want to set a due date, so that the system can warn me when it's overdue.

### Sharing
- As an engineer, I want to share a todo with a teammate, so that we can collaborate.
- As a tech lead, I want to reassign a todo, so that I can balance the team's load.

### Projects
- As an engineer, I want to group todos into a project, so that I can see all related work at once.
- As an engineering manager, I want a project digest emailed weekly, so that I track progress without nagging the team.

### Audit
- As an admin, I want to see every status change on a todo, so that I can audit who closed what.

## 4. Business rules

- A todo's title is mandatory, ≤ 120 characters.
- A todo can have at most 10 collaborators.
- A todo cannot be deleted ; closing is the only terminal state.
- Overdue tasks (`due_date < now AND status != done`) appear in red on the UI.
- The weekly digest fires every Monday at 09:00 UTC. [INFERRED]

## 5. Integrations

- **GitHub** — link a todo to a PR via the `gh:owner/repo#123` shorthand.
- **Slack** — `/acme-todo` slash command to create a todo from chat.
- **Auth** — Acme SSO (SAML 2.0), no local accounts.

## 6. Out of scope

- Calendar sync — Acme uses Google Calendar separately ; no integration planned.
- Mobile apps — web-only for v1.
- Custom fields on todos — fixed schema in v1.
