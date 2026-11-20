"""Planner Agent - Plans workflow architectures from natural language prompts or specifications.
Decomposes requirements into structured multi-agent graphs with canonical nodes and connections.
"""

from typing import List, Dict, Any, Optional
import json
import logging
from app.core.gemini_client import call_gemini

logger = logging.getLogger(__name__)

# Canonical component templates
DEFAULT_TEMPLATES = {
    "resume": {
        "name": "Resume Evaluation Agent",
        "description": "Reads resumes, extracts candidate skills, compares with job specs, scores fit, and creates evaluation scorecard.",
        "nodes": [
            {
                "id": "node-1",
                "type": "customWorkflow",
                "position": {"x": 100, "y": 150},
                "data": {
                    "label": "Upload Resume",
                    "componentType": "Input",
                    "status": "ready",
                    "config": {"source": "file_upload", "allowedTypes": ["pdf", "docx"]},
                },
            },
            {
                "id": "node-2",
                "type": "customWorkflow",
                "position": {"x": 380, "y": 150},
                "data": {
                    "label": "Read Resume PDF",
                    "componentType": "Document Reader",
                    "status": "ready",
                    "config": {"extractText": True, "parseTables": False},
                },
            },
            {
                "id": "node-3",
                "type": "customWorkflow",
                "position": {"x": 660, "y": 150},
                "data": {
                    "label": "Evaluate Fit (Gemini)",
                    "componentType": "LLM",
                    "status": "ready",
                    "config": {
                        "model": "gemini-1.5-pro",
                        "instructions": "Analyze candidate skills in React, TypeScript, Python and score alignment from 1 to 10.",
                        "temperature": 0.3,
                    },
                },
            },
            {
                "id": "node-4",
                "type": "customWorkflow",
                "position": {"x": 940, "y": 150},
                "data": {
                    "label": "Check Score Threshold",
                    "componentType": "Condition",
                    "status": "ready",
                    "config": {"rule": "fit_score >= 7", "field": "score"},
                },
            },
            {
                "id": "node-5",
                "type": "customWorkflow",
                "position": {"x": 1220, "y": 80},
                "data": {
                    "label": "Hiring Manager Review",
                    "componentType": "Human Approval",
                    "status": "ready",
                    "config": {"approverRole": "Lead Recruiter", "timeoutHours": 24},
                },
            },
            {
                "id": "node-6",
                "type": "customWorkflow",
                "position": {"x": 1500, "y": 150},
                "data": {
                    "label": "Evaluation Report",
                    "componentType": "Output",
                    "status": "ready",
                    "config": {"format": "markdown_card", "notifySlack": True},
                },
            },
        ],
        "edges": [
            {"id": "e1-2", "source": "node-1", "target": "node-2", "animated": True},
            {"id": "e2-3", "source": "node-2", "target": "node-3", "animated": True},
            {"id": "e3-4", "source": "node-3", "target": "node-4", "animated": True},
            {"id": "e4-5", "source": "node-4", "target": "node-5", "sourceHandle": "true", "animated": True},
            {"id": "e5-6", "source": "node-5", "target": "node-6", "animated": True},
        ],
    },
    "invoice": {
        "name": "Invoice & Receipt Processor",
        "description": "Extracts vendor, line items, and totals from invoices; validates against purchase orders.",
        "nodes": [
            {
                "id": "node-1",
                "type": "customWorkflow",
                "position": {"x": 100, "y": 150},
                "data": {
                    "label": "Receive Invoice",
                    "componentType": "Input",
                    "status": "ready",
                    "config": {"source": "email_attachment", "allowedTypes": ["pdf", "jpg"]},
                },
            },
            {
                "id": "node-2",
                "type": "customWorkflow",
                "position": {"x": 380, "y": 150},
                "data": {
                    "label": "OCR & Parser",
                    "componentType": "Document Reader",
                    "status": "ready",
                    "config": {"extractText": True, "parseTables": True},
                },
            },
            {
                "id": "node-3",
                "type": "customWorkflow",
                "position": {"x": 660, "y": 150},
                "data": {
                    "label": "Extract Totals & Line Items",
                    "componentType": "LLM",
                    "status": "ready",
                    "config": {
                        "model": "gemini-1.5-flash",
                        "instructions": "Extract invoice number, total amount, VAT, and vendor details into structured JSON.",
                    },
                },
            },
            {
                "id": "node-4",
                "type": "customWorkflow",
                "position": {"x": 940, "y": 150},
                "data": {
                    "label": "Audit Amount (> $1000)",
                    "componentType": "Condition",
                    "status": "ready",
                    "config": {"rule": "total_amount > 1000"},
                },
            },
            {
                "id": "node-5",
                "type": "customWorkflow",
                "position": {"x": 1220, "y": 80},
                "data": {
                    "label": "Finance Manager Approval",
                    "componentType": "Human Approval",
                    "status": "ready",
                    "config": {"approverRole": "Finance Controller"},
                },
            },
            {
                "id": "node-6",
                "type": "customWorkflow",
                "position": {"x": 1500, "y": 150},
                "data": {
                    "label": "ERP System Sync",
                    "componentType": "Tool",
                    "status": "ready",
                    "config": {"toolName": "AccountingAPI", "endpoint": "https://api.erp.internal/invoices"},
                },
            },
            {
                "id": "node-7",
                "type": "customWorkflow",
                "position": {"x": 1780, "y": 150},
                "data": {
                    "label": "Processing Receipt",
                    "componentType": "Output",
                    "status": "ready",
                    "config": {"format": "json_receipt"},
                },
            },
        ],
        "edges": [
            {"id": "e1-2", "source": "node-1", "target": "node-2", "animated": True},
            {"id": "e2-3", "source": "node-2", "target": "node-3", "animated": True},
            {"id": "e3-4", "source": "node-3", "target": "node-4", "animated": True},
            {"id": "e4-5", "source": "node-4", "target": "node-5", "sourceHandle": "true", "animated": True},
            {"id": "e5-6", "source": "node-5", "target": "node-6", "animated": True},
            {"id": "e4-6", "source": "node-4", "target": "node-6", "sourceHandle": "false", "animated": True},
            {"id": "e6-7", "source": "node-6", "target": "node-7", "animated": True},
        ],
    },
    "support": {
        "name": "Customer Support Dispatcher",
        "description": "Classifies incoming customer tickets, extracts urgency, crafts response draft, and routes to team.",
        "nodes": [
            {
                "id": "node-1",
                "type": "customWorkflow",
                "position": {"x": 100, "y": 150},
                "data": {
                    "label": "Customer Ticket",
                    "componentType": "Input",
                    "status": "ready",
                    "config": {"source": "zendesk_webhook"},
                },
            },
            {
                "id": "node-2",
                "type": "customWorkflow",
                "position": {"x": 380, "y": 150},
                "data": {
                    "label": "Classify & Sentiment",
                    "componentType": "LLM",
                    "status": "ready",
                    "config": {
                        "model": "gemini-1.5-flash",
                        "instructions": "Determine intent (Billing, Technical, Account) and customer sentiment (Frustrated, Neutral, Happy).",
                    },
                },
            },
            {
                "id": "node-3",
                "type": "customWorkflow",
                "position": {"x": 660, "y": 150},
                "data": {
                    "label": "Check Urgent Escalation",
                    "componentType": "Condition",
                    "status": "ready",
                    "config": {"rule": "urgency == 'HIGH' or sentiment == 'Frustrated'"},
                },
            },
            {
                "id": "node-4",
                "type": "customWorkflow",
                "position": {"x": 940, "y": 80},
                "data": {
                    "label": "Senior Support Review",
                    "componentType": "Human Approval",
                    "status": "ready",
                    "config": {"approverRole": "Tier 3 Specialist"},
                },
            },
            {
                "id": "node-5",
                "type": "customWorkflow",
                "position": {"x": 1220, "y": 150},
                "data": {
                    "label": "Auto-Draft Response",
                    "componentType": "LLM",
                    "status": "ready",
                    "config": {
                        "model": "gemini-1.5-pro",
                        "instructions": "Draft an empathetic, comprehensive solution addressing customer questions with documentation links.",
                    },
                },
            },
            {
                "id": "node-6",
                "type": "customWorkflow",
                "position": {"x": 1500, "y": 150},
                "data": {
                    "label": "Dispatch & Ticket Update",
                    "componentType": "Output",
                    "status": "ready",
                    "config": {"format": "zendesk_reply"},
                },
            },
        ],
        "edges": [
            {"id": "e1-2", "source": "node-1", "target": "node-2", "animated": True},
            {"id": "e2-3", "source": "node-2", "target": "node-3", "animated": True},
            {"id": "e3-4", "source": "node-3", "target": "node-4", "sourceHandle": "true", "animated": True},
            {"id": "e4-5", "source": "node-4", "target": "node-5", "animated": True},
            {"id": "e3-5", "source": "node-3", "target": "node-5", "sourceHandle": "false", "animated": True},
            {"id": "e5-6", "source": "node-5", "target": "node-6", "animated": True},
        ],
    },
}


class PlannerAgent:
    """Specialized AI agent responsible for planning multi-agent workflow topologies."""

    def __init__(self):
        self.role = "Workflow Planner"

    def plan_workflow(
        self, prompt: str, user_requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Translates user prompt or goal into a planned workflow graph with canonical nodes.
        Uses Gemini LLM if key is configured, with high-quality fallback heuristics.
        """
        p_lower = prompt.lower()

        # Check for Gemini generation first
        system_instruction = (
            "You are the Planner Agent for AgentForge AI. Convert the user's natural language goal into a JSON "
            "workflow graph. Use only these 7 canonical componentTypes: "
            "['Input', 'Document Reader', 'LLM', 'Tool', 'Condition', 'Human Approval', 'Output'].\n"
            "Respond ONLY with valid JSON having keys: 'name', 'description', 'requirements', 'nodes', 'edges'."
        )
        ai_response = call_gemini(prompt=prompt, system_instruction=system_instruction)
        if ai_response:
            try:
                # Strip markdown json blocks if returned
                clean_json = ai_response.strip()
                if clean_json.startswith("```"):
                    clean_json = clean_json.split("\n", 1)[1]
                    clean_json = clean_json.rsplit("```", 1)[0].strip()
                data = json.loads(clean_json)
                if "nodes" in data and "edges" in data:
                    return data
            except Exception as e:
                logger.warning(f"Failed to parse Gemini generated workflow: {e}")

        # Intelligent template selection based on intent
        if any(w in p_lower for w in ["invoice", "bill", "tax", "receipt", "accounting", "payment"]):
            tpl = DEFAULT_TEMPLATES["invoice"]
        elif any(w in p_lower for w in ["support", "ticket", "customer", "email", "sentiment", "escalat"]):
            tpl = DEFAULT_TEMPLATES["support"]
        else:
            tpl = DEFAULT_TEMPLATES["resume"]

        requirements = user_requirements or [
            "Ingest input data or document stream",
            "Extract structured attributes and content",
            "Perform AI cognitive reasoning and scoring",
            "Apply conditional routing and quality thresholds",
            "Present terminal output or evaluation scorecard",
        ]

        return {
            "name": tpl["name"],
            "description": prompt or tpl["description"],
            "requirements": requirements,
            "nodes": tpl["nodes"],
            "edges": tpl["edges"],
        }
