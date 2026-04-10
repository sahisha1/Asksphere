"""
EXPERT TRACKER - "Who Knows This?" Feature
Tracks who contributes to what knowledge
"""

import streamlit as st
from datetime import datetime
import json
import os

class ExpertTracker:
    """
    Tracks expertise across the company
    Each person gets "expertise points" for:
    - Uploading documents
    - Speaking in Slack
    - Attending meetings
    """
    
    def __init__(self, data_file="expertise_data.json"):
        self.data_file = data_file
        self.expertise = self.load_expertise()
    
    def load_expertise(self):
        """Load saved expertise data"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_expertise(self):
        """Save expertise data"""
        with open(self.data_file, 'w') as f:
            json.dump(self.expertise, f, indent=2)
    
    def add_document_contribution(self, person_name, document_name, topics):
        """
        Record that a person contributed a document
        topics: list of keywords from the document
        """
        if person_name not in self.expertise:
            self.expertise[person_name] = {'topics': {}, 'total_points': 0, 'documents': []}
        
        # Add document to list
        if 'documents' not in self.expertise[person_name]:
            self.expertise[person_name]['documents'] = []
        self.expertise[person_name]['documents'].append(document_name)
        
        # Add points for each topic
        for topic in topics:
            if topic not in self.expertise[person_name]['topics']:
                self.expertise[person_name]['topics'][topic] = 0
            self.expertise[person_name]['topics'][topic] += 10  # 10 points per doc
            self.expertise[person_name]['total_points'] += 10
        
        self.save_expertise()
        print(f"✅ Recorded: {person_name} knows about {topics}")
    
    def add_slack_contribution(self, person_name, topic, message_count=1):
        """
        Record Slack message contributions
        """
        if person_name not in self.expertise:
            self.expertise[person_name] = {'topics': {}, 'total_points': 0, 'slack_messages': 0}
        
        if 'slack_messages' not in self.expertise[person_name]:
            self.expertise[person_name]['slack_messages'] = 0
        self.expertise[person_name]['slack_messages'] += message_count
        
        if topic not in self.expertise[person_name]['topics']:
            self.expertise[person_name]['topics'][topic] = 0
        
        # 2 points per Slack message (less than documents)
        self.expertise[person_name]['topics'][topic] += 2 * message_count
        self.expertise[person_name]['total_points'] += 2 * message_count
        
        self.save_expertise()
    
    def find_experts(self, topic, top_k=3):
        """
        Find top experts for a given topic
        Returns: list of (person_name, score, details)
        """
        experts = []
        
        for person, data in self.expertise.items():
            score = 0
            matching_topics = []
            
            # Check all topics this person knows
            for known_topic, points in data.get('topics', {}).items():
                if topic.lower() in known_topic.lower() or known_topic.lower() in topic.lower():
                    score += points
                    matching_topics.append(known_topic)
            
            if score > 0:
                experts.append({
                    'name': person,
                    'score': score,
                    'matching_topics': matching_topics,
                    'total_points': data.get('total_points', 0),
                    'documents': len(data.get('documents', [])),
                    'slack_messages': data.get('slack_messages', 0)
                })
        
        # Sort by score
        experts.sort(key=lambda x: x['score'], reverse=True)
        return experts[:top_k]
    
    def extract_topics_from_text(self, text):
        """
        Extract key topics from text
        Simple version: just get important words
        """
        # Simple keyword extraction (can be improved)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had'}
        words = text.lower().split()
        
        # Get unique important words (length > 4 and not stop words)
        topics = set()
        for word in words:
            # Remove punctuation
            word = word.strip('.,!?;:()[]{}"\'')
            if len(word) > 4 and word not in stop_words:
                topics.add(word)
        
        # Also look for capitalized words (likely proper nouns)
        for word in text.split():
            if len(word) > 2 and word[0].isupper() and word.lower() not in stop_words:
                topics.add(word.lower())
        
        return list(topics)[:10]  # Limit to 10 topics
    
    def get_all_experts(self):
        """Get all experts with their stats"""
        experts = []
        for person, data in self.expertise.items():
            experts.append({
                'name': person,
                'total_points': data.get('total_points', 0),
                'topics': len(data.get('topics', {})),
                'documents': len(data.get('documents', [])),
                'slack_messages': data.get('slack_messages', 0)
            })
        return sorted(experts, key=lambda x: x['total_points'], reverse=True)

# Test the expert tracker
if __name__ == "__main__":
    tracker = ExpertTracker()
    
    # Clear old data for testing
    tracker.expertise = {}
    
    # Simulate contributions
    tracker.add_document_contribution("Alice", "kubernetes_guide.pdf", ["kubernetes", "docker", "devops"])
    tracker.add_slack_contribution("Bob", "kubernetes", 5)
    tracker.add_slack_contribution("Alice", "python", 3)
    tracker.add_document_contribution("Carol", "vacation_policy.pdf", ["vacation", "holiday", "pto"])
    
    # Find experts
    print("\n🎯 Experts on Kubernetes:")
    experts = tracker.find_experts("kubernetes")
    for expert in experts:
        print(f"  - {expert['name']} (Score: {expert['score']})")
    
    print("\n🎯 All Experts:")
    for expert in tracker.get_all_experts():
        print(f"  - {expert['name']}: {expert['total_points']} points")