#!/usr/bin/env python3
"""
API wrapper for Docassemble document generation.

This script provides API endpoints to generate documents from templates
using Docassemble, including a specific endpoint for retainer agreements.
"""

import logging
import os

import requests
from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import BadRequest, InternalServerError

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCASSEMBLE_URL = "http://localhost:8080"  # Internal container URL
API_KEY = os.environ.get("DOCASSEMBLE_API_KEY", "")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return "OK", 200


@app.route("/api/v1/generate/retainer", methods=["POST"])
def generate_retainer():
    """
    Generate a retainer agreement PDF from JSON data.

    Expected JSON payload:
    {
        "client": {
            "full_name": "John Doe",
            "address": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip": "10001"
        },
        "incident": {
            "type": "Motor Vehicle Accident",
            "date": "January 1, 2025",
            "location": "New York, NY"
        },
        "attorney": {
            "full_name": "Jane Smith"
        },
        "firm": {
            "address": "456 Law Street",
            "city": "New York",
            "state": "NY",
            "zip": "10002"
        },
        "fee": {
            "percentage": "33.33"
        }
    }
    """
    try:
        # Get JSON data from request
        payload = request.get_json()
        if not payload:
            raise BadRequest("Missing JSON payload")

        logger.info("Received request to generate retainer agreement")

        # Generate a client ID from name if available
        client_id = "unknown"
        if payload.get("client", {}).get("full_name"):
            client_id = payload["client"]["full_name"].replace(" ", "_")

        # API endpoint for running an interview and getting a document
        interview_url = f"{DOCASSEMBLE_URL}/api/run_interview"

        # Set up the interview data
        interview_data = {
            "interview": "playground:retainer_interview.yml",
            "user_id": "api@example.com",
            "interface": "json",
            "secret": API_KEY,
            "question_data": payload,
            "format": "pdf",
        }

        # Run the interview
        logger.info("Calling Docassemble API to generate document")
        response = requests.post(interview_url, json=interview_data)

        # Check if the API call was successful
        if response.status_code != 200:
            logger.error(f"Docassemble API error: {response.status_code}")
            logger.error(response.text)
            raise InternalServerError("Failed to generate document")

        # Parse the response
        result = response.json()

        # Check if the interview completed successfully
        if "attachment" not in result or not result["attachment"]:
            logger.error("No attachment returned from Docassemble")
            raise InternalServerError("No document was generated")

        # Get the attachment data
        attachment_data = result["attachment"]

        # Create filename
        filename = f"Retainer_Agreement_{client_id}.pdf"

        # Create a response with the PDF data
        return Response(
            attachment_data,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except BadRequest as e:
        logger.error(f"Bad request: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except InternalServerError as e:
        logger.error(f"Internal server error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


if __name__ == "__main__":
    # For local development only - in production, this will be run by Gunicorn
    app.run(host="0.0.0.0", port=5000, debug=True)
