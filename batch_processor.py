#!/usr/bin/env python3
"""
Batch processor for student translations and personality analysis
This runs as a separate process to avoid threading issues with database connections
"""

import os
import sys
import time
import logging
from datetime import datetime
from app import app, db
from models import Student
from tasks import translate_to_japanese
from openai_integration import generate_archetype, generate_core_strength, generate_hidden_potential, generate_conversation_catalyst

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_processor.log'),
        logging.StreamHandler()
    ]
)

def process_pending_students():
    """Process all students who need translation and personality analysis"""
    with app.app_context():
        # Find students who need processing
        pending_students = Student.query.filter(Student.question1_jp.is_(None)).all()
        
        if not pending_students:
            logging.info("No pending students found for processing")
            return
            
        logging.info(f"Found {len(pending_students)} students needing processing")
        
        for student in pending_students:
            try:
                logging.info(f"Processing student {student.id}: {student.name}")
                
                # Process translations
                translations = []
                questions = [student.question1, student.question2, student.question3, 
                           student.question4, student.question5, student.question6]
                
                for i, question in enumerate(questions, 1):
                    try:
                        translation = translate_to_japanese(question)
                        translations.append(translation)
                        logging.info(f"Question {i} translated for student {student.id}")
                        time.sleep(0.2)  # Rate limiting
                    except Exception as e:
                        logging.error(f"Translation failed for question {i} of student {student.id}: {e}")
                        translations.append("翻訳エラー")
                
                # Update student with translations
                student.question1_jp = translations[0]
                student.question2_jp = translations[1]
                student.question3_jp = translations[2]
                student.question4_jp = translations[3]
                student.question5_jp = translations[4]
                student.question6_jp = translations[5]
                
                # Generate personality analysis
                student_answers = {
                    'question1': student.question1,
                    'question2': student.question2,
                    'question3': student.question3,
                    'question4': student.question4,
                    'question5': student.question5,
                    'question6': student.question6
                }
                
                try:
                    student.archetype = generate_archetype(student_answers)
                    time.sleep(0.2)
                except Exception as e:
                    logging.error(f"Archetype generation failed for student {student.id}: {e}")
                    student.archetype = "個性豊かな学生"
                
                try:
                    student.core_strength = generate_core_strength(student_answers)
                    time.sleep(0.2)
                except Exception as e:
                    logging.error(f"Core strength generation failed for student {student.id}: {e}")
                    student.core_strength = "創造的な思考力と独自の視点を持っています。"
                
                try:
                    student.hidden_potential = generate_hidden_potential(student_answers)
                    time.sleep(0.2)
                except Exception as e:
                    logging.error(f"Hidden potential generation failed for student {student.id}: {e}")
                    student.hidden_potential = "リーダーシップの才能が眠っている可能性があります。"
                
                try:
                    student.conversation_catalyst = generate_conversation_catalyst(student_answers)
                except Exception as e:
                    logging.error(f"Conversation catalyst generation failed for student {student.id}: {e}")
                    student.conversation_catalyst = "趣味や興味のあることについて話すと、とても輝いて見えます。"
                
                # Save to database
                try:
                    db.session.commit()
                    logging.info(f"✅ Successfully processed student {student.id}: {student.name}")
                except Exception as e:
                    logging.error(f"Database save failed for student {student.id}: {e}")
                    db.session.rollback()
                    
                # Brief pause between students
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Critical error processing student {student.id}: {e}")
                db.session.rollback()
                continue

def main():
    """Main function to run batch processing"""
    logging.info("Starting batch processor for student translations")
    
    try:
        process_pending_students()
        logging.info("Batch processing completed successfully")
    except Exception as e:
        logging.error(f"Batch processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()