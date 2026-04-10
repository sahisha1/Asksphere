"""
Silent Attendee - Meeting Analyzer Core Logic
Analyzes meeting transcripts and extracts insights
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

class MeetingAnalyzer:
    def __init__(self, storage_path="meetings_database.json"):
        self.storage_path = storage_path
        self.meetings = []
        self.load_meetings()
    
    def load_meetings(self):
        """Load past meetings from database"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.meetings = json.load(f)
            except:
                self.meetings = []
    
    def save_meetings(self):
        """Save meetings to database"""
        with open(self.storage_path, 'w') as f:
            json.dump(self.meetings, f, indent=2)
    
    def analyze_transcript(self, transcript: str, meeting_name: str, groq_client) -> Dict:
        """Analyze meeting transcript using AI"""
        
        analysis_prompt = f"""
        Analyze this meeting transcript and extract:
        
        1. summary (2-3 sentences)
        2. action_items (task, assignee, deadline)
        3. decisions made
        4. contradictions found
        5. speakers list
        6. key quotes
        7. efficiency_score (0-100)
        8. wasted_time_minutes
        9. missing_topics
        
        Transcript:
        {transcript[:4000]}
        
        Return ONLY valid JSON format:
        {{
            "summary": "...",
            "action_items": [{{"task": "...", "assignee": "...", "deadline": "..."}}],
            "decisions": ["decision1", "decision2"],
            "contradictions": [],
            "speakers": [],
            "key_quotes": [{{"speaker": "...", "quote": "..."}}],
            "efficiency_score": 75,
            "wasted_time_minutes": 10,
            "missing_topics": []
        }}
        """
        
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a meeting analyzer. Return ONLY valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis_text = response.choices[0].message.content
            analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()
            analysis = json.loads(analysis_text)
            
        except Exception as e:
            analysis = {
                "summary": f"Meeting analyzed: {meeting_name}",
                "action_items": [],
                "decisions": [],
                "contradictions": [],
                "speakers": [],
                "key_quotes": [],
                "efficiency_score": 50,
                "wasted_time_minutes": 0,
                "missing_topics": []
            }
        
        meeting_data = {
            "id": len(self.meetings) + 1,
            "name": meeting_name,
            "timestamp": datetime.now().isoformat(),
            "transcript_preview": transcript[:500],
            "full_transcript": transcript,
            **analysis
        }
        
        self.meetings.append(meeting_data)
        self.save_meetings()
        
        return meeting_data
    
    def search_meetings(self, query: str, limit: int = 3) -> List[Dict]:
        """Search through past meetings"""
        results = []
        query_lower = query.lower()
        
        for meeting in self.meetings:
            relevance_score = 0
            context = []
            
            if query_lower in meeting.get('summary', '').lower():
                relevance_score += 10
                context.append(f"Summary: {meeting['summary'][:100]}")
            
            for item in meeting.get('action_items', []):
                if query_lower in item.get('task', '').lower():
                    relevance_score += 8
                    context.append(f"Action: {item['task']} → {item.get('assignee', 'Unknown')}")
            
            for decision in meeting.get('decisions', []):
                if query_lower in decision.lower():
                    relevance_score += 8
                    context.append(f"Decision: {decision}")
            
            if relevance_score > 0:
                results.append({
                    'meeting_name': meeting['name'],
                    'date': meeting['timestamp'],
                    'relevance_score': relevance_score,
                    'context': context[:3],
                    'summary': meeting.get('summary', '')
                })
        
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results[:limit]
    
    def get_all_meetings_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.meetings:
            return {"total": 0}
        
        total_action_items = sum(len(m.get('action_items', [])) for m in self.meetings)
        total_decisions = sum(len(m.get('decisions', [])) for m in self.meetings)
        avg_efficiency = sum(m.get('efficiency_score', 0) for m in self.meetings) / len(self.meetings)
        
        return {
            "total": len(self.meetings),
            "total_action_items": total_action_items,
            "total_decisions": total_decisions,
            "avg_efficiency": round(avg_efficiency, 1)
        }
    
    def format_report(self, meeting_data: Dict) -> str:
        """Format meeting analysis as markdown"""
        report = f"""
### 🤫 Silent Attendee Report

**📅 Meeting:** {meeting_data['name']}
**🕐 Analyzed:** {meeting_data['timestamp'][:19]}

---

#### 📝 Summary
{meeting_data.get('summary', 'No summary available')}

---

#### ✅ Action Items
"""
        if meeting_data.get('action_items'):
            for item in meeting_data['action_items']:
                assignee = item.get('assignee', 'Unknown')
                deadline = item.get('deadline', 'No deadline')
                report += f"- **{item['task']}** → {assignee} (by {deadline})\n"
        else:
            report += "- No action items found\n"
        
        report += """
---

#### 🎯 Decisions Made
"""
        if meeting_data.get('decisions'):
            for decision in meeting_data['decisions']:
                report += f"- {decision}\n"
        else:
            report += "- No decisions recorded\n"
        
        report += f"""
---

#### 📊 Meeting Efficiency
- **Efficiency Score:** {meeting_data.get('efficiency_score', 50)}/100
- **Wasted Time:** ~{meeting_data.get('wasted_time_minutes', 0)} minutes
- **Speakers:** {', '.join(meeting_data.get('speakers', ['Unknown']))}

---
*🤫 Silent Attendee - Making meetings matter* 💡
"""
        return report
    