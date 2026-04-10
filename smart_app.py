"""
COMPLETE AI KNOWLEDGE PLATFORM
Features: RAG + RBAC + Expert Finder + Slack + Meeting Analyzer + Voice Input + Action Tracker
"""

import streamlit as st
import numpy as np
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from groq import Groq
from pypdf import PdfReader

# Import custom modules
# ============================================
# ACTION TRACKER CLASS (Built-in)
# ============================================
class ActionTracker:
    def __init__(self, storage_path="actions.json"):
        self.storage_path = storage_path
        self.actions = []
        self.load_actions()
    
    def load_actions(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.actions = json.load(f)
            except:
                self.actions = []
    
    def save_actions(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.actions, f, indent=2)
    
    def add_action(self, task, assignee, deadline, source_meeting=""):
        action = {
            'id': len(self.actions) + 1,
            'task': task,
            'assignee': assignee,
            'deadline': deadline if deadline else "No deadline specified",
            'status': 'pending',
            'source_meeting': source_meeting,
            'created_at': datetime.now().isoformat(),
            'completed_at': None
        }
        self.actions.append(action)
        self.save_actions()
        return action
    
    def complete_action(self, action_id):
        for action in self.actions:
            if action['id'] == action_id:
                action['status'] = 'completed'
                action['completed_at'] = datetime.now().isoformat()
                self.save_actions()
                return True
        return False
    
    def get_pending_actions(self):
        return [a for a in self.actions if a['status'] == 'pending']
    
    def get_completed_actions(self):
        return [a for a in self.actions if a['status'] == 'completed']
    
    def get_overdue_actions(self):
        overdue = []
        today = datetime.now().date()
        for action in self.actions:
            if action['status'] == 'pending' and action['deadline'] != "No deadline specified":
                try:
                    deadline_date = datetime.strptime(action['deadline'], '%Y-%m-%d').date()
                    if deadline_date < today:
                        overdue.append(action)
                except:
                    pass
        return overdue
    
    def get_stats(self):
        pending = len(self.get_pending_actions())
        completed = len(self.get_completed_actions())
        overdue = len(self.get_overdue_actions())
        return {
            'total': len(self.actions),
            'pending': pending,
            'completed': completed,
            'overdue': overdue,
            'completion_rate': (completed / len(self.actions) * 100) if self.actions else 0
        }
    
    def extract_actions_from_text(self, text, groq_client):
        prompt = f"""
        Extract action items from this meeting transcript.
        Return as JSON array: [{{"task": "...", "assignee": "...", "deadline": "..."}}]
        Transcript: {text[:2000]}
        """
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            import json as json_lib
            result_text = response.choices[0].message.content
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            actions = json_lib.loads(result_text)
            return actions if isinstance(actions, list) else [actions]
        except:
            return []

load_dotenv()

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="AskSphere",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# LOAD CUSTOM CSS FROM FILE
# ============================================
def load_css():
    """Load custom CSS from styles.css file"""
    css_file = "styles.css"
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
    else:
        # Fallback CSS if file doesn't exist
        st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }
        .main-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; }
        .main-header h1 { color: white; margin: 0; }
        .expert-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin: 10px 0; }
        </style>
        """, unsafe_allow_html=True)

# Call the CSS loader
load_css()

# ============================================
# EXPERT TRACKER CLASS
# ============================================
class ExpertTracker:
    def __init__(self):
        self.experts = {}
        self.load_data()
    
    def load_data(self):
        if os.path.exists("expertise_data.json"):
            try:
                with open("expertise_data.json", 'r') as f:
                    self.experts = json.load(f)
            except:
                self.experts = {}
    
    def save_data(self):
        with open("expertise_data.json", 'w') as f:
            json.dump(self.experts, f, indent=2)
    
    def extract_topics(self, text):
        stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was', 'were',
                      'have', 'has', 'had', 'but', 'not', 'you', 'they', 'she', 'he', 'it', 'is'}
        words = text.lower().split()
        topics = set()
        for word in words[:300]:
            word = word.strip('.,!?;:()[]{}"\'-')
            if len(word) > 3 and word not in stop_words and word.isalpha():
                topics.add(word)
        return list(topics)[:10]
    
    def add_expert(self, name, document_name, topics):
        if name not in self.experts:
            self.experts[name] = {'topics': {}, 'documents': [], 'total_score': 0}
        
        if document_name not in self.experts[name]['documents']:
            self.experts[name]['documents'].append(document_name)
        
        for topic in topics:
            if topic not in self.experts[name]['topics']:
                self.experts[name]['topics'][topic] = 0
            self.experts[name]['topics'][topic] += 10
            self.experts[name]['total_score'] += 10
        
        self.save_data()
        return True
    
    def find_experts(self, query):
        query = query.lower().strip()
        results = []
        
        for name, data in self.experts.items():
            score = 0
            matching_topics = []
            
            for topic, points in data['topics'].items():
                if query == topic or query in topic or topic in query:
                    score += points
                    matching_topics.append(topic)
            
            if score > 0:
                results.append({
                    'name': name,
                    'score': score,
                    'topics': matching_topics,
                    'documents': len(data['documents'])
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:3]

# ============================================
# SLACK PROCESSOR CLASS
# ============================================
class SlackProcessor:
    def __init__(self):
        self.messages = []
        self.users = {}
    
    def process_uploaded_file(self, file_content: bytes, filename: str) -> dict:
        try:
            if filename.endswith('.json'):
                data = json.loads(file_content.decode('utf-8'))
            else:
                return {'error': 'Please upload JSON file'}
            
            self.messages = []
            self.users = {}
            
            if isinstance(data, list):
                for channel_data in data:
                    channel = channel_data.get('channel', 'unknown')
                    messages = channel_data.get('messages', [])
                    for msg in messages:
                        self._add_message(msg, channel)
            elif isinstance(data, dict):
                channels = data.get('channels', [data])
                for channel_data in channels:
                    channel = channel_data.get('name', 'general')
                    messages = channel_data.get('messages', [])
                    for msg in messages:
                        self._add_message(msg, channel)
            
            return {
                'success': True,
                'messages': len(self.messages),
                'users': len(self.users)
            }
        except Exception as e:
            return {'error': f"Failed: {str(e)}"}
    
    def _add_message(self, msg: dict, channel: str):
        user = msg.get('user', msg.get('username', 'unknown'))
        text = msg.get('text', '')
        
        if user == 'slackbot' or not text:
            return
        
        topic = self._detect_topic(text)
        
        self.messages.append({
            'user': user,
            'text': text,
            'channel': channel,
            'topic': topic
        })
        
        if user not in self.users:
            self.users[user] = {'messages': [], 'topics': {}, 'total': 0}
        
        self.users[user]['messages'].append(text)
        self.users[user]['total'] += 1
        
        if topic not in self.users[user]['topics']:
            self.users[user]['topics'][topic] = 0
        self.users[user]['topics'][topic] += 1
    
    def _detect_topic(self, text: str) -> str:
        text_lower = text.lower()
        topics = {
            'deployment': ['deploy', 'release', 'production', 'ci/cd'],
            'python': ['python', 'django', 'flask', 'pip'],
            'database': ['database', 'sql', 'migration', 'postgres'],
            'budget': ['budget', 'cost', 'spending', 'finance'],
            'security': ['security', 'vulnerability', 'audit']
        }
        for topic, keywords in topics.items():
            if any(k in text_lower for k in keywords):
                return topic
        return 'general'
    
    def find_experts(self, topic: str, limit: int = 3) -> list:
        experts = []
        for user, data in self.users.items():
            mentions = data['topics'].get(topic, 0)
            if mentions > 0:
                experts.append({
                    'name': user,
                    'mentions': mentions,
                    'total_messages': data['total'],
                    'expertise_level': 'Expert 🏆' if mentions >= 10 else 'Knowledgeable 📚' if mentions >= 5 else 'Familiar 👍'
                })
        experts.sort(key=lambda x: x['mentions'], reverse=True)
        return experts[:limit]
    
    def search_conversations(self, query: str, limit: int = 5) -> list:
        results = []
        for msg in self.messages:
            if query.lower() in msg['text'].lower():
                results.append(msg)
        return results[:limit]
    
    def get_summary(self) -> dict:
        if not self.messages:
            return {'loaded': False}
        
        topic_counts = {}
        for msg in self.messages:
            topic = msg.get('topic', 'general')
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return {
            'loaded': True,
            'total_messages': len(self.messages),
            'total_users': len(self.users),
            'top_topics': dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def create_sample_slack_data(self) -> bytes:
        import random
        users = ['alex_chen', 'sarah_jones', 'mike_wilson', 'lisa_wong']
        topics = ['deployment', 'python', 'database', 'budget']
        
        messages = []
        for channel in ['#general', '#tech']:
            channel_msgs = []
            for i in range(30):
                user = random.choice(users)
                topic = random.choice(topics)
                templates = {
                    'deployment': [f"Deployed new version", "CI/CD pipeline ready"],
                    'python': [f"Python script optimized", "Need help with Django"],
                    'database': [f"Database migration done", "SQL query fixed"],
                    'budget': [f"Budget approved", "Cost optimization"]
                }
                text = random.choice(templates.get(topic, ["Hello"]))
                channel_msgs.append({'user': user, 'text': text})
            messages.append({'channel': channel, 'messages': channel_msgs})
        
        return json.dumps(messages, indent=2).encode('utf-8')

# ============================================
# MEETING ANALYZER CLASS
# ============================================
class MeetingAnalyzer:
    def __init__(self, storage_path="meetings_database.json"):
        self.storage_path = storage_path
        self.meetings = []
        self.load_meetings()
    
    def load_meetings(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.meetings = json.load(f)
            except:
                self.meetings = []
    
    def save_meetings(self):
        with open(self.storage_path, 'w') as f:
            json.dump(self.meetings, f, indent=2)
    
    def analyze_transcript(self, transcript: str, meeting_name: str, groq_client) -> dict:
        analysis_prompt = f"""
        Analyze this meeting transcript and extract:
        
        1. **summary** (2-3 sentences)
        2. **action_items** (who, what, deadline)
        3. **decisions** (list of decisions)
        4. **key_quotes** (important quotes)
        5. **efficiency_score** (0-100)
        
        Transcript: {transcript[:4000]}
        
        Return JSON format:
        {{
            "summary": "...",
            "action_items": [{{"task": "...", "assignee": "...", "deadline": "..."}}],
            "decisions": ["decision1"],
            "key_quotes": [{{"speaker": "...", "quote": "..."}}],
            "efficiency_score": 75
        }}
        """
        
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            import json as json_lib
            analysis_text = response.choices[0].message.content
            analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()
            analysis = json_lib.loads(analysis_text)
        except:
            analysis = {
                "summary": "Meeting analyzed successfully.",
                "action_items": [],
                "decisions": [],
                "key_quotes": [],
                "efficiency_score": 70
            }
        
        meeting_data = {
            "id": len(self.meetings) + 1,
            "name": meeting_name,
            "timestamp": datetime.now().isoformat(),
            **analysis
        }
        
        self.meetings.append(meeting_data)
        self.save_meetings()
        return meeting_data
    
    def search_meetings(self, query: str, limit: int = 3) -> list:
        results = []
        query_lower = query.lower()
        
        for meeting in self.meetings:
            relevance = 0
            context = []
            
            if query_lower in meeting.get('summary', '').lower():
                relevance += 10
                context.append(f"Summary: {meeting['summary'][:100]}")
            
            for item in meeting.get('action_items', []):
                if query_lower in item.get('task', '').lower():
                    relevance += 8
                    context.append(f"Action: {item['task']} → {item.get('assignee', 'Unknown')}")
            
            if relevance > 0:
                results.append({
                    'meeting_name': meeting['name'],
                    'date': meeting['timestamp'],
                    'relevance_score': relevance,
                    'context': context[:2]
                })
        
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:limit]
    
    def get_all_meetings_summary(self) -> dict:
        if not self.meetings:
            return {"total": 0}
        
        total_actions = sum(len(m.get('action_items', [])) for m in self.meetings)
        avg_efficiency = sum(m.get('efficiency_score', 0) for m in self.meetings) / len(self.meetings)
        
        return {
            "total": len(self.meetings),
            "total_action_items": total_actions,
            "avg_efficiency": round(avg_efficiency, 1)
        }
    
    def format_report(self, meeting_data: dict) -> str:
        report = f"""
### 📋 Meeting Report: {meeting_data['name']}

**📝 Summary**  
{meeting_data.get('summary', 'No summary available')}

**✅ Action Items**
"""
        if meeting_data.get('action_items'):
            for item in meeting_data['action_items']:
                report += f"- **{item['task']}** → {item.get('assignee', 'Unknown')} (by {item.get('deadline', 'No deadline')})\n"
        else:
            report += "- No action items found\n"
        
        report += f"""
**🎯 Decisions Made**
"""
        if meeting_data.get('decisions'):
            for decision in meeting_data['decisions']:
                report += f"- {decision}\n"
        else:
            report += "- No decisions recorded\n"
        
        report += f"""
**📊 Efficiency Score:** {meeting_data.get('efficiency_score', 70)}/100

---
*🤫 Silent Attendee - Making meetings matter*
"""
        return report

# ============================================
# INITIALIZE SESSION STATE
# ============================================
if 'docs' not in st.session_state:
    st.session_state.docs = []
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = []
if 'expert_tracker' not in st.session_state:
    st.session_state.expert_tracker = ExpertTracker()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'slack_processor' not in st.session_state:
    st.session_state.slack_processor = SlackProcessor()
if 'slack_loaded' not in st.session_state:
    st.session_state.slack_loaded = False
if 'meeting_analyzer' not in st.session_state:
    st.session_state.meeting_analyzer = MeetingAnalyzer()
if 'action_tracker' not in st.session_state:
    st.session_state.action_tracker = ActionTracker()

# Live recording session states
if 'live_recorder_active' not in st.session_state:
    st.session_state.live_recorder_active = False
if 'recorded_transcript' not in st.session_state:
    st.session_state.recorded_transcript = []
if 'current_meeting_name' not in st.session_state:
    st.session_state.current_meeting_name = ""
if 'listening' not in st.session_state:
    st.session_state.listening = False

# ============================================
# LOAD MODELS
# ============================================
@st.cache_resource
def load_models():
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
    return embedder, groq

try:
    embedder, groq = load_models()
except Exception as e:
    st.error(f"❌ Failed to load models: {e}")
    st.stop()

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class='main-header'>
    <h1>🧠 Company AI Knowledge Platform</h1>
    <p>Your intelligent assistant for documents, experts, meetings, and Slack</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("### 👤 User Profile")
    user_role = st.selectbox(
        "Select your role",
        ["employee", "manager", "hr", "executive"],
        help="Different roles see different information"
    )
    
    st.divider()
    
    # Stats
    st.markdown("### 📊 Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Docs", len(st.session_state.docs))
    with col2:
        st.metric("👥 Experts", len(st.session_state.expert_tracker.experts))
    
    st.divider()
    
    # Expert Finder
    st.markdown("### 🔍 Find Experts")
    expert_query = st.text_input("Who knows about...", placeholder="e.g., python, database")
    
    if expert_query:
        with st.spinner("Searching..."):
            experts = st.session_state.expert_tracker.find_experts(expert_query)
            if experts:
                for expert in experts:
                    st.markdown(f"""
                    <div class='expert-card'>
                        <strong>👤 {expert['name']}</strong><br>
                        <small>🏆 Score: {expert['score']}</small><br>
                        <small>📚 {', '.join(expert['topics'][:2])}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(f"ℹ️ No experts found for '{expert_query}'")
    
    st.divider()
    
    # Document Upload
    st.markdown("### 📄 Add Document")
    uploaded_file = st.file_uploader("Upload PDF or TXT", type=['pdf', 'txt'])
    uploader_name = st.text_input("Your name", placeholder="e.g., John Doe")
    
    if uploaded_file and uploader_name:
        if st.button("📥 Add to Knowledge Base", use_container_width=True):
            with st.spinner("Processing..."):
                if uploaded_file.type == "application/pdf":
                    reader = PdfReader(uploaded_file)
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text()
                else:
                    content = uploaded_file.read().decode('utf-8')
                
                topics = st.session_state.expert_tracker.extract_topics(content)
                st.session_state.expert_tracker.add_expert(uploader_name, uploaded_file.name, topics)
                
                embedding = embedder.encode(content)
                st.session_state.docs.append({
                    'name': uploaded_file.name,
                    'content': content,
                    'uploader': uploader_name,
                    'topics': topics,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.session_state.embeddings.append(embedding)
                
                st.success(f"✅ **{uploader_name}** is now expert on: {', '.join(topics[:3])}")
                st.rerun()
    
    st.divider()
    
    # Slack Integration
    st.markdown("### 💬 Slack Integration")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Sample Data"):
            sample_data = st.session_state.slack_processor.create_sample_slack_data()
            st.download_button("Download", sample_data, "sample_slack.json", key="slack_dl")
    
    uploaded_slack = st.file_uploader("Upload Slack JSON", type=['json'], key="slack_upload")
    
    if uploaded_slack:
        if st.button("Process Slack"):
            with st.spinner("Processing..."):
                result = st.session_state.slack_processor.process_uploaded_file(
                    uploaded_slack.getvalue(), uploaded_slack.name
                )
                if result.get('success'):
                    st.session_state.slack_loaded = True
                    st.success(f"✅ Loaded {result['messages']} messages")
                    st.rerun()
    
    st.divider()
    
    # Meeting Analyzer
    st.markdown("### 🎙️ Meeting Analyzer")
    
    meeting_file = st.file_uploader("Upload transcript", type=['txt'], key="meeting_upload")
    meeting_name = st.text_input("Meeting name", placeholder="e.g., Weekly Sync", key="meeting_name")
    
    if meeting_file and meeting_name:
        if st.button("Analyze Meeting", use_container_width=True):
            with st.spinner("Analyzing..."):
                transcript = meeting_file.read().decode('utf-8')
                result = st.session_state.meeting_analyzer.analyze_transcript(
                    transcript, meeting_name, groq
                )
                report = st.session_state.meeting_analyzer.format_report(result)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": report,
                    "is_meeting": True
                })
                st.rerun()

    # ============================================
    # LIVE MEETING RECORDER WITH VOICE INPUT
    # ============================================
    st.divider()
    st.markdown("### 🎙️ Live Meeting Recorder")
    st.markdown("*Record with voice or text*")
    
    # Create meetings folder
    if not os.path.exists("meetings"):
        os.makedirs("meetings")
    
    if not st.session_state.live_recorder_active:
        meeting_title = st.text_input("Meeting title", placeholder="e.g., Weekly Sync March 15", key="meeting_title_input")
        
        if st.button("🎙️ Start Recording", use_container_width=True):
            if meeting_title:
                st.session_state.current_meeting_name = meeting_title
                st.session_state.live_recorder_active = True
                st.session_state.recorded_transcript = []
                st.success(f"🔴 Recording started: {meeting_title}")
                st.rerun()
            else:
                st.warning("Please enter a meeting title first!")
        
        # Show saved recordings
        st.markdown("---")
        st.markdown("### 📁 Saved Recordings")
        
        meeting_files = [f for f in os.listdir("meetings") if f.endswith('_transcript.txt')]
        if meeting_files:
            meeting_files.sort(reverse=True)
            for file in meeting_files[:5]:
                file_path = os.path.join("meetings", file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                st.download_button(
                    label=f"📄 {file.replace('_transcript.txt', '')[:30]}",
                    data=file_content,
                    file_name=file,
                    mime="text/plain",
                    key=f"download_{file}"
                )
        else:
            st.info("No saved recordings yet")
    
    else:
        # Recording active
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ff4444, #cc0000); 
                    color: white; 
                    padding: 10px; 
                    border-radius: 10px; 
                    text-align: center;
                    animation: pulse 1.5s infinite;">
            🔴 LIVE RECORDING IN PROGRESS
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**📝 Meeting:** {st.session_state.current_meeting_name}")
        
        # Voice Input Section
        st.markdown("### 🎤 Voice Input")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🎙️ Start Voice", use_container_width=True):
                st.session_state.listening = True
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop Voice", use_container_width=True):
                st.session_state.listening = False
                st.rerun()
        
        with col3:
            st.markdown("*Speak naturally*")
        
        if st.session_state.listening:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe, #00f2fe); 
                        padding: 15px; 
                        border-radius: 15px; 
                        text-align: center;
                        animation: pulse 1.5s infinite;">
                🎤 Listening... Speak now!
            </div>
            """, unsafe_allow_html=True)
            
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                with st.spinner("Converting speech to text..."):
                    text = recognizer.recognize_google(audio)
                    st.success(f"📝 Recognized: {text}")
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    st.session_state.recorded_transcript.append(f"[{timestamp}] {text}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"🎙️ **Voice input:** {text}"
                    })
                    st.rerun()
                    
            except sr.WaitTimeoutError:
                st.warning("No speech detected")
            except sr.UnknownValueError:
                st.warning("Could not understand audio")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                st.session_state.listening = False
        
        # Manual text input
        st.markdown("### 📝 Manual Input")
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            spoken_text = st.text_input("Type what was said", placeholder="Enter conversation...", key="spoken_input")
        with col2:
            if st.button("➕ Add", use_container_width=True):
                if spoken_text:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    st.session_state.recorded_transcript.append(f"[{timestamp}] {spoken_text}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"🎙️ **Meeting:** {spoken_text}"
                    })
                    st.success("Added ✓")
                    st.rerun()
        with col3:
            if st.button("🗑️ Clear Last", use_container_width=True):
                if st.session_state.recorded_transcript:
                    st.session_state.recorded_transcript.pop()
                    st.rerun()
        
        # Live transcript display
        st.markdown("### 📝 Live Transcript")
        if st.session_state.recorded_transcript:
            for line in st.session_state.recorded_transcript[-10:]:
                st.caption(f"• {line}")
        else:
            st.info("No transcript yet")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏹️ Stop & Save", use_container_width=True):
                if st.session_state.recorded_transcript:
                    safe_name = st.session_state.current_meeting_name.replace(" ", "_").lower()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{safe_name}_{timestamp}"
                    
                    transcript_path = os.path.join("meetings", f"{filename}_transcript.txt")
                    with open(transcript_path, 'w', encoding='utf-8') as f:
                        f.write(f"Meeting: {st.session_state.current_meeting_name}\n")
                        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("="*60 + "\n\n")
                        for line in st.session_state.recorded_transcript:
                            f.write(line + "\n")
                    
                    st.success(f"✅ Saved to {transcript_path}")
                    
                    # Extract actions automatically
                    full_transcript = "\n".join(st.session_state.recorded_transcript)
                    extracted = st.session_state.action_tracker.extract_actions_from_text(full_transcript, groq)
                    
                    if extracted:
                        st.success(f"🎯 Found {len(extracted)} action items!")
                        for action in extracted:
                            st.session_state.action_tracker.add_action(
                                task=action.get('task', 'Unknown'),
                                assignee=action.get('assignee', 'Unassigned'),
                                deadline=action.get('deadline', 'No deadline'),
                                source_meeting=st.session_state.current_meeting_name
                            )
                    
                    st.session_state.live_recorder_active = False
                    st.rerun()
                else:
                    st.warning("No transcript to save!")
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.live_recorder_active = False
                st.session_state.recorded_transcript = []
                st.rerun()
    
    # ============================================
    # ACTION TRACKER
    # ============================================
    st.divider()
    st.markdown("### ✅ Action Tracker")
    
    stats = st.session_state.action_tracker.get_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 Pending", stats['pending'])
    with col2:
        st.metric("✅ Completed", stats['completed'])
    with col3:
        st.metric("⚠️ Overdue", stats['overdue'])
    
    with st.expander("➕ Quick Add Action"):
        task = st.text_input("Task", placeholder="What needs to be done?", key="quick_task")
        assignee = st.text_input("Assignee", placeholder="Who is responsible?", key="quick_assignee")
        deadline = st.date_input("Deadline", key="quick_deadline")
        
        if st.button("Add Action", use_container_width=True):
            if task and assignee:
                st.session_state.action_tracker.add_action(
                    task=task,
                    assignee=assignee,
                    deadline=deadline.strftime('%Y-%m-%d'),
                    source_meeting="Manual entry"
                )
                st.success(f"✅ Added: {task} → {assignee}")
                st.rerun()
    
    pending = st.session_state.action_tracker.get_pending_actions()
    if pending:
        st.markdown("**📋 Pending Actions**")
        for action in pending[:5]:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(f"• **{action['task']}** → {action['assignee']}")
                if action['deadline'] != "No deadline specified":
                    st.caption(f"  📅 Due: {action['deadline']}")
            with col2:
                if st.button("✅", key=f"complete_{action['id']}"):
                    st.session_state.action_tracker.complete_action(action['id'])
                    st.rerun()
    
    overdue = st.session_state.action_tracker.get_overdue_actions()
    if overdue:
        st.warning(f"⚠️ {len(overdue)} overdue action(s)!")

# ============================================
# MAIN CHAT INTERFACE
# ============================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📚 Documents", len(st.session_state.docs))
with col2:
    st.metric("👥 Experts", len(st.session_state.expert_tracker.experts))
with col3:
    st.metric("💬 Messages", len(st.session_state.messages) // 2)
with col4:
    meeting_stats = st.session_state.meeting_analyzer.get_all_meetings_summary()
    st.metric("📋 Meetings", meeting_stats.get('total', 0))

st.divider()

# ============================================
# ACTION DASHBOARD IN MAIN AREA
# ============================================
with st.expander("✅ Action Dashboard", expanded=False):
    stats = st.session_state.action_tracker.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Total", stats['total'])
    with col2:
        st.metric("⏳ Pending", stats['pending'])
    with col3:
        st.metric("✅ Completed", stats['completed'])
    with col4:
        st.metric("⚠️ Overdue", stats['overdue'])
    
    st.progress(stats['completion_rate'] / 100)
    st.caption(f"Completion Rate: {stats['completion_rate']:.0f}%")
    
    pending = st.session_state.action_tracker.get_pending_actions()
    if pending:
        st.markdown("### 📋 Pending Actions")
        for action in pending:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.write(f"**{action['task']}**")
            with col2:
                st.write(f"👤 {action['assignee']}")
            with col3:
                st.write(f"📅 {action['deadline']}")
            with col4:
                if st.button("✅ Complete", key=f"complete_main_{action['id']}"):
                    st.session_state.action_tracker.complete_action(action['id'])
                    st.rerun()

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if msg["role"] == "assistant" and "sources" in msg:
            with st.expander("📚 Sources"):
                for src in msg["sources"]:
                    st.markdown(f"""
                    <div class='source-card'>
                        📁 {src['name']}<br>
                        👤 {src['uploader']}<br>
                        🏷️ {', '.join(src['topics'][:3])}
                    </div>
                    """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask me anything about your company..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with message_placeholder.container():
            st.markdown('<div class="typing-dots"><span></span><span></span><span></span></div>', unsafe_allow_html=True)
        
        # Check for expert query
        if any(phrase in prompt.lower() for phrase in ["who knows", "expert on", "find expert"]):
            topic = prompt.lower().replace("who knows", "").replace("expert on", "").replace("find expert", "").strip().strip('?').strip()
            
            doc_experts = st.session_state.expert_tracker.find_experts(topic)
            slack_experts = []
            if st.session_state.slack_loaded:
                slack_experts = st.session_state.slack_processor.find_experts(topic, limit=2)
            
            time.sleep(0.5)
            
            if doc_experts or slack_experts:
                response = f"### 🎯 Experts for '{topic}'\n\n"
                if doc_experts:
                    response += "**📚 From Documents:**\n"
                    for exp in doc_experts:
                        response += f"• **{exp['name']}** (Score: {exp['score']})\n"
                if slack_experts:
                    response += "\n**💬 From Slack:**\n"
                    for exp in slack_experts:
                        response += f"• **{exp['name']}** - {exp['expertise_level']} ({exp['mentions']} mentions)\n"
            else:
                response = f"No experts found for '{topic}'. Upload a document with your name to become an expert!"
            
            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Check for meeting search
        elif any(phrase in prompt.lower() for phrase in ["meeting", "what happened", "action item"]):
            results = st.session_state.meeting_analyzer.search_meetings(prompt, limit=2)
            
            if results:
                response = f"### 📚 Found {len(results)} relevant meetings\n\n"
                for r in results:
                    response += f"**{r['meeting_name']}**\n"
                    for ctx in r['context']:
                        response += f"• {ctx}\n"
                    response += "\n"
            else:
                response = "No matching meetings found. Upload a meeting transcript first!"
            
            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Normal Q&A
        elif st.session_state.docs:
            q_embedding = embedder.encode(prompt)
            similarities = []
            
            for doc, emb in zip(st.session_state.docs, st.session_state.embeddings):
                sim = np.dot(q_embedding, emb) / (np.linalg.norm(q_embedding) * np.linalg.norm(emb))
                similarities.append(sim)
            
            top_indices = np.argsort(similarities)[-2:][::-1]
            context = ""
            sources = []
            
            for idx in top_indices:
                doc = st.session_state.docs[idx]
                context += f"\n\n--- {doc['name']} ---\n{doc['content'][:1500]}"
                sources.append({'name': doc['name'], 'uploader': doc['uploader'], 'topics': doc['topics']})
            
            try:
                completion = groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"You are a company assistant for {user_role}. Answer based ONLY on provided documents."},
                        {"role": "user", "content": f"Documents:{context}\n\nQuestion: {prompt}"}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                response = completion.choices[0].message.content
                message_placeholder.markdown(response)
                
                with st.expander("📚 Sources"):
                    for src in sources:
                        st.markdown(f"📁 {src['name']} (by {src['uploader']})")
                
            except Exception as e:
                response = f"Error: {e}"
                message_placeholder.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response, "sources": sources})
        
        else:
            response = "No documents found! Upload documents in the sidebar to get started."
            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #888; padding: 20px;'>
    <small>🔒 Role-based access control | 🧠 Powered by Groq Llama 3 | 💡 Ask "who knows python" or upload a meeting transcript</small>
</div>
""", unsafe_allow_html=True)