# StudentVibe 2.0 - Product Requirements Document

## 🎯 **Vision Statement**
StudentVibe is an AI-powered group activity tool that helps teachers and club leaders create meaningful connections among students through personality-based squad formation and engaging icebreaker activities.

## 🎨 **Design System**
- **Primary Colors**: Electric Violet (#8B5CF6), Sunglow Yellow (#FFD700)
- **UI Philosophy**: Premium, animated, engaging but performance-optimized
- **Target Aesthetic**: Modern, friendly, educational with subtle animations

---

## 📱 **Core User Journey**

### **Phase 1: Session Creation (Teacher/Leader)**
1. Teacher/Leader creates account and sets up session
2. Configures session parameters (name, question set, group size)
3. Generates secure invite link for students
4. Shares link with class/club members (30-40 people max)

### **Phase 2: Student Participation (Guest Mode)**
1. **Join via Link**: Students click secure invite link (no account required)
2. **Quick Profile**: Enter name and basic info for session
3. **Answer Questions**: Complete personality questionnaire (6-12 questions)
4. **AI Analysis**: Receive personality insights in real-time

### **Phase 3: Group Formation & Activities**
1. **AI Squad Formation**: System creates optimal groups of 3-6 people
2. **Icebreaker Generation**: Custom conversation starters for each group
3. **Activity Execution**: Groups interact face-to-face using provided prompts
4. **Session Management**: Teacher monitors progress and facilitates

### **Phase 4: Optional Account Creation**
1. **Sign-up Prompt**: At session end, offer account creation for guests
2. **Data Transfer**: Move session data to permanent profile
3. **History Tracking**: Store personality insights and session experiences
4. **Future Sessions**: Faster participation with existing profile

---

## 🏗️ **Technical Architecture**

### **Frontend (Web App)**
- **Framework**: React/Next.js or Vue.js
- **Animations**: Framer Motion for premium feel
- **Responsive**: Mobile-first design for student devices
- **PWA**: Install-able web app for teachers

### **Backend (Base44)**
- **Authentication**: Base44 built-in auth for teachers/leaders only
- **Guest Sessions**: Temporary user handling without accounts
- **Database**: Optimized for sessions, guest users, and question libraries
- **AI Integration**: OpenAI API for personality analysis and squad formation

### **Security Features**
- **Secure Invite Links**: Time-limited, session-specific URLs
- **Session Isolation**: Guest data isolated per session
- **Data Retention**: Automatic cleanup of guest data after 30 days
- **Access Control**: Only session creator can manage participants

---

## 👥 **User Types & Permissions**

### **Teachers/Club Leaders (Account Required)**
- Create and manage sessions
- Generate secure invite links
- Monitor session progress and group dynamics
- Access post-session analytics and feedback
- Export session results and insights

### **Students/Members (Guest Mode Default)**
- Join sessions via secure link
- Complete questionnaires and activities
- Participate in AI-generated groups
- View their personality insights during session
- Optional: Create account to save data permanently

### **Registered Students (Optional)**
- Faster session joining with pre-filled profile
- Session history and personality evolution tracking
- Achievement collection across multiple sessions
- Enhanced privacy controls for personal data

---

## 🎮 **Achievement System (For Registered Users)**

### **Session Participation**
- **First Timer**: Complete first session
- **Question Master**: Answer all questions in a session
- **Group Harmony**: High group satisfaction rating
- **Conversation Starter**: Successfully use icebreakers

### **Personality Growth**
- **Self Discovery**: Complete personality analysis
- **Adaptability**: Participate in different group types
- **Leadership**: Take initiative in group activities
- **Connector**: Help facilitate group discussions

---

## 🔒 **Privacy & Safety Features**

### **Guest User Protection**
- No permanent data storage without consent
- Session-only visibility of personal information
- Automatic data deletion after session expiry
- No cross-session data sharing for guests

### **Teacher/Leader Controls**
- Session monitoring dashboard
- Ability to remove disruptive participants
- Export/import class rosters for easier setup
- Privacy-compliant data handling

### **Safety Measures**
- Age-appropriate content filtering
- Community guidelines for classroom use
- Report functionality for inappropriate behavior
- Emergency session termination controls

---

## 📊 **Question Library System**

### **Question Sets by Purpose**
1. **General Friendship**: Basic personality and interests (Default)
2. **Study Groups**: Academic collaboration and learning styles
3. **Creative Projects**: Artistic collaboration and creativity
4. **Team Building**: Leadership and collaboration skills
5. **Cultural Exchange**: Background and traditions sharing
6. **Icebreaker Lite**: Quick 3-question version for short sessions

### **Scalability for Group Sizes**
- **Small Groups** (10-15 people): 6-8 questions, 15-20 minutes
- **Large Classes** (30-40 people): 4-6 questions, 10-15 minutes
- **Quick Activities**: 3 essential questions, 5-10 minutes

---

## 🎨 **Premium UI/UX Features**

### **Session Flow Animations**
- **Joining**: Smooth onboarding for guests via invite link
- **Questionnaire**: Card-flip animations between questions
- **AI Processing**: Engaging "personality analysis" loading states
- **Group Reveal**: Dramatic group formation animations
- **Results**: Celebration animations for completed activities

### **Visual Question Design**
- **Icon-based**: Visual representations for each question
- **Progress Indicators**: Clear session timeline and completion status
- **Interactive Elements**: Swipe, tap, and drag interactions
- **Accessibility**: High contrast, readable fonts, screen reader support

---

## 📈 **Success Metrics**

### **Session Quality**
- Session completion rate (start to finish)
- Group satisfaction ratings
- Teacher/leader retention
- Icebreaker engagement effectiveness

### **User Experience**
- Time to complete questionnaire
- Guest-to-registered user conversion rate
- Session replay rate (teachers using multiple times)
- Technical performance (loading times, error rates)

### **Educational Impact**
- Student engagement feedback
- Teacher satisfaction surveys
- Classroom integration success
- Word-of-mouth referrals to other educators

---

## 🚀 **MVP Feature Scope**

### **Phase 1 (Core Classroom Tool)**
✅ Teacher account creation and session setup
✅ Secure invite link generation
✅ Guest user questionnaire interface
✅ AI personality analysis and squad formation
✅ Basic icebreaker generation
✅ Session management dashboard

### **Phase 2 (Enhanced Experience)**
⏳ Multiple question libraries for different purposes
⏳ Advanced group formation algorithms
⏳ Premium animations and micro-interactions
⏳ Guest-to-account conversion flow
⏳ Session analytics and reporting

### **Phase 3 (Advanced Features)**
⏳ n8n webhook integration for sophisticated AI
⏳ Achievement system for registered users
⏳ Advanced session management tools
⏳ Integration with learning management systems
⏳ Bulk user import/export capabilities

---

## 🎯 **Target Audience**

### **Primary Users (Teachers/Leaders)**
- **Age**: 25-55
- **Context**: Classroom teachers, club advisors, workshop facilitators
- **Goals**: Improve student engagement, facilitate group work, break ice in new classes
- **Pain Points**: Difficulty forming balanced groups, awkward group dynamics

### **Secondary Users (Students)**
- **Age**: 16-24 (high school to college)
- **Context**: Classroom activities, club meetings, orientation sessions
- **Goals**: Meet new people, participate in engaging activities, understand themselves better
- **Tech Comfort**: High, mobile-native generation

### **Use Cases**
- **New Class Icebreakers**: First day of semester group formation
- **Project Team Assignment**: AI-optimized project groups
- **Club Activities**: Youth group bonding exercises
- **Workshop Sessions**: Professional development team building
- **Orientation Programs**: New student integration activities

---

## 💡 **Differentiation Strategy**

### **vs. Traditional Icebreakers**
- AI-powered personality matching for better group dynamics
- Instant, engaging digital experience
- Data-driven insights for educators
- Scalable to large groups (30-40 people)

### **vs. Survey Tools**
- Real-time AI analysis and group formation
- Built-in icebreaker generation
- Educational focus with privacy protection
- Engaging, game-like interface for students

### **vs. Team Building Apps**
- Designed specifically for educational settings
- Guest-friendly (no forced account creation)
- Age-appropriate content and safety features
- Teacher/leader control and oversight

---

## 🛡️ **Risk Mitigation**

### **Technical Risks**
- **AI Accuracy**: Diverse training data, educator feedback integration
- **Scalability**: Performance optimization for 40-user sessions
- **Security**: Secure link generation, session isolation

### **Educational Risks**
- **Privacy Compliance**: FERPA/GDPR compliant, minimal data collection
- **Inappropriate Content**: Educator oversight, content filtering
- **Technical Barriers**: Simple interface, mobile-optimized

### **Adoption Risks**
- **Teacher Training**: Simple onboarding, video tutorials
- **Student Engagement**: Gamified experience, quick participation
- **Technical Support**: Comprehensive help documentation, chat support

---

## 🔗 **Secure Invite Link Implementation**

### **Link Generation**
- **Format**: `studentvibe.app/join/[SESSION_ID]/[SECURE_TOKEN]`
- **Security**: Time-limited (24-48 hours), single-use per student
- **Customization**: Optional custom session names for easy sharing

### **Access Control**
- **Session Capacity**: Configurable max participants (default 40)
- **Entry Requirements**: Optional passcode for extra security
- **Status Tracking**: Real-time participant count for teachers
- **Link Management**: Ability to regenerate or disable links

---

*This PRD serves as the foundation for building StudentVibe 2.0 as a classroom/club activity tool focused on meaningful group formation and face-to-face interactions.*
