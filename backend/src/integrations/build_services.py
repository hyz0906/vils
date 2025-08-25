"""Build service integrations for CI/CD platforms."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import ClientTimeout

from ..auth.encryption import decrypt_api_key


class BuildStatus:
    """Build status constants."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BuildServiceInterface(ABC):
    """Abstract base class for build service integrations."""
    
    @abstractmethod
    async def trigger_build(
        self, 
        project: str, 
        branch: str, 
        tag: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger a build for a specific tag."""
        pass
    
    @abstractmethod
    async def get_build_status(self, build_id: str) -> str:
        """Get the current status of a build."""
        pass
    
    @abstractmethod
    async def get_build_logs(self, build_id: str) -> str:
        """Retrieve build logs."""
        pass
    
    @abstractmethod
    async def cancel_build(self, build_id: str) -> bool:
        """Cancel a running build."""
        pass


class JenkinsIntegration(BuildServiceInterface):
    """Jenkins CI/CD integration."""
    
    def __init__(self, base_url: str, api_token: str):
        """Initialize Jenkins integration.
        
        Args:
            base_url: Jenkins base URL
            api_token: Jenkins API token (encrypted)
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = decrypt_api_key(api_token)
        self.timeout = ClientTimeout(total=30)
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get HTTP session with authentication."""
        auth = aiohttp.BasicAuth('api', self.api_token)
        return aiohttp.ClientSession(auth=auth, timeout=self.timeout)
    
    async def trigger_build(
        self, 
        project: str, 
        branch: str, 
        tag: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger a Jenkins build.
        
        Args:
            project: Jenkins job name
            branch: Git branch name
            tag: Git tag name
            parameters: Build parameters
            
        Returns:
            Build information dictionary
        """
        async with await self._get_session() as session:
            # Prepare build parameters
            build_params = {
                'token': self.api_token,
                'BRANCH': branch,
                'TAG': tag,
                **parameters
            }
            
            # Trigger build
            url = f"{self.base_url}/job/{project}/buildWithParameters"
            
            async with session.post(url, params=build_params) as response:
                if response.status == 201:
                    # Extract build queue URL from Location header
                    location = response.headers.get('Location', '')
                    queue_id = location.split('/')[-2] if location else None
                    
                    return {
                        'build_id': queue_id,
                        'status': BuildStatus.PENDING,
                        'url': f"{self.base_url}/job/{project}",
                        'service': 'jenkins',
                        'queue_url': location
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to trigger Jenkins build: {response.status} - {error_text}")
    
    async def get_build_status(self, build_id: str) -> str:
        """Get Jenkins build status.
        
        Args:
            build_id: Jenkins build/queue ID
            
        Returns:
            Build status string
        """
        async with await self._get_session() as session:
            # First check if it's in the queue
            queue_url = f"{self.base_url}/queue/item/{build_id}/api/json"
            
            try:
                async with session.get(queue_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('cancelled'):
                            return BuildStatus.CANCELLED
                        elif data.get('executable'):
                            # Build has started, get actual build status
                            build_url = data['executable']['url'] + 'api/json'
                            
                            async with session.get(build_url) as build_response:
                                if build_response.status == 200:
                                    build_data = await build_response.json()
                                    
                                    if build_data.get('building'):
                                        return BuildStatus.RUNNING
                                    elif build_data.get('result') == 'SUCCESS':
                                        return BuildStatus.SUCCESS
                                    elif build_data.get('result') == 'FAILURE':
                                        return BuildStatus.FAILED
                                    elif build_data.get('result') == 'ABORTED':
                                        return BuildStatus.CANCELLED
                        else:
                            return BuildStatus.PENDING
            except Exception:
                # If queue check fails, try direct build check
                build_url = f"{self.base_url}/job/unknown/{build_id}/api/json"
                
                try:
                    async with session.get(build_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('building'):
                                return BuildStatus.RUNNING
                            elif data.get('result') == 'SUCCESS':
                                return BuildStatus.SUCCESS
                            elif data.get('result') == 'FAILURE':
                                return BuildStatus.FAILED
                            else:
                                return BuildStatus.CANCELLED
                except Exception:
                    pass
            
            return BuildStatus.PENDING
    
    async def get_build_logs(self, build_id: str) -> str:
        """Get Jenkins build logs.
        
        Args:
            build_id: Jenkins build ID
            
        Returns:
            Build logs as string
        """
        async with await self._get_session() as session:
            # Try to get logs from build
            log_url = f"{self.base_url}/job/unknown/{build_id}/consoleText"
            
            try:
                async with session.get(log_url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        return f"Logs not available (HTTP {response.status})"
            except Exception as e:
                return f"Error retrieving logs: {str(e)}"
    
    async def cancel_build(self, build_id: str) -> bool:
        """Cancel a Jenkins build.
        
        Args:
            build_id: Jenkins build/queue ID
            
        Returns:
            True if cancellation was successful
        """
        async with await self._get_session() as session:
            # Try to cancel queue item first
            cancel_url = f"{self.base_url}/queue/cancelItem"
            
            try:
                async with session.post(cancel_url, params={'id': build_id}) as response:
                    return response.status == 200
            except Exception:
                return False


class GitHubActionsIntegration(BuildServiceInterface):
    """GitHub Actions integration."""
    
    def __init__(self, token: str, owner: str, repo: str):
        """Initialize GitHub Actions integration.
        
        Args:
            token: GitHub API token (encrypted)
            owner: Repository owner
            repo: Repository name
        """
        self.token = decrypt_api_key(token)
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.timeout = ClientTimeout(total=30)
        
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for GitHub API."""
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'VILS/1.0'
        }
    
    async def trigger_build(
        self, 
        project: str, 
        branch: str, 
        tag: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger a GitHub Actions workflow.
        
        Args:
            project: Workflow filename or ID
            branch: Git branch name
            tag: Git tag name
            parameters: Workflow inputs
            
        Returns:
            Build information dictionary
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Trigger workflow dispatch
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/workflows/{project}/dispatches"
            
            payload = {
                'ref': tag,
                'inputs': {
                    'tag': tag,
                    'branch': branch,
                    **parameters
                }
            }
            
            async with session.post(url, headers=self._get_headers(), json=payload) as response:
                if response.status == 204:
                    # Workflow dispatch successful, get recent runs to find our run
                    await asyncio.sleep(1)  # Give GitHub a moment to create the run
                    
                    runs_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs"
                    params = {
                        'per_page': 5,
                        'status': 'queued,in_progress'
                    }
                    
                    async with session.get(runs_url, headers=self._get_headers(), params=params) as runs_response:
                        if runs_response.status == 200:
                            runs_data = await runs_response.json()
                            
                            if runs_data.get('workflow_runs'):
                                # Get the most recent run (likely ours)
                                run = runs_data['workflow_runs'][0]
                                return {
                                    'build_id': str(run['id']),
                                    'status': BuildStatus.PENDING,
                                    'url': run['html_url'],
                                    'service': 'github_actions'
                                }
                    
                    # Fallback if we can't find the specific run
                    return {
                        'build_id': f"dispatch_{int(asyncio.get_event_loop().time())}",
                        'status': BuildStatus.PENDING,
                        'url': f"https://github.com/{self.owner}/{self.repo}/actions",
                        'service': 'github_actions'
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to trigger GitHub Actions workflow: {response.status} - {error_text}")
    
    async def get_build_status(self, build_id: str) -> str:
        """Get GitHub Actions run status.
        
        Args:
            build_id: GitHub Actions run ID
            
        Returns:
            Build status string
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs/{build_id}"
            
            try:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        status = data.get('status', '')
                        conclusion = data.get('conclusion', '')
                        
                        if status == 'queued':
                            return BuildStatus.PENDING
                        elif status == 'in_progress':
                            return BuildStatus.RUNNING
                        elif status == 'completed':
                            if conclusion == 'success':
                                return BuildStatus.SUCCESS
                            elif conclusion == 'failure':
                                return BuildStatus.FAILED
                            elif conclusion == 'cancelled':
                                return BuildStatus.CANCELLED
                            else:
                                return BuildStatus.FAILED
                        else:
                            return BuildStatus.PENDING
                    else:
                        return BuildStatus.PENDING
            except Exception:
                return BuildStatus.PENDING
    
    async def get_build_logs(self, build_id: str) -> str:
        """Get GitHub Actions run logs.
        
        Args:
            build_id: GitHub Actions run ID
            
        Returns:
            Build logs as string
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Get logs download URL
            logs_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs/{build_id}/logs"
            
            try:
                async with session.get(logs_url, headers=self._get_headers(), allow_redirects=True) as response:
                    if response.status == 200:
                        # GitHub returns a zip file with logs
                        content = await response.read()
                        # In a real implementation, you'd extract and parse the zip
                        return f"Logs available (zip file, {len(content)} bytes). Full log parsing not implemented."
                    else:
                        return f"Logs not available (HTTP {response.status})"
            except Exception as e:
                return f"Error retrieving logs: {str(e)}"
    
    async def cancel_build(self, build_id: str) -> bool:
        """Cancel a GitHub Actions run.
        
        Args:
            build_id: GitHub Actions run ID
            
        Returns:
            True if cancellation was successful
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/actions/runs/{build_id}/cancel"
            
            try:
                async with session.post(url, headers=self._get_headers()) as response:
                    return response.status == 202
            except Exception:
                return False


class GitLabCIIntegration(BuildServiceInterface):
    """GitLab CI integration."""
    
    def __init__(self, base_url: str, token: str, project_id: str):
        """Initialize GitLab CI integration.
        
        Args:
            base_url: GitLab instance URL
            token: GitLab API token (encrypted)
            project_id: GitLab project ID
        """
        self.base_url = base_url.rstrip('/')
        self.token = decrypt_api_key(token)
        self.project_id = project_id
        self.timeout = ClientTimeout(total=30)
        
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for GitLab API."""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    async def trigger_build(
        self, 
        project: str, 
        branch: str, 
        tag: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger a GitLab CI pipeline.
        
        Args:
            project: Pipeline configuration (unused, uses default)
            branch: Git branch name
            tag: Git tag name
            parameters: Pipeline variables
            
        Returns:
            Build information dictionary
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Trigger pipeline
            url = f"{self.base_url}/api/v4/projects/{self.project_id}/pipeline"
            
            payload = {
                'ref': tag,
                'variables': [
                    {'key': 'TAG', 'value': tag},
                    {'key': 'BRANCH', 'value': branch},
                    *[{'key': k, 'value': str(v)} for k, v in parameters.items()]
                ]
            }
            
            async with session.post(url, headers=self._get_headers(), json=payload) as response:
                if response.status == 201:
                    data = await response.json()
                    
                    return {
                        'build_id': str(data['id']),
                        'status': BuildStatus.PENDING,
                        'url': data['web_url'],
                        'service': 'gitlab_ci'
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to trigger GitLab CI pipeline: {response.status} - {error_text}")
    
    async def get_build_status(self, build_id: str) -> str:
        """Get GitLab CI pipeline status.
        
        Args:
            build_id: GitLab pipeline ID
            
        Returns:
            Build status string
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/api/v4/projects/{self.project_id}/pipelines/{build_id}"
            
            try:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status', '')
                        
                        status_map = {
                            'created': BuildStatus.PENDING,
                            'waiting_for_resource': BuildStatus.PENDING,
                            'preparing': BuildStatus.PENDING,
                            'pending': BuildStatus.PENDING,
                            'running': BuildStatus.RUNNING,
                            'success': BuildStatus.SUCCESS,
                            'failed': BuildStatus.FAILED,
                            'canceled': BuildStatus.CANCELLED,
                            'skipped': BuildStatus.CANCELLED,
                        }
                        
                        return status_map.get(status, BuildStatus.PENDING)
                    else:
                        return BuildStatus.PENDING
            except Exception:
                return BuildStatus.PENDING
    
    async def get_build_logs(self, build_id: str) -> str:
        """Get GitLab CI pipeline logs.
        
        Args:
            build_id: GitLab pipeline ID
            
        Returns:
            Build logs as string
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Get jobs for the pipeline
            jobs_url = f"{self.base_url}/api/v4/projects/{self.project_id}/pipelines/{build_id}/jobs"
            
            try:
                async with session.get(jobs_url, headers=self._get_headers()) as response:
                    if response.status == 200:
                        jobs = await response.json()
                        logs = []
                        
                        for job in jobs:
                            job_id = job['id']
                            job_name = job['name']
                            
                            # Get logs for each job
                            log_url = f"{self.base_url}/api/v4/projects/{self.project_id}/jobs/{job_id}/trace"
                            
                            async with session.get(log_url, headers=self._get_headers()) as log_response:
                                if log_response.status == 200:
                                    job_logs = await log_response.text()
                                    logs.append(f"=== Job: {job_name} ===\n{job_logs}\n")
                        
                        return "\n".join(logs) if logs else "No logs available"
                    else:
                        return f"Jobs not available (HTTP {response.status})"
            except Exception as e:
                return f"Error retrieving logs: {str(e)}"
    
    async def cancel_build(self, build_id: str) -> bool:
        """Cancel a GitLab CI pipeline.
        
        Args:
            build_id: GitLab pipeline ID
            
        Returns:
            True if cancellation was successful
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/api/v4/projects/{self.project_id}/pipelines/{build_id}/cancel"
            
            try:
                async with session.post(url, headers=self._get_headers()) as response:
                    return response.status == 200
            except Exception:
                return False


class BuildServiceFactory:
    """Factory for creating build service instances."""
    
    @staticmethod
    def create_service(
        service_type: str, 
        config: Dict[str, Any]
    ) -> BuildServiceInterface:
        """Create a build service instance.
        
        Args:
            service_type: Type of build service
            config: Service configuration
            
        Returns:
            Build service instance
            
        Raises:
            ValueError: If service type is not supported
        """
        if service_type == 'jenkins':
            return JenkinsIntegration(
                base_url=config['base_url'],
                api_token=config['api_token']
            )
        elif service_type == 'github_actions':
            return GitHubActionsIntegration(
                token=config['token'],
                owner=config['owner'],
                repo=config['repo']
            )
        elif service_type == 'gitlab_ci':
            return GitLabCIIntegration(
                base_url=config['base_url'],
                token=config['token'],
                project_id=config['project_id']
            )
        else:
            raise ValueError(f"Unsupported build service: {service_type}")
    
    @staticmethod
    def get_supported_services() -> list[str]:
        """Get list of supported build services.
        
        Returns:
            List of supported service types
        """
        return ['jenkins', 'github_actions', 'gitlab_ci']