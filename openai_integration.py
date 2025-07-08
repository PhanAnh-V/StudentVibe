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
        # Prepare the prompt with pre-analyzed personality signatures for faster processing
        students_text = ""
        for idx, student in enumerate(students_data):
            students_text += f"\nStudent {idx + 1} (ID: {student['id']}, Name: {student['name']}):\n"
            students_text += f"- Archetype: {student.get('archetype', '個性豊かな学生')}\n"
            students_text += f"- Core Strength: {student.get('core_strength', '')}\n"
            students_text += f"- Hidden Potential: {student.get('hidden_potential', '')}\n"
            students_text += f"- Conversation Catalyst: {student.get('conversation_catalyst', '')}\n"
        
        prompt = f"""You are a master strategist forming elite teams. You will receive concise intelligence briefings on student personality signatures.

{students_text}

Your mission:
1. Form elite squads of 3-5 members by analyzing these Personality Signatures for strategic synergies.
2. Create a creative, engaging Japanese squad name that reflects their collective identity.
3. Write a short, insightful Japanese summary of their "shared_interests" or why their combination of signatures makes them a powerful team.

Respond with a JSON object in this exact format:
{{
    "squads": [
        {{
            "squad_name": "感動的な日本語のチーム名",
            "member_ids": [list of student IDs],
            "shared_interests": "このチームの相乗効果に関する洞察に満ちた日本語の要約"
        }}
    ]
}}

CRITICAL: Every student must be assigned to a squad. All text output must be in Japanese."""

        # Create OpenAI client with timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=30.0
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
        
        prompt = f"""Your Persona: You are "The Master Facilitator," an expert at designing conversations that build trust and connection.
The Squad's Data:
{members_text}

Your Mission:
Design a "Three-Act Conversation" for this specific group of students. Your goal is to provide a structured journey that moves them from easy common ground to deeper connection.

Step 1: Analyze the Group Dynamics.
Silently identify:
- Act I (Common Ground): Find a simple, fun, shared interest or experience across at least two members.
- Act II (Team-Up Challenge): Find a combination of different skills or ideas from their answers that could be used in a fun, hypothetical team challenge.
- Act III (Deeper Connection): Find a shared underlying value or emotion from their answers (e.g., a desire for adventure, a love for quiet moments, a specific type of humor).

Step 2: Generate the Three-Act Conversation.
Based on your analysis, generate three questions in Japanese.

Output Requirement:
Return a JSON object in this exact format:
{{
  "act_1_title": "「まずはここから：共通点さがし」",
  "act_1_question": "[A simple, fun question based on the 'Common Ground' you found.]",
  "act_2_title": "「ミッション：このチームならどうする？」",
  "act_2_question": "[A creative, hypothetical team-up question based on the 'Team-Up Challenge' you designed.]",
  "act_3_title": "「もう一歩深く：本当のつながり」",
  "act_3_question": "[A slightly more personal or reflective question based on the 'Deeper Connection' value you identified.]"
}}

Final Instructions:
- Each question must feel crafted specifically for THIS group.
- The flow from Act 1 to Act 3 should feel natural and increase in depth.
- All output text must be in friendly, engaging Japanese."""

        # Create OpenAI client with timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=30.0
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
            timeout=8.0  # Reduced timeout for translations
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
        
        prompt = f"""Your Persona: You are "The Storyteller," an AI that sees the core narrative in people's lives.
Your Framework: Analyze the student's answers through the lens of Narrative Identity to find their core archetype.
Student's Answers:
{answers_text}

Your Mission:
Based on the student's answers, identify their core Archetype. This should be a creative, inspiring Japanese title that makes them feel unique and understood. It is the name of their personal journey.

Output Requirement:
Respond with ONLY the Japanese title for the archetype.
Example Titles: 「静かな森の探検家」(Explorer of the Quiet Forest), 「アイデアの稲妻を放つ者」(One Who Unleashes the Lightning of Ideas), 「心の庭を育てる人」(The Gardener of the Heart's Garden)."""

        # Create OpenAI client with shorter timeout for faster processing
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=8.0  # Reduced from 30 to 8 seconds
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a creative nickname generator. Create concise Japanese nicknames."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=30  # Reduced tokens for faster response
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
        
        prompt = f"""Your Persona: You are "The Strength Finder," an AI that recognizes the unique gifts people bring to others.
Your Framework: Analyze their answers for themes of Agency (their power) and Communion (their connection to others).
Student's Answers:
{answers_text}

Your Mission:
Based on the student's answers, write a short, powerful paragraph in Japanese describing their "Core Compass"—their greatest strength as a friend and collaborator. This is the tool they can always rely on.

Output Requirement:
Respond with ONLY the Japanese paragraph describing their core strength."""

        # Create OpenAI client with shorter timeout for faster processing
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=8.0  # Reduced from 30 to 8 seconds
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a personality analyst. Write concise Japanese sentences about strengths."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=60  # Reduced tokens for faster response
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
        
        prompt = f"""Your Persona: You are "The Horizon Scanner," an AI that sees what's possible for people.
Your Framework: Analyze their answers for what is NOT said—gaps, curiosities, or slight hesitations that suggest an area for growth.
Student's Answers:
{answers_text}

Your Mission:
Based on their answers, identify their "Uncharted Territory"—a hidden potential or growth edge. Frame it positively as an exciting next adventure. This should feel like an insightful and encouraging challenge.

Output Requirement:
Respond with ONLY the Japanese paragraph describing their hidden potential."""

        # Create OpenAI client with shorter timeout for faster processing
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=8.0  # Reduced from 30 to 8 seconds
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a personality analyst. Write concise Japanese sentences about hidden potential."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=60  # Reduced tokens for faster response
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
        
        prompt = f"""Your Persona: You are "The Bridge Builder," an AI that knows how to start meaningful conversations.
Your Framework: Find the single most unique and interesting detail from their answers.
Student's Answers:
{answers_text}

Your Mission:
Based on their answers, write a single Japanese sentence that acts as "Your First Step"—a perfect conversation starter for others to ask them. It should be intriguing and easy for someone else to act on.

Output Requirement:
Respond with ONLY the Japanese sentence for the conversation catalyst.
Example: 「彼らの『秘密のスーパーパワー』が実際に役立った時の話を聞いてみてください。」"""

        # Create OpenAI client with shorter timeout for faster processing
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=8.0  # Reduced from 30 to 8 seconds
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a conversation expert. Write concise Japanese sentences about conversation starters."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=60  # Reduced tokens for faster response
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

