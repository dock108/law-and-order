"""Email template renderer using Jinja2.

This module provides utilities for loading and rendering email templates.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Union

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Path to email templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "email_templates"


def render_email_template(
    template_name: str, context: Dict[str, Union[str, Dict]]
) -> str:
    """Render an email template with the provided context.

    Args:
        template_name: The name of the template file to render
        context: Dictionary containing variables to inject into the template

    Returns:
        The rendered HTML template as a string

    Raises:
        FileNotFoundError: If the template file doesn't exist
        jinja2.exceptions.TemplateError: If there are syntax errors in the template
    """
    if not os.path.exists(TEMPLATES_DIR / template_name):
        raise FileNotFoundError(f"Email template {template_name} not found")

    # Set up Jinja environment
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Add current_year to the context
    if "current_year" not in context:
        context["current_year"] = datetime.now().year

    # Load and render the template
    template = env.get_template(template_name)
    return template.render(**context)
