"""
Role-Based Access Control (RBAC)
Controls what information different roles can see
This is what makes your project enterprise-ready!
"""

class RoleBasedAccess:
    """
    Manages access control for different roles
    Roles: employee, manager, hr, executive
    """
    
    def __init__(self):
        # Define what topics each role can access
        self.role_permissions = {
            'employee': {
                'allowed_topics': [
                    'vacation', 'remote_work', 'benefits', 
                    'training', 'code_of_conduct'
                ],
                'forbidden_topics': [
                    'salary', 'bonus', 'layoffs', 'confidential'
                ],
                'max_sensitivity': 1  # 1-5 scale
            },
            'manager': {
                'allowed_topics': [
                    'vacation', 'remote_work', 'benefits',
                    'training', 'code_of_conduct', 'salary',
                    'performance', 'budget'
                ],
                'forbidden_topics': [
                    'layoffs', 'acquisition', 'executive'
                ],
                'max_sensitivity': 3
            },
            'hr': {
                'allowed_topics': ['*'],  # All topics
                'forbidden_topics': [],
                'max_sensitivity': 5
            },
            'executive': {
                'allowed_topics': ['*'],
                'forbidden_topics': [],
                'max_sensitivity': 5
            }
        }
        
        # Document sensitivity mapping
        self.document_sensitivity = {
            'policies.txt': 1,  # Public
            'salary.txt': 4,     # Very sensitive
            'sample.pdf': 2,     # Medium
        }
    
    def can_query(self, role: str, question: str) -> bool:
        """
        Check if a role can ask a certain question
        Based on keywords in the question
        """
        if role not in self.role_permissions:
            role = 'employee'  # Default to employee
        
        permissions = self.role_permissions[role]
        
        # If role has '*' access, allow everything
        if '*' in permissions['allowed_topics']:
            return True
        
        # Check for forbidden topics
        question_lower = question.lower()
        for forbidden in permissions['forbidden_topics']:
            if forbidden in question_lower:
                return False
        
        # Check if question contains any allowed topic
        # If not, default to allowed (but filter in retrieval)
        return True
    
    def get_filter(self, role: str) -> dict:
        """
        Get metadata filter for vector search
        Returns filter dict for ChromaDB
        """
        if role == 'executive' or role == 'hr':
            # Can see everything
            return None
        
        # Employees and managers see filtered content
        # We filter by source file sensitivity
        return {
            '$or': [
                {'sensitivity': {'$lte': self.role_permissions[role]['max_sensitivity']}},
                {'sensitivity': {'$exists': False}}  # Documents without sensitivity tag
            ]
        }
    
    def add_document_permissions(self, doc_metadata: dict, role: str) -> dict:
        """Add permission metadata to a document"""
        doc_metadata['allowed_roles'] = self._get_allowed_roles_for_doc(doc_metadata)
        return doc_metadata
    
    def _get_allowed_roles_for_doc(self, metadata: dict) -> list:
        """Determine which roles can access a document"""
        sensitivity = metadata.get('sensitivity', 1)
        
        allowed = []
        for role, perms in self.role_permissions.items():
            if perms['max_sensitivity'] >= sensitivity:
                allowed.append(role)
        
        return allowed

# Test RBAC
if __name__ == "__main__":
    rbac = RoleBasedAccess()
    
    test_questions = [
        ("How many vacation days?", "employee"),
        ("What is the CEO's salary?", "employee"),
        ("What is the CEO's salary?", "hr"),
        ("Tell me about layoffs", "manager"),
    ]
    
    for question, role in test_questions:
        allowed = rbac.can_query(role, question)
        print(f"Role: {role} | Q: {question}")
        print(f"Allowed: {allowed}\n")