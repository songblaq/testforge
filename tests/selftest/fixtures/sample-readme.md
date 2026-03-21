# Sample Project README

This is a sample README used as test input for TestForge selftest fixtures.

## Features

- User authentication (login, logout, password reset)
- Dashboard with summary statistics
- Project management (create, list, update, delete)
- Report generation (Markdown, HTML)
- Settings page (profile, notifications, API keys)

## User Roles

- Admin: full access to all features
- Editor: can create and edit projects
- Viewer: read-only access

## Business Rules

- Users must be authenticated to access any feature
- Admins can delete any project; Editors can only delete their own
- Reports are generated on demand and cached for 1 hour
- API keys expire after 90 days of inactivity

## Screens

1. Login page (`/login`)
2. Dashboard (`/dashboard`)
3. Projects list (`/projects`)
4. Project detail (`/projects/:id`)
5. Report view (`/projects/:id/report`)
6. Settings (`/settings`)
