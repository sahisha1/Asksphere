"""
Action Tracker - Track tasks from meetings
"""

import json
import os
from datetime import datetime

class ActionTracker:
    def __init__(self, storage_path="actions.json"):
        self.storage_path = storage_path
        self.actions = []
        self.load_actions()
    
    def load_actions(self):
        """Load actions from JSON file"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.actions = json.load(f)
            except:
                self.actions = []
    
    def save_actions(self):
        """Save actions to JSON file"""
        with open(self.storage_path, 'w') as f:
            json.dump(self.actions, f, indent=2)
    
    def add_action(self, task, assignee, deadline, source_meeting=""):
        """Add a new action item"""
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
        """Mark action as completed"""
        for action in self.actions:
            if action['id'] == action_id:
                action['status'] = 'completed'
                action['completed_at'] = datetime.now().isoformat()
                self.save_actions()
                return True
        return False
    
    def delete_action(self, action_id):
        """Delete an action"""
        self.actions = [a for a in self.actions if a['id'] != action_id]
        self.save_actions()
    
    def get_pending_actions(self):
        """Get all pending actions"""
        return [a for a in self.actions if a['status'] == 'pending']
    
    def get_completed_actions(self):
        """Get all completed actions"""
        return [a for a in self.actions if a['status'] == 'completed']
    
    def get_overdue_actions(self):
        """Get overdue actions"""
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
        """Get action statistics"""
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
        """Use AI to extract action items from meeting transcript"""
        prompt = f"""
        Extract action items from this meeting transcript.
        For each action, identify: task, who is responsible, and deadline if mentioned.
        
        Transcript: {text[:2000]}
        
        Return as JSON array:
        [{{"task": "...", "assignee": "...", "deadline": "..."}}]
        
        If no deadline mentioned, use "No deadline specified".
        Only return the JSON array, no other text.
        """
        
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You extract action items from meetings. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            import json as json_lib
            result_text = response.choices[0].message.content
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            actions = json_lib.loads(result_text)
            
            if not isinstance(actions, list):
                actions = [actions]
            
            return actions
        except Exception as e:
            print(f"Error extracting actions: {e}")
            return []