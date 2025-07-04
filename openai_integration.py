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
        # Prepare the prompt with pre-analyzed student personality signatures
        students_text = ""
        for idx, student in enumerate(students_data):
            students_text += f"\nStudent {idx + 1} (ID: {student['id']}, Name: {student['name']}):\n"
            students_text += f"- Archetype: {student['archetype']}\n"
            students_text += f"- Core Strength: {student['core_strength']}\n"
            students_text += f"- Hidden Potential: {student['hidden_potential']}\n"
            students_text += f"- Conversation Catalyst: {student['conversation_catalyst']}\n"
        
        prompt = f"""You are a master strategist and elite team formation specialist. You receive concise intelligence briefings on student personality signatures, not raw data.

Below are pre-analyzed student profiles with their key personality signatures:

{students_text}

Your strategic mission:
1. Form elite squads of 3-4 members by analyzing complementary Personality Signatures
2. Look for strategic combinations where different archetypes create powerful synergies
3. Balance core strengths with hidden potentials for maximum team effectiveness
4. Create Japanese squad names that reflect their collective strategic advantage
5. Think like a master strategist forming specialized units

Respond with a JSON object in this exact format:
{{
    "squads": [
        {{
            "squad_name": "Strategic Japanese name that reflects their combined power",
            "member_ids": [list of student IDs],
            "shared_interests": "Concise Japanese summary of their strategic synergy and what makes them powerful together"
        }}
    ]
}}

Strategic Requirements:
- Every student must be assigned to exactly one squad
- Squad names MUST be in Japanese kanji/kana only - NO romaji or English
- Focus on complementary personality signatures, not just similarities
- Shared interests should explain their strategic advantage as a team
- Think quality over quantity - create elite, balanced teams

Form teams that would dominate any challenge through their complementary strengths!"""

        # Create OpenAI client with timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=30.0  # 30 second timeout
        )
        
        response = timeout_client.chat.completions.create(
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
    Generate personalized icebreaker questions using Connection Blueprint analysis
    Acts as an expert social facilitator to find deep connections between squad members
    """
    try:
        # Prepare detailed member profiles for Connection Blueprint analysis
        members_text = ""
        for member in squad_members_data:
            members_text += f"\n{member['name']}:\n"
            members_text += f"- Adventure Co-Pilot: {member['question1']}\n"
            members_text += f"- Passion Deep-Dive: {member['question2']}\n"
            members_text += f"- Laughter Test: {member['question3']}\n"
            members_text += f"- Secret Superpower: {member['question4']}\n"
            members_text += f"- Vibe Check: {member['question5']}\n"
            members_text += f"- Ultimate Crew Quality: {member['question6']}\n"
        
        prompt = f"""You are an expert social facilitator creating Connection Blueprint icebreakers for squad "{squad_name}".

STEP 1: DEEP CONNECTION ANALYSIS
Analyze these squad members to identify:
- ONE SYNERGY POINT: A shared interest, value, or experience that connects them
- ONE COMPLEMENTARITY POINT: Different but compatible strengths that would enhance their group dynamic

Squad members:
{members_text}

STEP 2: TARGETED ICEBREAKER CREATION
Based on your analysis, create TWO Japanese icebreaker questions that:
- Reference the specific SYNERGY you identified (shared connection)
- Leverage the COMPLEMENTARITY you found (different strengths working together)
- Feel natural and engaging for college students
- Encourage deep, meaningful conversation beyond surface level
- Are written in warm, friendly Japanese

RESPONSE FORMAT:
Return a JSON object: {{"icebreakers": ["Question 1 in Japanese", "Question 2 in Japanese"]}}

IMPORTANT: These questions should feel uniquely crafted for THIS specific group based on the deep connections you've discovered. Act like a social facilitator who truly understands what makes people connect."""

        # Create OpenAI client with timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=30.0  # 30 second timeout for deep analysis
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert social facilitator who finds deep, meaningful connections between people to create truly engaging conversation starters."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,  # Balanced creativity for meaningful connections
            max_tokens=400,
        )

        if response.choices[0].message.content:
            icebreaker_data = json.loads(response.choices[0].message.content)
            logging.info(f"Generated Connection Blueprint icebreakers for {squad_name}: {icebreaker_data}")
            # Return the JSON string to store in database
            return json.dumps(icebreaker_data, ensure_ascii=False)
        else:
            raise ValueError("Empty response from AI")

    except Exception as e:
        logging.error(f"Error generating Connection Blueprint icebreaker: {str(e)}")
        # Return meaningful fallback icebreakers in JSON format
        fallback_icebreakers = {
            "icebreakers": [
                "チームの中で一番「これは私の隠れた才能だ！」と思うものを一つずつ紹介して、それをどう組み合わせたら面白いプロジェクトができそうか話し合ってみよう。",
                "みんなの答えを見ていて、この中で一番「運命的な出会い」だと思う組み合わせはどれ？その理由も含めて教えて。"
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
        
        # Create OpenAI client with timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=15.0  # 15 second timeout for translations
        )
        
        response = timeout_client.chat.completions.create(
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


def generate_archetype(student_answers):
    """
    Generate a creative Japanese nickname for the student
    """
    try:
        # Prepare the student answers text
        answers_text = ""
        for i in range(1, 7):
            question_key = f'question{i}'
            if question_key in student_answers:
                answers_text += f"Question {i}: {student_answers[question_key]}\n"
        
        prompt = f"""Based on these student answers, create only a creative Japanese nickname (2-4 words):

{answers_text}

Return only the Japanese nickname that captures their personality."""

        # Create OpenAI client with short timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=10.0
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a creative nickname generator. Create concise Japanese nicknames."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=50
        )
        
        if response.choices[0].message.content:
            result = response.choices[0].message.content.strip()
            logging.info(f"Generated archetype: {result}")
            return result
        else:
            return "個性豊かな学生"
            
    except Exception as e:
        logging.error(f"Error generating archetype: {str(e)}")
        return "個性豊かな学生"


def generate_core_strength(student_answers):
    """
    Generate a sentence about their strength as a friend
    """
    try:
        # Prepare the student answers text
        answers_text = ""
        for i in range(1, 7):
            question_key = f'question{i}'
            if question_key in student_answers:
                answers_text += f"Question {i}: {student_answers[question_key]}\n"
        
        prompt = f"""Based on these student answers, write 1 sentence in Japanese about their strength as a friend:

{answers_text}

Return only the Japanese sentence about their core strength."""

        # Create OpenAI client with short timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=10.0
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a personality analyst. Write concise Japanese sentences about strengths."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        if response.choices[0].message.content:
            result = response.choices[0].message.content.strip()
            logging.info(f"Generated core strength: {result}")
            return result
        else:
            return "創造的な思考力と独自の視点を持っています。"
            
    except Exception as e:
        logging.error(f"Error generating core strength: {str(e)}")
        return "創造的な思考力と独自の視点を持っています。"


def generate_hidden_potential(student_answers):
    """
    Generate a sentence about their untapped ability
    """
    try:
        # Prepare the student answers text
        answers_text = ""
        for i in range(1, 7):
            question_key = f'question{i}'
            if question_key in student_answers:
                answers_text += f"Question {i}: {student_answers[question_key]}\n"
        
        prompt = f"""Based on these student answers, write 1 sentence in Japanese about their hidden potential or untapped ability:

{answers_text}

Return only the Japanese sentence about their hidden potential."""

        # Create OpenAI client with short timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=10.0
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a personality analyst. Write concise Japanese sentences about hidden potential."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        if response.choices[0].message.content:
            result = response.choices[0].message.content.strip()
            logging.info(f"Generated hidden potential: {result}")
            return result
        else:
            return "リーダーシップの才能が眠っている可能性があります。"
            
    except Exception as e:
        logging.error(f"Error generating hidden potential: {str(e)}")
        return "リーダーシップの才能が眠っている可能性があります。"


def generate_conversation_catalyst(student_answers):
    """
    Generate a conversation starter based on their interests
    """
    try:
        # Prepare the student answers text
        answers_text = ""
        for i in range(1, 7):
            question_key = f'question{i}'
            if question_key in student_answers:
                answers_text += f"Question {i}: {student_answers[question_key]}\n"
        
        prompt = f"""Based on these student answers, write 1 sentence in Japanese about a conversation starter from their interests:

{answers_text}

Return only the Japanese sentence about how to start a conversation with them."""

        # Create OpenAI client with short timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=10.0
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a conversation expert. Write concise Japanese sentences about conversation starters."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        if response.choices[0].message.content:
            result = response.choices[0].message.content.strip()
            logging.info(f"Generated conversation catalyst: {result}")
            return result
        else:
            return "趣味や興味のあることについて話すと、とても輝いて見えます。"
            
    except Exception as e:
        logging.error(f"Error generating conversation catalyst: {str(e)}")
        return "趣味や興味のあることについて話すと、とても輝いて見えます。"

