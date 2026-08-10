"""
File: models/skill.py

Description:
Defines the Skill domain model used throughout the application.
A Skill represents any named capability, tool, method, or area of knowledge
possessed by a candidate or required by a job.

Author:
Navneet Prakash Yadav
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Skill(BaseModel):
    """
    Represents a job-relevant capability.
    """

    name: str = Field(..., description="Name of the skill.")

    category: Optional[str] = Field(default=None, description="Optional category of the skill.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Skill name cannot be empty.")

        canonical_names = {
            "ai": "AI",
            "agentic ai": "Agentic AI",
            "api": "API",
            "aws": "AWS",
            "c#": "C#",
            "c++": "C++",
            "crm": "CRM",
            "data structures and algorithms": "Data Structures and Algorithms",
            "dbms": "DBMS",
            "gcp": "GCP",
            "generative ai": "Generative AI",
            "google colab": "Google Colab",
            "github": "GitHub",
            "javascript": "JavaScript",
            "jupyter": "Jupyter",
            "langchain": "LangChain",
            "langgraph": "LangGraph",
            "llm": "LLM",
            "llms": "LLMs",
            "ms excel": "MS Excel",
            "ms powerpoint": "MS PowerPoint",
            "ms word": "MS Word",
            "mongodb": "MongoDB",
            "mysql": "MySQL",
            "nlp": "NLP",
            "node.js": "Node.js",
            "numpy": "NumPy",
            "opencv": "OpenCV",
            "pos": "POS",
            "power bi": "Power BI",
            "pytorch": "PyTorch",
            "react.js": "React.js",
            "rest api": "REST API",
            "rest apis": "REST APIs",
            "seo": "SEO",
            "sop": "SOP",
            "sops": "SOPs",
            "scikit-learn": "Scikit-learn",
            "socket.io": "Socket.IO",
            "sql": "SQL",
            "streamlit": "Streamlit",
            "tensorflow": "TensorFlow",
            "typescript": "TypeScript",
            "ui": "UI",
            "ux": "UX",
            "vs code": "VS Code",
            "webrtc": "WebRTC",
        }

        canonical_name = canonical_names.get(value.casefold())
        if canonical_name is not None:
            return canonical_name
        if value.isupper() and any(character.isalpha() for character in value):
            return value
        return value.title()
