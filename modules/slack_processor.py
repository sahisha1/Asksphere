"""
Slack Processor - Handles uploaded Slack exports
Extracts expertise from conversations
"""

import json
from typing import List, Dict
from datetime import datetime

class SlackProcessor:
    def __init__(self):
        self.messages = []
        self.users = {}
        self.expertise = {}
    
    def process_uploaded_file(self, file_content: bytes, filename: str) -> Dict:
        """
        Process uploaded Slack export file
        Returns: Stats about processed data
        """
        try:
            # Parse JSON content
            if filename.endswith('.json'):
                data = json.loads(file_content.decode('utf-8'))
            else:
                # Handle zip files if needed
                return {'error': 'Please upload JSON file. For zip files, extract first.'}
            
            # Reset data
            self.messages = []
            self.users = {}
            
            # Process messages
            total_messages = 0
            
            # Handle different Slack export formats
            if isinstance(data, list):
                # Format: list of channels
                for channel_data in data:
                    channel = channel_data.get('channel', 'unknown')
                    messages = channel_data.get('messages', [])
                    
                    for msg in messages:
                        self._add_message(msg, channel)
                        total_messages += 1
                        
            elif isinstance(data, dict):
                # Format: single channel or workspace export
                channels = data.get('channels', [data])
                for channel_data in channels:
                    channel = channel_data.get('name', 'general')
                    messages = channel_data.get('messages', [])
                    
                    for msg in messages:
                        self._add_message(msg, channel)
                        total_messages += 1
            
            return {
                'success': True,
                'messages': total_messages,
                'users': len(self.users),
                'channels': len(set(msg.get('channel', 'unknown') for msg in self.messages))
            }
            
        except Exception as e:
            return {'error': f"Failed to process Slack file: {str(e)}"}
    
    def _add_message(self, msg: Dict, channel: str):
        """Add a single message to the dataset"""
        user = msg.get('user', msg.get('username', 'unknown'))
        text = msg.get('text', '')
        
        # Skip bot messages and empty text
        if user == 'slackbot' or not text:
            return
        
        # Detect topic from message
        topic = self._detect_topic(text)
        
        message = {
            'user': user,
            'text': text,
            'channel': channel,
            'timestamp': msg.get('ts', msg.get('timestamp', '')),
            'topic': topic
        }
        
        self.messages.append(message)
        
        # Update user stats
        if user not in self.users:
            self.users[user] = {
                'name': user,
                'messages': [],
                'topics': {},
                'total_messages': 0
            }
        
        self.users[user]['messages'].append(message)
        self.users[user]['total_messages'] += 1
        
        # Update topic expertise
        if topic not in self.users[user]['topics']:
            self.users[user]['topics'][topic] = 0
        self.users[user]['topics'][topic] += 1
    
    def _detect_topic(self, text: str) -> str:
        """Detect topic from message text"""
        text_lower = text.lower()
        
        topics = {
            'deployment': ['deploy', 'release', 'production', 'rollback', 'ci/cd', 'devops'],
            'python': ['python', 'django', 'flask', 'pip', 'virtualenv', 'py'],
            'database': ['database', 'sql', 'migration', 'postgres', 'mysql', 'query'],
            'budget': ['budget', 'cost', 'spending', 'approval', 'finance', 'money'],
            'hiring': ['hire', 'interview', 'candidate', 'recruiting', 'job', 'position'],
            'vacation': ['vacation', 'pto', 'holiday', 'time off', 'leave', 'break'],
            'security': ['security', 'vulnerability', 'patch', 'audit', 'access', 'auth'],
            'frontend': ['react', 'vue', 'angular', 'css', 'html', 'ui', 'frontend'],
            'backend': ['api', 'endpoint', 'server', 'backend', 'microservice'],
            'documentation': ['doc', 'documentation', 'readme', 'wiki', 'guide']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return 'general'
    
    def find_experts(self, topic: str, limit: int = 3) -> List[Dict]:
        """Find experts on a topic based on Slack conversations"""
        experts = []
        
        for user_name, user_data in self.users.items():
            topic_mentions = user_data['topics'].get(topic, 0)
            total_messages = user_data['total_messages']
            
            if topic_mentions > 0:
                # Calculate expertise score
                # Score = mentions + (mentions/total_messages) * 50
                frequency_bonus = (topic_mentions / max(total_messages, 1)) * 50
                score = topic_mentions + frequency_bonus
                
                # Get recent messages about this topic
                recent_msgs = [
                    msg for msg in user_data['messages']
                    if msg.get('topic') == topic
                ][:3]
                
                experts.append({
                    'name': user_name,
                    'score': score,
                    'mentions': topic_mentions,
                    'total_messages': total_messages,
                    'expertise_level': self._get_expertise_level(topic_mentions),
                    'recent_messages': recent_msgs
                })
        
        experts.sort(key=lambda x: x['score'], reverse=True)
        return experts[:limit]
    
    def search_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        """Search Slack conversations for keywords"""
        results = []
        query_lower = query.lower()
        
        for msg in self.messages:
            if query_lower in msg['text'].lower():
                results.append({
                    'user': msg['user'],
                    'text': msg['text'],
                    'channel': msg['channel'],
                    'timestamp': msg['timestamp'],
                    'topic': msg.get('topic', 'general')
                })
        
        return results[:limit]
    
    def _get_expertise_level(self, mentions: int) -> str:
        """Convert mention count to expertise level"""
        if mentions >= 20:
            return "Expert 🏆"
        elif mentions >= 10:
            return "Knowledgeable 📚"
        elif mentions >= 5:
            return "Familiar 👍"
        else:
            return "Learning 📖"
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.messages:
            return {'loaded': False}
        
        # Find top topics
        topic_counts = {}
        for msg in self.messages:
            topic = msg.get('topic', 'general')
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Find most active users
        active_users = [(name, data['total_messages']) 
                       for name, data in self.users.items()]
        active_users.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'loaded': True,
            'total_messages': len(self.messages),
            'total_users': len(self.users),
            'top_topics': dict(sorted(topic_counts.items(), 
                                      key=lambda x: x[1], 
                                      reverse=True)[:5]),
            'most_active': active_users[:3]
        }
    
    def create_sample_slack_data(self) -> bytes:
        """Create sample Slack data for testing"""
        import random
        from datetime import datetime, timedelta
        
        users = ['alex_chen', 'sarah_jones', 'mike_wilson', 'lisa_wong']
        topics = ['deployment', 'python', 'database', 'budget', 'general']
        
        channels = ['#general', '#tech', '#random']
        messages = []
        
        for channel in channels:
            channel_messages = []
            for i in range(50):
                user = random.choice(users)
                topic = random.choice(topics)
                
                templates = {
                    'deployment': [f"Deployed new version to production", "CI/CD pipeline is failing", "Can someone review my deployment?"],
                    'python': [f"Python script is running slow", "Need help with Django", "Python best practices?"],
                    'database': [f"Database migration complete", "SQL query optimization needed", "Backup completed"],
                    'budget': [f"Q3 budget approved", "Cost saving initiative", "Budget review meeting at 2pm"],
                    'general': [f"Hello everyone!", "Good morning team", "Anyone free for a quick call?"]
                }
                
                text = random.choice(templates.get(topic, ["Hello"]))
                
                channel_messages.append({
                    'user': user,
                    'text': text,
                    'ts': str(int(datetime.now().timestamp()) - random.randint(0, 86400 * 30))
                })
            
            messages.append({
                'channel': channel,
                'messages': channel_messages
            })
        
        return json.dumps(messages, indent=2).encode('utf-8')