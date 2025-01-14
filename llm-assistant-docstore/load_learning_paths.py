from sqlalchemy.orm import Session
from app.models.database import LearningPath, Tutorial, SessionLocal, TutorialChapter
from datetime import datetime

def load_sample_data():
    db = SessionLocal()
    
    # Clear existing data
    db.query(TutorialChapter).delete()
    db.query(Tutorial).delete()
    db.query(LearningPath).delete()
    
    # Create a sample learning path
    python_path = LearningPath(
        title="Python Programming Fundamentals",
        description="Learn the basics of Python programming language",
        category="Programming",
        path_metadata={"difficulty": "beginner"}
    )
    db.add(python_path)
    db.flush()  # Flush to get the ID
    
    # Create tutorials with chapters
    tutorials_data = [
        {
            "title": "Getting Started with Python",
            "description": "Learn the basics of Python syntax and setup",
            "content": "This tutorial will guide you through Python basics.",
            "order": 1,
            "estimated_duration": 30,
            "chapters": [
                {
                    "title": "Installation and Setup",
                    "content": """# Installing Python
1. Visit python.org
2. Download the latest version
3. Run the installer
4. Verify installation with `python --version`""",
                    "order": 1
                },
                {
                    "title": "Basic Syntax",
                    "content": """# Python Basic Syntax
- Variables and data types
- Basic operators
- Writing your first program
- Running Python scripts""",
                    "order": 2
                }
            ]
        },
        {
            "title": "Python Data Structures",
            "description": "Understanding Python's built-in data structures",
            "content": "Learn about lists, dictionaries, and more.",
            "order": 2,
            "estimated_duration": 45,
            "chapters": [
                {
                    "title": "Lists and Tuples",
                    "content": """# Lists and Tuples in Python
- Creating lists
- List operations
- Tuples vs Lists
- Common methods""",
                    "order": 1
                },
                {
                    "title": "Dictionaries",
                    "content": """# Python Dictionaries
- Key-value pairs
- Dictionary methods
- Nested dictionaries
- Common use cases""",
                    "order": 2
                },
                {
                    "title": "Sets",
                    "content": """# Python Sets
- Creating sets
- Set operations
- Use cases for sets
- Performance considerations""",
                    "order": 3
                }
            ]
        }
    ]
    
    for tutorial_data in tutorials_data:
        chapters = tutorial_data.pop('chapters')
        tutorial = Tutorial(
            learning_path_id=python_path.id,
            **tutorial_data
        )
        db.add(tutorial)
        db.flush()  # Get the tutorial ID
        
        # Add chapters for this tutorial
        for chapter_data in chapters:
            chapter = TutorialChapter(
                tutorial_id=tutorial.id,
                **chapter_data
            )
            db.add(chapter)
    
    # Add another learning path for variety
    git_path = LearningPath(
        title="Git Version Control",
        description="Master Git for version control",
        category="Development Tools",
        path_metadata={"difficulty": "intermediate"}
    )
    db.add(git_path)
    db.flush()
    
    git_tutorials = [
        {
            "title": "Git Basics",
            "description": "Learn the fundamental Git commands",
            "content": "Understanding basic Git workflow",
            "order": 1,
            "estimated_duration": 40,
            "chapters": [
                {
                    "title": "Git Setup",
                    "content": """# Setting up Git
1. Installing Git
2. Basic configuration
3. Creating your first repository""",
                    "order": 1
                },
                {
                    "title": "Basic Commands",
                    "content": """# Essential Git Commands
- git init
- git add
- git commit
- git status
- git log""",
                    "order": 2
                }
            ]
        },
        {
            "title": "Branching and Merging",
            "description": "Working with Git branches",
            "content": "Learn to work with branches in Git",
            "order": 2,
            "estimated_duration": 50,
            "chapters": [
                {
                    "title": "Working with Branches",
                    "content": """# Git Branching
- Creating branches
- Switching branches
- Branch management""",
                    "order": 1
                },
                {
                    "title": "Merging Strategies",
                    "content": """# Git Merging
- Basic merging
- Handling conflicts
- Merge strategies""",
                    "order": 2
                }
            ]
        }
    ]
    
    for tutorial_data in git_tutorials:
        chapters = tutorial_data.pop('chapters')
        tutorial = Tutorial(
            learning_path_id=git_path.id,
            **tutorial_data
        )
        db.add(tutorial)
        db.flush()
        
        for chapter_data in chapters:
            chapter = TutorialChapter(
                tutorial_id=tutorial.id,
                **chapter_data
            )
            db.add(chapter)
    
    try:
        db.commit()
        print("Sample learning paths, tutorials, and chapters loaded successfully!")
    except Exception as e:
        print(f"Error loading sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_sample_data() 