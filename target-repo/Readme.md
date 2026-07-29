# AI Coding Agent

An autonomous AI agent designed to understand an existing Node.js/Express codebase and implement product requirements with minimal guidance.

## Architecture & Agent Workflow
- **LLM Engine:** Groq API / OpenAI Client integration for agentic decision-making and code modifications.
- **Workflow Steps:**
  1. **Repo Exploration:** Automatically walks the repository structure to inspect key directories (`app/controllers`, `app/models`, `app/routes`).
  2. **Plan Generation:** Analyzes user requirements (`Improve organisation and search`) and creates an execution strategy (tagging system implementation).
  3. **Code Modification:** Dynamically updates schema and injects tag filtering endpoint (`GET /notes/tag?tag=...`) into controller routes.
  4. **Summary Output:** Outputs structured logs summarizing modified files and new endpoints.

## How the Repository is Explored
The agent inspects file paths dynamically to locate entry points (`server.js`), schema definitions (`app/models/note.model.js`), and CRUD handlers (`app/controllers/note.controller.js`).

## Assumptions & Trade-offs
- Added an array field `tags` to the MongoDB note schema to support scalable organization.
- Added a focused endpoint (`/notes/tag`) to query by tag while preserving all existing legacy CRUD endpoints and database behavior.

## Demo Video
- **Google Drive Link:** [INSERT YOUR GOOGLE DRIVE VIDEO LINK HERE]