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
        
        prompt = f"""You are a creative team leader and social dynamics expert who specializes in forming amazing student squads.

Below are student responses to 6 questions about their interests, passions, and personalities:

{students_text}

Your mission:
1. Group these students into squads of 3-4 members each
2. Create fun, memorable squad names in JAPANESE that reflect their collective identity
3. Find the common threads that will bond each group together
4. Balance shared interests with complementary strengths
5. Think like a camp counselor - make it exciting and meaningful!

Respond with a JSON object in this exact format:
{{
    "squads": [
        {{
            "squad_name": "Creative Japanese name (like 'アドベンチャーチーム' or 'クリエイティブスピリッツ')",
            "member_ids": [list of student IDs],
            "shared_interests": "Brief, inspiring summary in Japanese of what bonds this group together"
        }}
    ]
}}

Requirements:
- Every student must be assigned to exactly one squad
- Squad names MUST be in Japanese and engaging
- Shared interests MUST be in Japanese and show why these students belong together
- Use natural, exciting Japanese that students would be proud to be part of

Make each squad feel like a special club they'd be excited to join!"""

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


def generate_personality_signature(student_answers):
    """
    Generate a comprehensive personality signature with archetype and three insights
    """
    try:
        # Prepare the student answers text
        answers_text = ""
        for i in range(1, 7):
            question_key = f'question{i}'
            if question_key in student_answers:
                answers_text += f"Question {i}: {student_answers[question_key]}\n"
        
        prompt = f"""Analyze the student's 6 answers to generate a "Personality Signature."
The signature should be insightful, positive, and inspiring.
All text must be in natural, engaging Japanese.

Student answers:
{answers_text}

Respond with a JSON object in this exact format:
{{
  "archetype": "A creative Japanese nickname that captures their core essence.",
  "core_strength": "A short paragraph describing their most powerful quality as a friend.",
  "hidden_potential": "An inspiring insight about a potential they might not see in themselves.",
  "conversation_catalyst": "A fun fact derived from their answers to start a conversation."
}}

Requirements:
- archetype: 2-6 Japanese words (like 好奇心旺盛な探検家, 静かな語り部)
- core_strength: 1-2 sentences about their best friendship quality
- hidden_potential: 1-2 sentences about untapped abilities
- conversation_catalyst: 1-2 sentences with a conversation starter based on their interests
- ALL text must be in Japanese
- Make it personal and specific to their answers"""

        # Create OpenAI client with timeout
        timeout_client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            timeout=30.0  # 30 second timeout for personality signature
        )
        
        response = timeout_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a skilled personality analyst who creates insightful Japanese personality profiles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        if response.choices[0].message.content:
            result = json.loads(response.choices[0].message.content)
            logging.info(f"Generated personality signature: {result}")
            return result
        else:
            logging.warning("Empty response from AI personality signature generation")
            return {
                "archetype": "個性豊かな学生",
                "core_strength": "創造的な思考力と独自の視点を持っています。",
                "hidden_potential": "リーダーシップの才能が眠っている可能性があります。",
                "conversation_catalyst": "趣味や興味のあることについて話すと、とても輝いて見えます。"
            }
            
    except Exception as e:
        logging.error(f"Error generating personality signature: {str(e)}")
        return {
            "archetype": "個性豊かな学生",
            "core_strength": "創造的な思考力と独自の視点を持っています。",
            "hidden_potential": "リーダーシップの才能が眠っている可能性があります。",
            "conversation_catalyst": "趣味や興味のあることについて話すと、とても輝いて見えます。"
        }

