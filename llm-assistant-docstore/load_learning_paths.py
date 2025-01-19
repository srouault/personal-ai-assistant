from sqlalchemy.orm import Session
from app.models.database import LearningPath, Tutorial, Chapter, Step, SessionLocal, init_db
from datetime import datetime

def load_sample_data():
    db = SessionLocal()
    
    # Clear existing data in correct order
    try:
        db.query(Step).delete()
        db.query(Chapter).delete()
        db.query(Tutorial).delete()
        db.query(LearningPath).delete()
        db.commit()
    except Exception as e:
        print(f"Error clearing data: {e}")
        db.rollback()
        return
    
    # Create a sample learning path
    python_path = LearningPath(
        title="Python Programming Fundamentals",
        description="Learn the basics of Python programming language",
        category="Programming",
        path_metadata={"difficulty": "beginner"}
    )
    db.add(python_path)
    db.flush()
    
    # Create tutorials with chapters and steps
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
                    "content": "Setting up Python development environment",
                    "order": 1,
                    "steps": [
                        {
                            "order": 1,
                            "title": "Download Python",
                            "content": "Visit python.org and download the latest version for your operating system.",
                            "expected_result": "Python installer downloaded successfully",
                            "validation_type": "manual"
                        },
                        {
                            "order": 2,
                            "title": "Install Python",
                            "content": "Run the installer and make sure to check 'Add Python to PATH'.",
                            "expected_result": "Python installed and added to system PATH",
                            "validation_type": "manual"
                        },
                        {
                            "order": 3,
                            "title": "Verify Installation",
                            "content": "Open a terminal/command prompt and run: python --version",
                            "expected_result": "Python version number displayed",
                            "validation_type": "code"
                        }
                    ]
                },
                {
                    "title": "Basic Syntax",
                    "content": "Learning Python's fundamental syntax",
                    "order": 2,
                    "steps": [
                        {
                            "order": 1,
                            "title": "First Python Program",
                            "content": "Create a new file called hello.py and write: print('Hello, World!')",
                            "expected_result": "File created with correct content",
                            "validation_type": "file_check"
                        },
                        {
                            "order": 2,
                            "title": "Run the Program",
                            "content": "In the terminal, navigate to your file location and run: python hello.py",
                            "expected_result": "'Hello, World!' displayed in terminal",
                            "validation_type": "code"
                        },
                        {
                            "order": 3,
                            "title": "Variables",
                            "content": "Create variables of different types: name = 'John', age = 25, height = 1.75",
                            "expected_result": "Variables created and values assigned correctly",
                            "validation_type": "code"
                        }
                    ]
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
                    "content": "Working with Python sequences",
                    "order": 1,
                    "steps": [
                        {
                            "order": 1,
                            "title": "Create a List",
                            "content": "Create a list of numbers: numbers = [1, 2, 3, 4, 5]",
                            "expected_result": "List created successfully",
                            "validation_type": "code"
                        },
                        {
                            "order": 2,
                            "title": "List Operations",
                            "content": "Add an element using append() and remove one using pop()",
                            "expected_result": "List modified correctly",
                            "validation_type": "code"
                        },
                        {
                            "order": 3,
                            "title": "Create a Tuple",
                            "content": "Create an immutable tuple: coordinates = (10, 20)",
                            "expected_result": "Tuple created successfully",
                            "validation_type": "code"
                        }
                    ]
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
        chapters_data = tutorial_data.pop('chapters')
        tutorial = Tutorial(
            learning_path_id=python_path.id,
            **tutorial_data
        )
        db.add(tutorial)
        db.flush()
        
        # Add chapters and steps for this tutorial
        for chapter_data in chapters_data:
            steps_data = chapter_data.pop('steps', [])  # Default to empty list if no steps
            chapter = Chapter(
                tutorial_id=tutorial.id,
                **chapter_data
            )
            db.add(chapter)
            db.flush()
            
            # Add steps for this chapter
            for step_data in steps_data:
                step = Step(
                    chapter_id=chapter.id,
                    **step_data
                )
                db.add(step)
    
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
                    "content": "Setting up Git environment",
                    "order": 1,
                    "steps": [
                        {
                            "order": 1,
                            "title": "Install Git",
                            "content": "Download and install Git for your operating system.",
                            "expected_result": "Git successfully installed",
                            "validation_type": "manual"
                        },
                        {
                            "order": 2,
                            "title": "Configure Git",
                            "content": "Set up your Git username and email using git config commands.",
                            "expected_result": "Git configuration complete",
                            "validation_type": "code"
                        },
                        {
                            "order": 3,
                            "title": "Verify Installation",
                            "content": "Run 'git --version' to verify installation.",
                            "expected_result": "Git version displayed",
                            "validation_type": "code"
                        }
                    ]
                },
                {
                    "title": "Basic Commands",
                    "content": "Learning essential Git commands",
                    "order": 2,
                    "steps": [
                        {
                            "order": 1,
                            "title": "Initialize Repository",
                            "content": "Create a new repository using 'git init'",
                            "expected_result": ".git directory created",
                            "validation_type": "code"
                        },
                        {
                            "order": 2,
                            "title": "Stage Changes",
                            "content": "Add files to staging using 'git add'",
                            "expected_result": "Files staged successfully",
                            "validation_type": "code"
                        },
                        {
                            "order": 3,
                            "title": "Commit Changes",
                            "content": "Commit staged changes using 'git commit'",
                            "expected_result": "Changes committed successfully",
                            "validation_type": "code"
                        }
                    ]
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
                    "content": "Understanding Git branching",
                    "order": 1,
                    "steps": [
                        {
                            "order": 1,
                            "title": "Create Branch",
                            "content": "Create a new branch using 'git branch' or 'git checkout -b'",
                            "expected_result": "New branch created",
                            "validation_type": "code"
                        },
                        {
                            "order": 2,
                            "title": "Switch Branches",
                            "content": "Switch between branches using 'git checkout'",
                            "expected_result": "Successfully switched branches",
                            "validation_type": "code"
                        },
                        {
                            "order": 3,
                            "title": "List Branches",
                            "content": "View all branches using 'git branch'",
                            "expected_result": "Branch list displayed",
                            "validation_type": "code"
                        }
                    ]
                },
                {
                    "title": "Merging Strategies",
                    "content": "Learning about Git merge strategies",
                    "order": 2,
                    "steps": [
                        {
                            "order": 1,
                            "title": "Basic Merge",
                            "content": "Merge a branch using 'git merge'",
                            "expected_result": "Branch merged successfully",
                            "validation_type": "code"
                        },
                        {
                            "order": 2,
                            "title": "Handle Conflicts",
                            "content": "Resolve merge conflicts when they occur",
                            "expected_result": "Conflicts resolved",
                            "validation_type": "manual"
                        },
                        {
                            "order": 3,
                            "title": "Review Merge",
                            "content": "Check merge result using 'git log' and 'git status'",
                            "expected_result": "Merge verified",
                            "validation_type": "code"
                        }
                    ]
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
            steps_data = chapter_data.pop('steps', [])  # Get steps data and remove from chapter_data
            chapter = Chapter(
                tutorial_id=tutorial.id,
                **chapter_data
            )
            db.add(chapter)
            db.flush()
            
            # Add steps for this chapter
            for step_data in steps_data:
                step = Step(
                    chapter_id=chapter.id,
                    **step_data
                )
                db.add(step)
    
    try:
        db.commit()
        print("Sample learning paths, tutorials, and chapters loaded successfully!")
    except Exception as e:
        print(f"Error loading sample data: {e}")
        db.rollback()
    finally:
        db.close()

def load_tutorial_content():
    db = SessionLocal()
    
    # Example tutorial with explicit steps
    tutorial = Tutorial(
        title="Getting Started with Git",
        description="Learn the basics of Git version control"
    )
    
    chapter1 = Chapter(
        title="Basic Git Commands",
        description="Learn essential Git commands",
        content="In this chapter, we'll learn the basic Git commands for version control.",
        order=1
    )
    
    steps = [
        Step(
            order=1,
            title="Initialize Git Repository",
            content="Create a new Git repository using 'git init' command.",
            expected_result="A new .git directory is created",
            validation_type="manual"
        ),
        Step(
            order=2,
            title="Add Files",
            content="Stage files using 'git add' command.",
            expected_result="Files are staged for commit",
            validation_type="manual"
        ),
        Step(
            order=3,
            title="Commit Changes",
            content="Commit staged files using 'git commit -m \"message\"'.",
            expected_result="Changes are committed to repository",
            validation_type="manual"
        )
    ]
    
    chapter1.steps = steps
    tutorial.chapters = [chapter1]
    
    db.add(tutorial)
    db.commit()
    db.close()

if __name__ == "__main__":
    init_db()
    load_sample_data()
    load_tutorial_content() 