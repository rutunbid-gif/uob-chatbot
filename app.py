from flask import Flask, render_template, request, jsonify
from datetime import datetime
import re

app = Flask(__name__)

# KNOWLEDGE BASE - Built from YOUR provided UoB datasets
KNOWLEDGE_BASE = {
    "courses_undergraduate": {
        "keywords": ["undergraduate", "ug", "bachelor", "bsc", "ba", "beng", "msci", "llb", "degree", "course", "program", "study"],
        "response": """📚 **Undergraduate Courses at University of Bristol**

**Available Programs (30 courses):**

**Computer Science & Technology:**
- BSc Computer Science: 3 years, £9,250/yr (UK), £23,000/yr (Int'l)
- BSc Artificial Intelligence: 3 years, £9,250/yr (UK), £23,200/yr (Int'l)
- BSc Software Engineering: 3 years, £9,250/yr (UK), £22,500/yr (Int'l)

**Engineering:**
- BEng Mechanical Engineering: 3.5 years, £9,250/yr (UK), £24,000/yr (Int'l)
- BEng Civil Engineering: 3.5 years, £9,250/yr (UK), £23,500/yr (Int'l)
- BEng Electrical Engineering: 3.5 years, £9,250/yr (UK), £23,800/yr (Int'l)

**Sciences:**
- MSci Mathematics: 4 years, £9,250/yr (UK), £23,500/yr (Int'l)
- BSc Physics: 3 years, £9,250/yr (UK), £22,800/yr (Int'l)
- BSc Chemistry: 3 years, £9,250/yr (UK), £22,000/yr (Int'l)
- BSc Biochemistry, Biomedical Sciences, Psychology, Neuroscience

**Business & Social Sciences:**
- BSc Economics, Finance & Accounting
- BA Business Management
- LLB Law
- BA Politics, International Relations, History

**Arts & Humanities:**
- BA English Literature, Creative Writing
- BA Modern Languages (4 years)
- BA Archaeology

**Environmental:**
- BSc Geography, Environmental Science, Climate Science
- BSc Sociology, Anthropology

**Start Date:** September 21, 2026
**All courses:** Full-time, 360 credits (3yr) or 420-480 credits (longer programs)

Source: university_of_bristol_courses_dataset.pdf"""
    },
    
    "courses_postgraduate": {
        "keywords": ["postgraduate", "masters", "msc", "ma", "mba", "pgt", "pgr", "taught", "research"],
        "response": """🎓 **Postgraduate Courses at University of Bristol**

**Available Programs (30 courses):**

**Technology & Data:**
- MSc Data Science: £12,000/yr (UK), £26,500/yr (Int'l)
- MSc Artificial Intelligence: £13,000/yr (UK), £27,000/yr (Int'l)
- MSc Cyber Security: £13,000/yr (UK), £27,000/yr (Int'l)
- MSc Robotics: £15,000/yr (UK), £30,000/yr (Int'l)
- MSc Software Engineering, Bioinformatics

**Sciences:**
- MSc Physics (Research), Astrophysics, Chemistry
- MSc Materials Science, Biomedicine, Neuroscience
- MSc Psychology, Clinical Psychology

**Business:**
- MSc Finance: £17,000/yr (UK), £34,000/yr (Int'l)
- MSc Accounting: £16,000/yr (UK), £32,000/yr (Int'l)
- MBA: 2 years, £21,000/yr (UK), £36,000/yr (Int'l)
- MSc International Business, Marketing, Management

**Health & Education:**
- MSc Public Health, Nursing
- MSc Education, Digital Education

**Arts:**
- MSc English Literature, MA History
- MA Film & Television, MA Fine Art

**Environmental:**
- MSc Climate Science: £12,500/yr (UK), £26,000/yr (Int'l)

**Duration:** 1 year (180 credits) except MBA (2 years, 240 credits)
**Start Date:** September 28, 2026
**Mode:** Full-time

Source: university_of_bristol_courses_dataset.pdf"""
    },
    
    "accommodation": {
        "keywords": ["accommodation", "housing", "halls", "residence", "rent", "room", "living", "stay", "hiatt", "churchill", "wills", "goldney", "colston", "orchard"],
        "response": """🏠 **University of Bristol Accommodation**

**On-Campus Halls (2026-27):**

**Stoke Bishop Area:**
- Hiatt Baker Hall: £185-£240/week (En-suite to Studio)
  Facilities: Gym, Study Lounge
- Churchill Hall: £180-£230/week
  Facilities: Music Room, Common Room
- Wills Hall: £190-£250/week
  Facilities: Library, Games Room

**City Centre:**
- Colston Street: £200-£260/week
  Facilities: Cinema Room, Laundry
- Orchard Heights: £210-£270/week
  Facilities: 24/7 Security, Gym

**Clifton:**
- Goldney Hall: £195-£255/week
  Facilities: Gardens, Bar, Music Room

**Harbourside:**
- Riverside House: £205-£265/week
  Facilities: Waterfront, Study Pods

**Contract:** September 15, 2026 - June 15, 2027 (39 weeks)
**Room Types:** En-suite, Premium En-suite, Studio

**Accommodation Guarantee:**
First-year undergraduates and new international postgraduates guaranteed university accommodation if applied by deadline.

**Contact:**
Accommodation Office: accommodation@university.ac.uk
Phone: +44 (0)20 7946 8200
Location: Accommodation Office, Campus West
Hours: Mon-Fri 9 AM-5 PM

Sources: university_of_bristol_accommodation_dataset.pdf, Accommodation_Dataset_AI_Framework.pdf"""
    },
    
    "extensions_ec": {
        "keywords": ["extension", "exceptional circumstances", "ec", "deadline", "late", "illness", "mitigating", "appeal", "suspension"],
        "response": """📝 **Extensions & Exceptional Circumstances (EC)**

**What are they?**
- Extension: Deadline extension for coursework due to valid reasons
- EC: Significant events affecting ability to complete assessments/exams
- Suspension: Temporary withdrawal from studies

**Eligible Reasons:**
- Medical illness (physical/mental health)
- Bereavement of close relative
- Victim of crime or serious incident
- Unavoidable emergencies
- Unexpected caring responsibilities
- Verified IT failure

**NOT Eligible:**
- Minor illness (<24hrs unless affecting exam)
- Last-minute IT/printer problems
- Poor time management
- Travel disruptions (unless major)

**Required Documents:**
- GP/hospital medical certificates (dated, signed)
- Police reports (for crime)
- Death certificates (bereavement)
- Counsellor/therapist letters
- Official employer letters

**Application Process:**
- Extensions: Submit BEFORE deadline via online form
- EC: Within 5 working days of affected assessment
- Suspension: Through School office with documents

**Appeals:**
Within 10 working days of decision rejection

**Contact:**
EC Support Team: ec-support@bristol.ac.uk
Phone: +44 117 900 1234
Hours: Mon-Fri 09:30-16:30

Source: Extensions_ECs_Dissertation_Ready.pdf"""
    },
    
    "study_skills": {
        "keywords": ["study skills", "writing", "workshop", "academic", "essay", "dissertation", "referencing", "citation", "tutoring", "support"],
        "response": """📖 **Study Skills & Writing Workshops**

**Services Offered:**
- Academic writing (structure, argumentation)
- Referencing (Harvard, APA, IEEE)
- Dissertation & project planning
- Critical reading & literature synthesis
- Time management & productivity
- Exam preparation & revision
- Note-taking & memory techniques
- Presentation skills

**Workshop Formats:**
- One-to-one tutorials: 30-60 min personalized sessions
- Small-group workshops: 60-90 min (max 20 students)
- Drop-in clinics: 15-20 min quick queries
- Online modules: Self-paced e-learning
- Webinars: Live Q&A with recordings

**Key Workshops:**
- Referencing Essentials (Harvard): 90 mins, termly
- Academic Writing: Argument & Structure: 120 mins
- Dissertation Planning: 60-90 mins, on request
- English for Academic Purposes: 45 mins weekly
- Exam Revision Techniques: 60 mins, termly

**Eligibility:**
All UG, PGT, PGR students
International students supported

**Booking:**
Via Study Skills portal - book in advance
One-to-one requires 24hr cancellation notice

**Contact:**
Study Skills Team: study-skills@bristol-example.ac.uk
Phone: +44 117 900 2200
Location: Student Support Building, Room 2.14
Hours: Mon-Fri 09:30-16:30

Source: Study_Skills_Writing_Workshops_Dataset.pdf"""
    },
    
    "scholarships": {
        "keywords": ["scholarship", "funding", "bursary", "financial", "aid", "money", "think big", "great", "commonwealth", "stipend"],
        "response": """💰 **Scholarships & Funding**

**Available Funding:**

**Think Big Scholarships:**
- Undergraduate: For international UG applicants
- Postgraduate: For international PGT applicants
- Deadline: April annually
- Documents: Personal statement, transcript

**UK Home Bursary:**
- Means-tested for UK students
- Low-income eligibility
- Deadline: June annually
- Documents: Income statement, UCAS ID

**GREAT Scholarship:**
- For eligible nationalities (PGT)
- Deadline: March annually
- Documents: Passport, transcript, essay

**Commonwealth Shared Scholarship:**
- Developing Commonwealth nations
- Deadline: December (prior year)
- Documents: Proof of nationality, offer letter

**Postgraduate Research Studentship:**
- For PGR offer-holders
- Covers tuition + living stipend
- Documents: Research proposal, references

**Eligibility Criteria:**
- Home and International students
- Outstanding academic performance
- Confirmed offer to study at UoB
- Financial need (for bursaries)

**Required Documents:**
- Academic transcripts & certificates
- Personal statement
- Financial evidence (for bursaries)
- Reference letters
- Proof of nationality

**Application:**
Submit via University of Bristol Funding Portal
www.bristol.ac.uk/fees-funding/awards

**Appeals:**
Within 10 working days of decision

**Contact:**
Scholarships Office: funding-support@bristol.ac.uk
Phone: +44 (0)117 900 5678
Hours: Mon-Fri 09:00-17:00

Source: University_of_Bristol_Scholarships_and_Funding_Dataset.pdf"""
    },
    
    "sports": {
        "keywords": ["sport", "sports", "gym", "fitness", "exercise", "club", "team", "football", "rugby", "rowing", "activities", "recreation"],
        "response": """⚽ **Sports, Fitness & Activities**

**Sports Categories:**

**Performance & Elite Sport:**
Structured support for national/international athletes
Coaching, strength & conditioning, physiotherapy

**Team & Competitive Clubs:**
70+ SU-affiliated sports clubs:
Football, rowing, hockey, cricket, netball, ultimate frisbee

**Recreational & Wellbeing:**
Fitness classes: yoga, pilates, HIIT
Gym sessions, intramural leagues

**Outdoor & Adventure:**
Hiking, climbing, surfing, paddleboarding, mountain biking

**Inclusive Sport:**
Adaptive Sport sessions, Women in Sport programmes

**Membership Types:**
- Sport Membership: Access to gyms, courts, fitness classes
- Club Membership: Join SU sports clubs
- Performance Membership: By invitation, specialist support
- Activity Pass: Pay-as-you-go sessions

**Key Facilities:**
- Coombe Dingle Sports Complex: Pitches, athletics track
- Indoor Sports Centre (Tyndall Avenue): Main gym, sports hall
- Clifton Hill House Gym: Compact fitness suite
- University Pool: 25m swimming pool

**Leadership Opportunities:**
- Sport Leadership Pathway
- Bristol Plus Award (Sport Track)
- Coaching qualifications (Level 1-3)

**Wellbeing Initiatives:**
- Active Residences: Free sessions in halls
- Move Programme: Dance, meditation, yoga
- Mental Fitness Workshops

**Contact:**
Sport Enquiries: sport-enquiries@bristol.ac.uk
Phone: +44 (0)117 900 5555
Location: Indoor Sports Centre, Tyndall Avenue

SU Sport: su-sport@bristol.ac.uk
Phone: +44 (0)117 455 6100

Source: University_of_Bristol_Sports_Fitness_and_Activities_Handbook_Dataset.pdf"""
    },
    
    "contacts_departments": {
        "keywords": ["contact", "email", "phone", "department", "office", "engineering", "computer science", "business", "medicine", "law", "arts"],
        "response": """📞 **Department Contacts (Academic Year 2025-2026)**

**Department of Engineering:**
Head: Prof. James Thompson - j.thompson@university.ac.uk
Senior Tutor: Dr. Sarah Mitchell - s.mitchell@university.ac.uk
Admin: engineering.admin@university.ac.uk / +44 (0)20 7946 1235
Office Hours: Mon-Fri 9-5 PM

**Department of Computer Science:**
Head: Prof. Richard Davies - r.davies@university.ac.uk
Senior Tutor: Dr. Oliver Davies - o.davies@university.ac.uk
Admin: computerscience.admin@university.ac.uk / +44 (0)20 7946 2200

**Department of Natural Sciences:**
Head: Prof. David Armstrong - d.armstrong@university.ac.uk
Senior Tutor: Dr. Helen Wright - h.wright@university.ac.uk
Admin: science.admin@university.ac.uk / +44 (0)20 7946 4200

**Department of Social Sciences:**
Head: Prof. Michael Stevens - m.stevens@university.ac.uk
Senior Tutor: Dr. Jennifer Hayes - j.hayes@university.ac.uk
Admin: socialsciences.admin@university.ac.uk / +44 (0)20 7946 5200

**Department of Business & Management:**
Head: Prof. Marcus Foster - m.foster@university.ac.uk
Senior Tutor: Dr. Sandra Hughes - s.hughes@university.ac.uk
Admin: business.admin@university.ac.uk / +44 (0)20 7946 6200

**Department of Arts & Humanities:**
Head: Prof. Eleanor Bennett - e.bennett@university.ac.uk
Admin: arts.admin@university.ac.uk / +44 (0)20 7946 7200

**Department of Medicine & Health Sciences:**
Head: Prof. Christopher Anderson - c.anderson@university.ac.uk
Admin: medicine.admin@university.ac.uk / +44 (0)20 7946 8200

**Department of Law:**
Head: Prof. Richard Campbell - r.campbell@university.ac.uk
Admin: law.admin@university.ac.uk / +44 (0)20 7946 9200

Source: Document (1).pdf - University Student Contact Directory"""
    },
    
    "student_services": {
        "keywords": ["student services", "support", "wellbeing", "counseling", "disability", "health", "careers", "library", "registry", "finance"],
        "response": """🎓 **Central Student Support Services**

**Academic Support:**
- Academic Skills Centre: academic.skills@university.ac.uk / +44 (0)20 7946 6000
- Library Services: library@university.ac.uk / +44 (0)20 7946 6100 (24/7 term time)
- Maths Help Centre: maths.help@university.ac.uk
- Writing Centre: writing.centre@university.ac.uk

**Wellbeing & Health:**
- Wellbeing Service: wellbeing@university.ac.uk / +44 (0)20 7946 7000
- 24/7 Emergency: wellbeing.emergency@university.ac.uk / +44 (0)20 7946 7999
- Student Health Centre: health.centre@university.ac.uk / +44 (0)20 7946 7200
- Disability Service: disability.service@university.ac.uk / +44 (0)20 7946 7100
- International Support: international.support@university.ac.uk

**Financial & Administrative:**
- Student Finance: student.finance@university.ac.uk / +44 (0)20 7946 8000
- Registry Services: registry@university.ac.uk / +44 (0)20 7946 8100
- ID Card Office: id.cards@university.ac.uk
- Accommodation: accommodation@university.ac.uk / +44 (0)20 7946 8200

**Careers & Employment:**
- Careers Service: careers@university.ac.uk / +44 (0)20 7946 8300
- Work Placements: placements@university.ac.uk

**Student Life:**
- Students' Union: su.reception@university.ac.uk / +44 (0)20 7946 8400
- SU Advice Centre: su.advice@university.ac.uk
- Sports Centre: sports@university.ac.uk / +44 (0)20 7946 8500
- Campus Security (24/7): security@university.ac.uk / +44 (0)20 7946 8888
- IT Help Desk: it.helpdesk@university.ac.uk

**Exams:**
- Exams Office: exams@university.ac.uk / +44 (0)20 7946 8700
- Mitigating Circumstances: mitcircs@university.ac.uk

**EMERGENCY CONTACTS:**
- Campus Security: +44 (0)20 7946 8888 (24/7)
- Medical Emergency: 999
- Mental Health Crisis: +44 (0)20 7946 7999 (24/7)
- NHS Non-Emergency: 111

Source: Document (1).pdf - University Student Contact Directory"""
    }
}

conversations = {}

def find_best_response(user_message, conversation_id):
    """Find best response from YOUR data"""
    message = user_message.lower().strip()
    
    matches = []
    for category, data in KNOWLEDGE_BASE.items():
        score = 0
        for keyword in data["keywords"]:
            if keyword in message:
                score += 1
        if score > 0:
            matches.append((score, data["response"]))
    
    if matches:
        matches.sort(reverse=True, key=lambda x: x[0])
        return matches[0][1]
    
    return """I can help you with University of Bristol information from these datasets:

📚 Undergraduate & Postgraduate Courses
🏠 Accommodation (Halls & Housing)
📝 Extensions & Exceptional Circumstances
📖 Study Skills & Writing Workshops
💰 Scholarships & Funding
⚽ Sports, Fitness & Activities
📞 Department Contacts
🎓 Student Support Services

All responses are sourced from official UoB datasets provided for this chatbot.

What would you like to know?"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        conversations[conversation_id].append({
            'role': 'user',
            'message': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        bot_response = find_best_response(user_message, conversation_id)
        
        conversations[conversation_id].append({
            'role': 'bot',
            'message': bot_response,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'response': bot_response,
            'status': 'success'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_sources': len(KNOWLEDGE_BASE),
        'datasets': list(KNOWLEDGE_BASE.keys())
    })

if __name__ == '__main__':
    print("🚀 Starting University of Bristol Chatbot (Custom Data)")
    print("📊 Loaded datasets:")
    for key in KNOWLEDGE_BASE.keys():
        print(f"   - {key}")
    print("\n📍 Open browser: http://localhost:5000")
    print("⚠️  Press CTRL+C to stop")
    app.run(debug=True, host='0.0.0.0', port=5000)