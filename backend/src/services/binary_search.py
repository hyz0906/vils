"""Binary search algorithm implementation for issue localization."""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..models.project import Tag


@dataclass
class TagInfo:
    """Tag information for binary search."""
    
    id: str
    name: str
    sequence_number: int
    commit_hash: str


@dataclass
class BinarySearchState:
    """State of binary search process."""
    
    good_index: int
    bad_index: int
    current_iteration: int
    tested_tags: Dict[str, str]  # tag_id -> 'working' | 'broken'
    total_tags: int


@dataclass
class SearchCandidate:
    """Candidate tag for testing."""
    
    position: int
    tag: TagInfo
    selected: bool = False


class BinarySearchEngine:
    """
    Implements the binary search algorithm for issue localization.
    Generates exactly 10 evenly distributed candidates per iteration.
    """
    
    def __init__(self, tags: List[Tag]):
        """Initialize the binary search engine.
        
        Args:
            tags: List of tags sorted by sequence number
        """
        # Sort tags by sequence number to ensure correct order
        self.tags = sorted(tags, key=lambda x: x.sequence_number or 0)
        self.tag_map = {str(tag.id): TagInfo(
            id=str(tag.id),
            name=tag.name,
            sequence_number=tag.sequence_number or 0,
            commit_hash=tag.commit_hash
        ) for tag in self.tags}
        
    def get_tag_info(self, tag_id: str) -> Optional[TagInfo]:
        """Get tag information by ID.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Tag information or None if not found
        """
        return self.tag_map.get(tag_id)
        
    def find_tag_index(self, tag_id: str) -> Optional[int]:
        """Find the index of a tag in the sorted list.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Index of the tag or None if not found
        """
        for i, tag in enumerate(self.tags):
            if str(tag.id) == tag_id:
                return i
        return None
    
    def generate_candidates(
        self, 
        good_index: int, 
        bad_index: int
    ) -> List[SearchCandidate]:
        """Generate exactly 10 candidate tags using binary division.
        
        Args:
            good_index: Index of the last known good tag
            bad_index: Index of the first known bad tag
            
        Returns:
            List of candidate tags for testing
            
        Raises:
            ValueError: If bad_index <= good_index
        """
        if bad_index <= good_index:
            raise ValueError("Bad index must be greater than good index")
            
        range_size = bad_index - good_index - 1
        
        # If range is too small, return all available tags
        if range_size <= 10:
            candidates = []
            for i in range(good_index + 1, bad_index):
                tag_info = TagInfo(
                    id=str(self.tags[i].id),
                    name=self.tags[i].name,
                    sequence_number=self.tags[i].sequence_number or 0,
                    commit_hash=self.tags[i].commit_hash
                )
                candidates.append(SearchCandidate(position=i, tag=tag_info))
            return candidates
        
        # Calculate interval size for 10 evenly distributed points
        # Divide the range into 11 sections, pick the boundaries
        interval = (bad_index - good_index) / 11.0
        
        candidates = []
        for i in range(1, 11):  # Generate exactly 10 points
            position = good_index + int(interval * i)
            
            # Ensure we don't exceed bounds and don't duplicate positions
            if position < bad_index and position > good_index:
                # Check if we already have this position
                if not any(c.position == position for c in candidates):
                    tag_info = TagInfo(
                        id=str(self.tags[position].id),
                        name=self.tags[position].name,
                        sequence_number=self.tags[position].sequence_number or 0,
                        commit_hash=self.tags[position].commit_hash
                    )
                    candidates.append(SearchCandidate(position=position, tag=tag_info))
        
        # Sort candidates by position
        candidates.sort(key=lambda x: x.position)
        
        # If we have fewer than 10 candidates due to rounding, 
        # add more evenly distributed ones
        if len(candidates) < 10 and range_size > 10:
            # Fill in gaps with additional candidates
            positions_used = {c.position for c in candidates}
            
            # Try to add more positions evenly distributed
            for i in range(good_index + 1, bad_index):
                if len(candidates) >= 10:
                    break
                if i not in positions_used:
                    # Calculate how "good" this position is for even distribution
                    tag_info = TagInfo(
                        id=str(self.tags[i].id),
                        name=self.tags[i].name,
                        sequence_number=self.tags[i].sequence_number or 0,
                        commit_hash=self.tags[i].commit_hash
                    )
                    candidates.append(SearchCandidate(position=i, tag=tag_info))
            
            # Re-sort and take only the 10 most evenly distributed
            candidates.sort(key=lambda x: x.position)
            if len(candidates) > 10:
                # Keep the 10 most evenly distributed candidates
                step = len(candidates) / 10.0
                selected_candidates = []
                for i in range(10):
                    idx = int(i * step)
                    selected_candidates.append(candidates[idx])
                candidates = selected_candidates
        
        return candidates
    
    def update_range(
        self,
        state: BinarySearchState,
        feedback: Dict[str, str]  # tag_id -> 'working' | 'broken'
    ) -> Tuple[int, int]:
        """Update search range based on user feedback.
        
        Args:
            state: Current search state
            feedback: User feedback for tested tags
            
        Returns:
            New (good_index, bad_index) tuple
        """
        # Update tested tags
        state.tested_tags.update(feedback)
        
        # Find the rightmost working tag
        new_good = state.good_index
        for tag_id, result in feedback.items():
            if result == 'working':
                tag_index = self.find_tag_index(tag_id)
                if tag_index is not None:
                    new_good = max(new_good, tag_index)
        
        # Find the leftmost broken tag
        new_bad = state.bad_index
        for tag_id, result in feedback.items():
            if result == 'broken':
                tag_index = self.find_tag_index(tag_id)
                if tag_index is not None:
                    new_bad = min(new_bad, tag_index)
        
        return new_good, new_bad
    
    def is_complete(self, good_index: int, bad_index: int) -> bool:
        """Check if search is complete (adjacent tags).
        
        Args:
            good_index: Index of last known good tag
            bad_index: Index of first known bad tag
            
        Returns:
            True if search is complete
        """
        return bad_index - good_index == 1
    
    def get_problematic_tag(self, good_index: int, bad_index: int) -> Optional[TagInfo]:
        """Get the identified problematic tag.
        
        Args:
            good_index: Index of last known good tag
            bad_index: Index of first known bad tag
            
        Returns:
            The problematic tag if search is complete
        """
        if self.is_complete(good_index, bad_index):
            tag = self.tags[bad_index]
            return TagInfo(
                id=str(tag.id),
                name=tag.name,
                sequence_number=tag.sequence_number or 0,
                commit_hash=tag.commit_hash
            )
        return None
    
    def calculate_progress(self, good_index: int, bad_index: int, total_tags: int) -> float:
        """Calculate the progress of the binary search as a percentage.
        
        Args:
            good_index: Index of last known good tag
            bad_index: Index of first known bad tag
            total_tags: Total number of tags in the original range
            
        Returns:
            Progress as a percentage (0-100)
        """
        if total_tags <= 1:
            return 100.0
            
        current_range = bad_index - good_index - 1
        if current_range <= 0:
            return 100.0
            
        # Progress is inversely related to the remaining range size
        progress = (1 - (current_range / total_tags)) * 100
        return min(100.0, max(0.0, progress))
    
    def estimate_iterations_remaining(self, good_index: int, bad_index: int) -> int:
        """Estimate how many more iterations are needed.
        
        Args:
            good_index: Index of last known good tag
            bad_index: Index of first known bad tag
            
        Returns:
            Estimated number of remaining iterations
        """
        current_range = bad_index - good_index - 1
        if current_range <= 0:
            return 0
        
        # Binary search: log2(n) iterations to narrow down to 1 item
        # Assuming we test ~5 candidates per iteration on average
        iterations = math.ceil(math.log2(current_range) / math.log2(5))
        return max(0, iterations)
    
    def get_search_statistics(
        self, 
        good_index: int, 
        bad_index: int, 
        current_iteration: int,
        total_original_range: int
    ) -> Dict[str, any]:
        """Get comprehensive search statistics.
        
        Args:
            good_index: Index of last known good tag
            bad_index: Index of first known bad tag
            current_iteration: Current iteration number
            total_original_range: Original range size
            
        Returns:
            Dictionary with search statistics
        """
        current_range = bad_index - good_index - 1
        progress = self.calculate_progress(good_index, bad_index, total_original_range)
        remaining_iterations = self.estimate_iterations_remaining(good_index, bad_index)
        
        return {
            "current_iteration": current_iteration,
            "current_range_size": current_range,
            "original_range_size": total_original_range,
            "progress_percentage": round(progress, 1),
            "estimated_remaining_iterations": remaining_iterations,
            "is_complete": self.is_complete(good_index, bad_index),
            "tags_eliminated": total_original_range - current_range,
            "efficiency": round((total_original_range - current_range) / max(1, current_iteration), 2)
        }