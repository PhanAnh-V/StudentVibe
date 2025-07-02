import json
import os
from openai import OpenAI
import logging
import httpx

# Initialize OpenAI client with timeout settings
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    timeout=httpx.Timeout(30.0, read=30.0, write=30.0, connect=30.0)
)

def generate_interest_recommendations(vibes_text, archetype=None):
    """
    Generate personalized interest recommendations based on student's vibes using AI
    """
    try:
        prompt = f"""
        Analyze the following student's interests and personality described in their own words:
        
        "{vibes_text}"
        
        {f"They have been identified as a '{archetype}' personality type." if archetype else ""}
        
        Based on this information, provide 5 personalized activity/interest recommendations that would:
        1. Complement their existing interests
        2. Help them explore new areas they might enjoy
        3. Foster personal growth and social connections
        4. Be age-appropriate for students
        
        Format your response as a JSON object with this structure:
        {{
            "recommendations": [
                {{
                    "activity": "Activity Name",
                    "reason": "Brief explanation why this fits their interests",
                    "category": "One of: Creative, Social, Academic, Physical, Technical, Cultural"
                }}
            ],
            "growth_areas": [
                "Area 1: Brief suggestion for expanding their interests",
                "Area 2: Brief suggestion for expanding their interests"
            ],
            "connection_opportunities": "Brief suggestion for how they could connect with like-minded peers"
        }}
        
        Keep recommendations specific, actionable, and encouraging.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educational counselor who specializes in understanding student interests and recommending activities that promote personal growth, learning, and social connection. Provide thoughtful, personalized recommendations based on student input."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=800,
            timeout=20
        )
        
        content = response.choices[0].message.content
        if not content:
            raise Exception("Empty response from OpenAI")
        result = json.loads(content)
        logging.info(f"Generated AI recommendations for vibes: {vibes_text[:50]}...")
        return result
        
    except Exception as e:
        logging.error(f"Error generating recommendations: {str(e)}")
        return get_fallback_recommendations(vibes_text, archetype)

def get_fallback_recommendations(vibes_text, archetype=None):
    """
    Provide basic recommendations when AI is unavailable
    """
    vibes_lower = vibes_text.lower()
    
    # Basic keyword-based recommendations
    recommendations = []
    
    if any(word in vibes_lower for word in ['game', 'gaming', 'video']):
        recommendations.append({
            "activity": "Game Development Club",
            "reason": "Your gaming interest could lead to creating your own games",
            "category": "Technical"
        })
    
    if any(word in vibes_lower for word in ['music', 'song', 'singing']):
        recommendations.append({
            "activity": "School Band or Choir",
            "reason": "Perfect way to develop your musical talents with others",
            "category": "Creative"
        })
    
    if any(word in vibes_lower for word in ['art', 'drawing', 'creative']):
        recommendations.append({
            "activity": "Digital Art Workshop",
            "reason": "Combine creativity with modern technology",
            "category": "Creative"
        })
    
    # Add generic recommendations to reach 5
    generic_recs = [
        {"activity": "Debate Club", "reason": "Develop communication and critical thinking", "category": "Academic"},
        {"activity": "Volunteer Club", "reason": "Make a positive impact while meeting new people", "category": "Social"},
        {"activity": "Photography Club", "reason": "Capture and share your unique perspective", "category": "Creative"},
        {"activity": "Coding Bootcamp", "reason": "Learn valuable technical skills for the future", "category": "Technical"},
        {"activity": "Book Club", "reason": "Explore new ideas and discuss with peers", "category": "Academic"}
    ]
    
    # Fill remaining slots
    while len(recommendations) < 5:
        for rec in generic_recs:
            if rec not in recommendations and len(recommendations) < 5:
                recommendations.append(rec)
    
    return {
        "recommendations": recommendations[:5],
        "growth_areas": [
            "Explore activities that combine your interests with new skills",
            "Consider joining clubs where you can meet people with similar passions"
        ],
        "connection_opportunities": "Look for school clubs or community groups related to your interests"
    }

def analyze_compatibility_with_ai(student1_vibes, student2_vibes):
    """
    Use AI to analyze compatibility between two students for squad formation
    """
    try:
        prompt = f"""
        Analyze the compatibility between these two students based on their interests:
        
        Student 1: "{student1_vibes}"
        Student 2: "{student2_vibes}"
        
        Provide a compatibility analysis in JSON format:
        {{
            "compatibility_score": 0.85,
            "shared_interests": ["interest1", "interest2"],
            "complementary_aspects": "How they complement each other",
            "potential_conflicts": "Any potential areas of difference",
            "collaboration_potential": "How well they might work together"
        }}
        
        Score should be between 0.0 and 1.0, where 1.0 is perfect compatibility.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in student psychology and group dynamics. Analyze compatibility between students for optimal team formation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=400
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logging.error(f"Error analyzing compatibility: {str(e)}")
        return {
            "compatibility_score": 0.5,
            "shared_interests": ["general interests"],
            "complementary_aspects": "Both students bring unique perspectives",
            "potential_conflicts": "None identified",
            "collaboration_potential": "Good potential for collaborative projects"
        }

def enhance_archetype_with_ai(vibes_text):
    """
    Use AI to enhance archetype detection with more nuanced analysis
    """
    try:
        prompt = f"""
        Analyze this student's personality and interests to determine their learning archetype:
        
        "{vibes_text}"
        
        Provide analysis in JSON format:
        {{
            "primary_archetype": "Most fitting archetype name",
            "secondary_traits": ["trait1", "trait2", "trait3"],
            "learning_style": "How they prefer to learn and engage",
            "strengths": ["strength1", "strength2"],
            "growth_opportunities": ["area1", "area2"],
            "ideal_group_role": "What role they'd excel at in group work"
        }}
        
        Choose primary archetype from: Gaming Guru, Music Maestro, Creative Artist, Adventure Seeker, 
        Sports Champion, Tech Wizard, Bookworm Scholar, Foodie Explorer, Movie Buff, Social Connector, 
        Nature Enthusiast, Mystery Vibe
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an educational psychologist specializing in student personality assessment and learning style identification."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=400
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logging.error(f"Error enhancing archetype: {str(e)}")
        return None