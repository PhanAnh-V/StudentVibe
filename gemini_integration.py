import json
import logging
import os

from google import genai
from google.genai import types
from pydantic import BaseModel


# IMPORTANT: KEEP THIS COMMENT
# Follow these instructions when using this blueprint:
# - Note that the newest Gemini model series is "gemini-2.5-flash" or gemini-2.5-pro"
#   - do not change this unless explicitly requested by the user
# - Sometimes the google genai SDK has occasional type errors. You might need to run to validate, at time.  
# The SDK was recently renamed from google-generativeai to google-genai. This file reflects the new name and the new APIs.

# This API key is from Gemini Developer API Key, not vertex AI API Key
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def group_students_into_squads(students_data):
    """
    Use AI to intelligently group students into squads of 3-4 based on their interests
    """
    try:
        # Prepare the prompt with student data
        students_text = ""
        for idx, student in enumerate(students_data):
            students_text += f"\nStudent {idx + 1} (ID: {student['id']}, Name: {student['name']}):\n"
            for i in range(1, 7):
                students_text += f"- Q{i}: {student[f'question{i}']}\n"
        
        prompt = f"""You are a social dynamics expert specializing in creating meaningful connections between students.

Below are student responses to 6 questions about their interests, passions, and personalities:

{students_text}

Your task:
1. Group these students into squads of 3-4 members each
2. Ensure each squad has a good balance of shared interests AND complementary qualities
3. Look for both similarities that will bond them and differences that will help them grow
4. Consider personality types, energy levels, and collaborative potential

Respond with a JSON object in this exact format:
{{
    "squads": [
        {{
            "name": "Creative and engaging squad name",
            "member_ids": [list of student IDs],
            "shared_interests": "Brief description of what bonds this group",
            "reasoning": "Why these students work well together"
        }}
    ]
}}

Make sure every student is assigned to exactly one squad."""

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.8,
            ),
        )

        if response.text:
            return json.loads(response.text)
        else:
            raise ValueError("Empty response from AI")

    except Exception as e:
        logging.error(f"Error in AI squad grouping: {str(e)}")
        raise


def generate_squad_icebreaker(squad_members_data, squad_name):
    """
    Generate a personalized icebreaker question for a specific squad
    """
    try:
        # Prepare member details
        members_text = ""
        for member in squad_members_data:
            members_text += f"\n{member['name']}:\n"
            members_text += f"- Adventure style: {member['question1']}\n"
            members_text += f"- Passion: {member['question2']}\n"
            members_text += f"- Humor: {member['question3']}\n"
            members_text += f"- Superpower: {member['question4']}\n"
            members_text += f"- Vibe: {member['question5']}\n"
            members_text += f"- Team quality: {member['question6']}\n"
        
        prompt = f"""You are creating a fun, personalized icebreaker question for a squad called "{squad_name}".

Squad members and their interests:
{members_text}

Create ONE unique, engaging icebreaker question that:
1. References specific interests or answers from the squad members
2. Encourages creative, fun responses
3. Helps the squad bond over shared experiences or discover new things about each other
4. Is playful and age-appropriate for students
5. Sparks conversation and laughter

The icebreaker should feel personal to THIS specific group, not generic.

Respond with just the icebreaker question text, nothing else."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.9,
                max_output_tokens=150,
            ),
        )

        if response.text:
            return response.text.strip()
        else:
            raise ValueError("Empty response from AI")

    except Exception as e:
        logging.error(f"Error generating icebreaker: {str(e)}")
        # Return a fallback icebreaker
        return "If your squad had to create a theme song using only sounds you can make with your body, what would it sound like?"