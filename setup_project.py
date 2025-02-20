#!/usr/bin/env python3
# setup_project.py

import shutil
from pathlib import Path

def create_directory_structure():
    """Create the project directory structure."""
    # Define the project structure
    directories = [
        "app/api/routes",
        "app/cli",
        "app/core",
        "app/models",
        "app/services/social_media",
        "app/utils",
        "tests",
    ]

    # Create base directories
    root = Path(".")
    for dir_path in directories:
        (root / dir_path).mkdir(parents=True, exist_ok=True)

def move_files():
    """Move existing files to their new locations."""
    file_moves = [
        # Social media files
        ("manager.py", "app/services/social_media/manager.py"),
        ("base.py", "app/services/social_media/base.py"),
        ("twitter.py", "app/services/social_media/twitter.py"),
        ("linkedin.py", "app/services/social_media/linkedin.py"),
        ("facebook.py", "app/services/social_media/facebook.py"),
        ("__init__.py", "app/services/social_media/__init__.py"),

        # Move preprint_forge.py content will be split into multiple files
        # We'll keep the original for reference
        ("preprint_forge.py", "app/services/paper_generator.py"),

        # Create necessary __init__.py files
        ("", "app/__init__.py"),
        ("", "app/api/__init__.py"),
        ("", "app/api/routes/__init__.py"),
        ("", "app/cli/__init__.py"),
        ("", "app/core/__init__.py"),
        ("", "app/models/__init__.py"),
        ("", "app/services/__init__.py"),
        ("", "app/utils/__init__.py"),
    ]

    for source, dest in file_moves:
        try:
            if source and Path(source).exists():
                Path(dest).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                print(f"Moved {source} to {dest}")
            elif not source:  # Create empty __init__.py
                Path(dest).touch()
                print(f"Created {dest}")
        except Exception as e:
            print(f"Error moving {source} to {dest}: {e}")

def create_additional_files():
    """Create additional necessary files if they don't exist."""
    files_to_create = {
        "app/core/config.py": """from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # Add your settings here
    pass

settings = Settings()
""",
        "app/core/logging.py": """import logging

def setup_logging():
    # Add your logging configuration here
    pass
""",
        "app/models/paper.py": """from pydantic import BaseModel
from typing import Optional

class Paper(BaseModel):
    # Add your paper model here
    pass
""",
        "tests/__init__.py": "",
}
    }

    for file_path, content in files_to_create.items():
        path = Path(file_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"Created {file_path}")

def backup_existing_files():
    """Create backup of existing files."""
    backup_dir = Path("backup_original_files")
    backup_dir.mkdir(exist_ok=True)

    files_to_backup = [
        "preprint_forge.py",
        "manager.py",
        "base.py",
        "twitter.py",
        "linkedin.py",
        "facebook.py",
        "__init__.py",
    ]

    for file_name in files_to_backup:
        source = Path(file_name)
        if source.exists():
            shutil.copy2(source, backup_dir / source.name)
            print(f"Backed up {file_name}")

def main():
    """Main function to set up the project structure."""
    print("Starting project restructuring...")

    # Backup existing files
    print("\nBacking up existing files...")
    backup_existing_files()

    # Create directory structure
    print("\nCreating directory structure...")
    create_directory_structure()

    # Move files to new locations
    print("\nMoving files to new locations...")
    move_files()

    # Create additional files
    print("\nCreating additional files...")
    create_additional_files()

    print("\nProject restructuring complete!")
    print("""
Next steps:
1. Review the backup_original_files directory to ensure all files were backed up
2. Check the new directory structure
3. Update import statements in moved files
4. Run tests to ensure everything works
5. Delete backup files if everything is working correctly
""")

if __name__ == "__main__":
    main()
