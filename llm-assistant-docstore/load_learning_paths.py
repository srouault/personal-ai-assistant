from sqlalchemy.orm import Session
from app.models.database import LearningPath, Tutorial, SessionLocal

def load_sample_data():
    db = SessionLocal()
    
    try:
        # Engineering Onboarding Path
        eng_path = LearningPath(
            title="Engineering Onboarding",
            description="Complete onboarding journey for new software engineers",
            category="Engineering",
            path_metadata={
                "department": "Engineering",
                "required": True,
                "estimated_days": 14
            }
        )
        db.add(eng_path)
        db.commit()
        db.refresh(eng_path)
        
        # Add tutorials for engineering onboarding
        tutorials = [
            {
                "title": "Development Environment Setup",
                "description": "Set up your local development environment with all necessary tools",
                "content": """# Development Environment Setup

1. Install required software:
   - Git
   - Docker
   - VS Code
   - Python 3.9+
   - Node.js 16+

2. Clone the main repositories:
   ```bash
   git clone https://github.com/company/main-service
   git clone https://github.com/company/frontend-app
   ```

3. Set up your SSH keys and configure Git

4. Install project dependencies""",
                "order": 1,
                "estimated_duration": 45
            },
            {
                "title": "Architecture Overview",
                "description": "Learn about our system architecture and main components",
                "content": """# System Architecture Overview

Our system consists of these main components:

1. Frontend (React.js)
2. Backend API (FastAPI)
3. Document Store (Vector DB)
4. Authentication Service
5. Analytics Pipeline

Key points to understand:
- Microservices architecture
- Event-driven communication
- Data flow patterns
- Security measures

Would you like to dive deeper into any of these components?""",
                "order": 2,
                "estimated_duration": 90
            },
            {
                "title": "Coding Standards",
                "description": "Learn our coding standards and best practices",
                "content": """# Coding Standards

Our team follows these key principles:

1. Code Style
   - PEP 8 for Python
   - ESLint config for JavaScript
   - Type hints required
   
2. Testing Requirements
   - Unit tests required (80% coverage)
   - Integration tests for APIs
   - E2E tests for critical paths

3. Code Review Process
   - Create detailed PR descriptions
   - Request review from 2 team members
   - Address all comments

4. Documentation
   - README.md for each service
   - API documentation
   - Architecture decision records

Questions about any of these areas?""",
                "order": 3,
                "estimated_duration": 60
            }
        ]
        
        for tutorial_data in tutorials:
            tutorial = Tutorial(
                learning_path_id=eng_path.id,
                **tutorial_data
            )
            db.add(tutorial)
        
        db.commit()
        print("Sample data loaded successfully!")
        
    except Exception as e:
        print(f"Error loading sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    load_sample_data() 