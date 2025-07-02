import json
import logging
import os

from openai import OpenAI


# IMPORTANT: KEEP THIS COMMENT
# Follow these instructions when using this blueprint:
# - Note that the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
#   do not change this unless explicitly requested by the user
# - Use the response_format: { type: "json_object" } option when requesting JSON responses
# - Request output in JSON format in the prompt

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


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

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a social dynamics expert specializing in creating meaningful connections between students."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )

        if response.choices[0].message.content:
            return json.loads(response.choices[0].message.content)
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
        
        prompt = f"""You are creating fun, personalized icebreaker questions for a squad called "{squad_name}".

Squad members and their interests:
{members_text}

Create TWO distinct, engaging icebreaker questions that:
1. Reference specific interests or answers from the squad members
2. Encourage creative, fun responses
3. Help the squad bond over shared experiences or discover new things about each other
4. Are playful and age-appropriate for students (18-23 years old, college age)
5. Spark conversation and laughter

The first question should be fun and lighthearted.
The second question should be more thoughtful and meaningful.
Both questions should feel personal to THIS specific group, not generic.

The final output must be in Japanese.

The response must be a JSON object containing a list of two distinct icebreaker questions. The required format is: {{"icebreakers": ["First Japanese question here", "Second Japanese question here"]}}."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are creating fun, personalized icebreaker questions for student squads."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.9,
            max_tokens=300,
        )

        if response.choices[0].message.content:
            icebreaker_data = json.loads(response.choices[0].message.content)
            # Return the JSON string to store in database
            return json.dumps(icebreaker_data, ensure_ascii=False)
        else:
            raise ValueError("Empty response from AI")

    except Exception as e:
        logging.error(f"Error generating icebreaker: {str(e)}")
        # Return a fallback icebreaker in JSON format
        fallback_icebreakers = {
            "icebreakers": [
                "もしあなたたちのスクワッドが体だけで作る音でテーマソングを作るとしたら、どんな音になりそう？",
                "今まで経験した中で一番「これは運命だった！」と思う出会いや発見について教えて。"
            ]
        }
        return json.dumps(fallback_icebreakers, ensure_ascii=False)


def translate_to_japanese(text):
    """
    Translate a given text to Japanese using OpenAI
    """
    try:
        if not text or not text.strip():
            return ""
            
        prompt = f"Please translate the following text to Japanese: {text}"
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate the given text to natural, conversational Japanese that would be appropriate for students."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200,
        )
        
        if response.choices[0].message.content:
            return response.choices[0].message.content.strip()
        else:
            logging.warning("Empty response from AI translation")
            return ""
            
    except Exception as e:
        logging.error(f"Error translating text to Japanese: {str(e)}")
        return ""  # Return empty string if translation fails