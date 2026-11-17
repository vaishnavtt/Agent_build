# AgentForge AI - Shared Schema & Node Definitions

This directory serves as the **single source of truth** for data contracts, workflow schemas, and node specifications across all six team members and subsystems (Frontend, Backend, AI Agent Architect, Workflow Engine, Testing).

## Directory Structure

- `workflow.schema.json`: JSON Schema (Draft 2020-12) specifying the valid structure of an AgentForge AI visual workflow.
- `node_definitions.json`: Registry of supported node types, default handles, metadata, icons, and configuration schemas.
- `types.ts`: TypeScript interfaces matching the JSON Schema for type-safe frontend and client development.

## Supported Node Types

| Node Type | Category | Icon | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **Input** | IO | `FileInput` | Ingests initial prompts, user parameters, or file triggers |
| **LLM** | AI | `Bot` | Executes reasoning/generation with Google Gemini models |
| **Document Reader** | Data | `FileText` | Extracts and chunks text from PDF, Markdown, DOCX files |
| **Tool** | Action | `Wrench` | Invokes external APIs or Python execution tools |
| **Condition** | Logic | `GitFork` | Evaluates boolean expressions for branching execution paths |
| **Human Approval** | Control | `UserCheck` | Pauses execution for human review and sign-off |
| **Output** | IO | `FileOutput` | Terminal node formatting and returning the workflow output |

## Workflow Format Specification

A minimal valid workflow adheres to:
```json
{
  "schemaVersion": "1.0.0",
  "metadata": {
    "id": "uuid-v4",
    "name": "Sample Workflow",
    "version": "1.0.0",
    "createdAt": "2026-11-17T00:00:00Z",
    "updatedAt": "2026-11-17T00:00:00Z"
  },
  "configuration": {
    "timeoutSeconds": 300,
    "maxRetries": 2,
    "autoRepairEnabled": true,
    "executionMode": "langgraph"
  },
  "nodes": [],
  "edges": []
}
```

