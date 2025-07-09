import os
import logging
from redis import Redis
from rq import Queue
from openai import OpenAI

# Set up the connection to Redis
try:
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        redis_conn = Redis.from_url(redis_url)
    else:
        # Use a simple Redis connection as fallback
        redis_conn = Redis(host='localhost', port=6379, db=0)
    q = Queue(connection=redis_conn)
except Exception as e:
    logging.error(f"Redis connection failed: {str(e)}")
    # Create a mock queue that will work for development without Redis
    class MockQueue:
        def enqueue(self, *args, **kwargs):
            logging.warning("Mock queue used - job not actually enqueued")
            return None
    q = MockQueue()

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


def process_student_answers(student_id, student_language):
    """
    Process student answers in the background: translate to Japanese and generate personality signatures
    """
    from app import app
    from models import Student, db
    
    with app.app_context():
        student = Student.query.get(student_id)
        if not student:
            logging.error(f"Could not find student with ID {student_id} to process.")
            return
            
        logging.info(f"Processing answers for student {student_id} ({student.name}) in language: {student_language}")
        
        # Handle Japanese translations based on student's language choice
        if student_language == 'ja':
            # Student chose Japanese - no translation needed, use original answers
            student.question1_jp = student.question1
            student.question2_jp = student.question2
            student.question3_jp = student.question3
            student.question4_jp = student.question4
            student.question5_jp = student.question5
            student.question6_jp = student.question6
            logging.info(f"Japanese detected for student {student_id}, using original answers")
        else:
            # Student chose other language - translate to Japanese
            try:
                student.question1_jp = translate_to_japanese(student.question1)
                student.question2_jp = translate_to_japanese(student.question2)
                student.question3_jp = translate_to_japanese(student.question3)
                student.question4_jp = translate_to_japanese(student.question4)
                student.question5_jp = translate_to_japanese(student.question5)
                student.question6_jp = translate_to_japanese(student.question6)
                logging.info(f"Successfully translated answers for student {student_id}")
            except Exception as e:
                logging.error(f"Translation failed for student {student_id}: {str(e)}")
                # Set empty translations if translation fails
                student.question1_jp = ""
                student.question2_jp = ""
                student.question3_jp = ""
                student.question4_jp = ""
                student.question5_jp = ""
                student.question6_jp = ""
        
        # Generate personality signatures using AI
        try:
            from openai_integration import generate_archetype, generate_core_strength, generate_hidden_potential, generate_conversation_catalyst
            
            # Prepare student answers for AI analysis
            student_answers = {
                'question1': student.question1,
                'question2': student.question2,
                'question3': student.question3,
                'question4': student.question4,
                'question5': student.question5,
                'question6': student.question6
            }
            
            # Generate personality signatures with fallback values
            try:
                student.archetype = generate_archetype(student_answers)
                logging.info(f"Generated archetype for student {student_id}")
            except Exception as e:
                logging.error(f"Archetype generation failed for student {student_id}: {str(e)}")
                student.archetype = "個性豊かな学生"
                
            try:
                student.core_strength = generate_core_strength(student_answers)
                logging.info(f"Generated core strength for student {student_id}")
            except Exception as e:
                logging.error(f"Core strength generation failed for student {student_id}: {str(e)}")
                student.core_strength = "創造的な思考力と独自の視点を持っています。"
                
            try:
                student.hidden_potential = generate_hidden_potential(student_answers)
                logging.info(f"Generated hidden potential for student {student_id}")
            except Exception as e:
                logging.error(f"Hidden potential generation failed for student {student_id}: {str(e)}")
                student.hidden_potential = "リーダーシップの才能が眠っている可能性があります。"
                
            try:
                student.conversation_catalyst = generate_conversation_catalyst(student_answers)
                logging.info(f"Generated conversation catalyst for student {student_id}")
            except Exception as e:
                logging.error(f"Conversation catalyst generation failed for student {student_id}: {str(e)}")
                student.conversation_catalyst = "趣味や興味のあることについて話すと、とても輝いて見えます。"
                
        except Exception as e:
            logging.error(f"Error importing AI functions for student {student_id}: {str(e)}")
            # Set fallback values if AI functions can't be imported
            student.archetype = "個性豊かな学生"
            student.core_strength = "創造的な思考力と独自の視点を持っています。"
            student.hidden_potential = "リーダーシップの才能が眠っている可能性があります。"
            student.conversation_catalyst = "趣味や興味のあることについて話すと、とても輝いて見えます。"
        
        # Save all changes to database
        try:
            db.session.commit()
            logging.info(f"Successfully processed and saved all data for student {student_id} ({student.name})")
        except Exception as e:
            logging.error(f"Database error saving processed data for student {student_id}: {str(e)}")
            db.session.rollback()
            raise