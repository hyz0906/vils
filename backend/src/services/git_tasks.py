"""
Background tasks for Git operations
"""

from celery import current_app
from typing import List, Dict, Any
import subprocess
import tempfile
import os
import shutil
from datetime import datetime

from ..core.celery_app import celery_app


@celery_app.task(bind=True)
def fetch_commit_list(self, repository_url: str, good_commit: str, bad_commit: str) -> List[Dict[str, Any]]:
    """
    Fetch commit list between good and bad commits
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "repo")
            
            # Clone repository
            clone_result = subprocess.run([
                "git", "clone", "--bare", repository_url, repo_dir
            ], capture_output=True, text=True, timeout=300)
            
            if clone_result.returncode != 0:
                raise Exception(f"Failed to clone repository: {clone_result.stderr}")
            
            # Get commit list between good and bad commits
            commit_list_result = subprocess.run([
                "git", "rev-list", "--reverse", f"{good_commit}..{bad_commit}"
            ], cwd=repo_dir, capture_output=True, text=True, timeout=60)
            
            if commit_list_result.returncode != 0:
                raise Exception(f"Failed to get commit list: {commit_list_result.stderr}")
            
            commit_hashes = commit_list_result.stdout.strip().split('\n')
            if not commit_hashes or commit_hashes == ['']:
                raise Exception("No commits found between good and bad commits")
            
            # Get detailed information for each commit
            commits = []
            for commit_hash in commit_hashes[:1000]:  # Limit to 1000 commits
                commit_info_result = subprocess.run([
                    "git", "show", "--format=%H|%an|%ae|%ad|%s", "--no-patch", commit_hash
                ], cwd=repo_dir, capture_output=True, text=True, timeout=30)
                
                if commit_info_result.returncode == 0:
                    info = commit_info_result.stdout.strip().split('|', 4)
                    if len(info) >= 5:
                        commits.append({
                            "hash": info[0],
                            "author_name": info[1],
                            "author_email": info[2],
                            "date": info[3],
                            "message": info[4],
                            "short_hash": info[0][:8]
                        })
            
            return commits
            
    except Exception as e:
        # Retry on failure
        if self.request.retries < 3:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        raise


@celery_app.task(bind=True)
def validate_commit(self, repository_url: str, commit_hash: str) -> Dict[str, Any]:
    """
    Validate that a commit exists in the repository
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "repo")
            
            # Clone repository
            clone_result = subprocess.run([
                "git", "clone", "--bare", repository_url, repo_dir
            ], capture_output=True, text=True, timeout=300)
            
            if clone_result.returncode != 0:
                raise Exception(f"Failed to clone repository: {clone_result.stderr}")
            
            # Check if commit exists
            commit_check_result = subprocess.run([
                "git", "cat-file", "-e", commit_hash
            ], cwd=repo_dir, capture_output=True, text=True, timeout=30)
            
            if commit_check_result.returncode != 0:
                return {
                    "valid": False,
                    "error": f"Commit {commit_hash} not found in repository"
                }
            
            # Get commit information
            commit_info_result = subprocess.run([
                "git", "show", "--format=%H|%an|%ae|%ad|%s", "--no-patch", commit_hash
            ], cwd=repo_dir, capture_output=True, text=True, timeout=30)
            
            if commit_info_result.returncode != 0:
                return {
                    "valid": False,
                    "error": f"Failed to get commit information: {commit_info_result.stderr}"
                }
            
            info = commit_info_result.stdout.strip().split('|', 4)
            if len(info) >= 5:
                return {
                    "valid": True,
                    "commit": {
                        "hash": info[0],
                        "author_name": info[1],
                        "author_email": info[2],
                        "date": info[3],
                        "message": info[4],
                        "short_hash": info[0][:8]
                    }
                }
            
            return {
                "valid": False,
                "error": "Failed to parse commit information"
            }
            
    except Exception as e:
        # Retry on failure
        if self.request.retries < 2:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {
            "valid": False,
            "error": str(e)
        }


@celery_app.task
def get_commit_diff(repository_url: str, commit1: str, commit2: str) -> Dict[str, Any]:
    """
    Get diff between two commits
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "repo")
            
            # Clone repository
            clone_result = subprocess.run([
                "git", "clone", "--bare", repository_url, repo_dir
            ], capture_output=True, text=True, timeout=300)
            
            if clone_result.returncode != 0:
                raise Exception(f"Failed to clone repository: {clone_result.stderr}")
            
            # Get diff stats
            diff_stats_result = subprocess.run([
                "git", "diff", "--stat", commit1, commit2
            ], cwd=repo_dir, capture_output=True, text=True, timeout=60)
            
            # Get diff content (limited)
            diff_content_result = subprocess.run([
                "git", "diff", "--no-color", commit1, commit2
            ], cwd=repo_dir, capture_output=True, text=True, timeout=60)
            
            # Get list of changed files
            changed_files_result = subprocess.run([
                "git", "diff", "--name-only", commit1, commit2
            ], cwd=repo_dir, capture_output=True, text=True, timeout=30)
            
            changed_files = []
            if changed_files_result.returncode == 0:
                changed_files = changed_files_result.stdout.strip().split('\n')
                changed_files = [f for f in changed_files if f]
            
            return {
                "success": True,
                "stats": diff_stats_result.stdout if diff_stats_result.returncode == 0 else "",
                "content": diff_content_result.stdout[:50000] if diff_content_result.returncode == 0 else "",  # Limit size
                "changed_files": changed_files,
                "commit1": commit1,
                "commit2": commit2
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task
def analyze_repository(repository_url: str) -> Dict[str, Any]:
    """
    Analyze repository structure and provide metadata
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "repo")
            
            # Clone repository
            clone_result = subprocess.run([
                "git", "clone", "--depth=1", repository_url, repo_dir
            ], capture_output=True, text=True, timeout=300)
            
            if clone_result.returncode != 0:
                raise Exception(f"Failed to clone repository: {clone_result.stderr}")
            
            analysis = {
                "repository_url": repository_url,
                "analysis_date": datetime.utcnow().isoformat(),
                "branches": [],
                "tags": [],
                "build_files": [],
                "languages": {},
                "total_commits": 0
            }
            
            # Get branches
            branches_result = subprocess.run([
                "git", "branch", "-r"
            ], cwd=repo_dir, capture_output=True, text=True, timeout=30)
            
            if branches_result.returncode == 0:
                branches = branches_result.stdout.strip().split('\n')
                analysis["branches"] = [b.strip().replace('origin/', '') for b in branches if b.strip() and not b.strip().startswith('origin/HEAD')]
            
            # Get tags
            tags_result = subprocess.run([
                "git", "tag", "-l"
            ], cwd=repo_dir, capture_output=True, text=True, timeout=30)
            
            if tags_result.returncode == 0:
                tags = tags_result.stdout.strip().split('\n')
                analysis["tags"] = [t for t in tags if t]
            
            # Find build files
            build_files = []
            common_build_files = [
                "Makefile", "makefile", "CMakeLists.txt", "build.gradle", "pom.xml",
                "package.json", "setup.py", "Cargo.toml", "go.mod", "requirements.txt",
                "Dockerfile", "docker-compose.yml", ".github/workflows", ".gitlab-ci.yml"
            ]
            
            for root, dirs, files in os.walk(repo_dir):
                for file in files:
                    if file in common_build_files:
                        rel_path = os.path.relpath(os.path.join(root, file), repo_dir)
                        build_files.append(rel_path)
                
                # Check for workflow directories
                for dir_name in dirs:
                    if dir_name in ['.github', '.gitlab']:
                        rel_path = os.path.relpath(os.path.join(root, dir_name), repo_dir)
                        build_files.append(rel_path)
            
            analysis["build_files"] = build_files
            
            # Count total commits (shallow clone shows only recent)
            commit_count_result = subprocess.run([
                "git", "rev-list", "--count", "HEAD"
            ], cwd=repo_dir, capture_output=True, text=True, timeout=30)
            
            if commit_count_result.returncode == 0:
                analysis["total_commits"] = int(commit_count_result.stdout.strip())
            
            return analysis
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "repository_url": repository_url
        }