# AI Coding Agent

An autonomous AI agent built in Python to explore an existing codebase, analyze product requirements, and implement new features with minimal user guidance.

## Architecture & Agent Workflow
- **LLM Engine:** Integrated with Groq API (OpenAI-compatible client) for fast code reasoning and tool calling.
- **Workflow:**
  1. **Exploration Phase:** Systematically scans repo structure, reads core route handlers, controllers, and models.
  2. **Planning Phase:** Analyzes requirement ("organise and search notes") and formulates an implementation plan (Tagging system).
  3. **Execution Phase:** Updates Mongoose schema with `tags` array and injects new filtering routes (`GET /notes/tag?tag=...`).
  4. **Verification & Summary:** Outputs logs of modified files and endpoints.

## Repository Exploration Strategy
The agent programmatically inspects directory trees to identify main app files (`server.js`), route files (`app/routes`), controllers (`app/controllers`), and schemas (`app/models`).

## Assumptions & Trade-offs
- Introduced tag-based filtering (`/notes/tag?tag=...`) to enhance searchability without breaking existing MongoDB CRUD contracts.
- Backward compatibility preserved for all original endpoints (`POST /notes`, `GET /notes`, etc.).

## Screen Recording Demo
- **Google Drive Video:** [YOUR_GOOGLE_DRIVE_LINK_HERE]