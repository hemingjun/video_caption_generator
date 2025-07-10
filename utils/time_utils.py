"""
Time-related utility functions for Video Caption Generator
"""
from datetime import timedelta
from typing import Tuple, Optional


def seconds_to_time_string(seconds: float, format_type: str = "srt") -> str:
    """
    Convert seconds to formatted time string
    
    Args:
        seconds: Time in seconds
        format_type: Output format ('srt', 'vtt', 'readable')
        
    Returns:
        Formatted time string
    """
    if format_type == "srt":
        return format_srt_time(seconds)
    elif format_type == "vtt":
        return format_vtt_time(seconds)
    elif format_type == "readable":
        return format_readable_time(seconds)
    else:
        raise ValueError(f"Unknown format type: {format_type}")


def format_srt_time(seconds: float) -> str:
    """
    Format seconds to SRT timestamp (HH:MM:SS,mmm)
    
    Args:
        seconds: Time in seconds
        
    Returns:
        SRT formatted time string
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    milliseconds = int((td.total_seconds() % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def format_vtt_time(seconds: float) -> str:
    """
    Format seconds to WebVTT timestamp (HH:MM:SS.mmm)
    
    Args:
        seconds: Time in seconds
        
    Returns:
        WebVTT formatted time string
    """
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    milliseconds = int((td.total_seconds() % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def format_readable_time(seconds: float) -> str:
    """
    Format seconds to human-readable time
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Human-readable time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def parse_time_string(time_str: str, format_type: str = "auto") -> float:
    """
    Parse time string to seconds
    
    Args:
        time_str: Time string to parse
        format_type: Format type ('srt', 'vtt', 'auto')
        
    Returns:
        Time in seconds
    """
    if format_type == "auto":
        if "," in time_str:
            format_type = "srt"
        elif "." in time_str and time_str.count(":") == 2:
            format_type = "vtt"
    
    if format_type == "srt":
        return parse_srt_time(time_str)
    elif format_type == "vtt":
        return parse_vtt_time(time_str)
    else:
        raise ValueError(f"Cannot parse time string: {time_str}")


def parse_srt_time(time_str: str) -> float:
    """
    Parse SRT timestamp to seconds
    
    Args:
        time_str: SRT time string (HH:MM:SS,mmm)
        
    Returns:
        Time in seconds
    """
    time_part, ms_part = time_str.split(",")
    hours, minutes, seconds = map(int, time_part.split(":"))
    milliseconds = int(ms_part)
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    return total_seconds


def parse_vtt_time(time_str: str) -> float:
    """
    Parse WebVTT timestamp to seconds
    
    Args:
        time_str: WebVTT time string (HH:MM:SS.mmm)
        
    Returns:
        Time in seconds
    """
    time_part, ms_part = time_str.rsplit(".", 1)
    hours, minutes, seconds = map(int, time_part.split(":"))
    milliseconds = int(ms_part)
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    return total_seconds


def calculate_duration(start_time: float, end_time: float) -> float:
    """
    Calculate duration between two times
    
    Args:
        start_time: Start time in seconds
        end_time: End time in seconds
        
    Returns:
        Duration in seconds
    """
    return max(0, end_time - start_time)


def shift_timestamps(
    segments: list,
    offset: float,
    start_key: str = "start",
    end_key: str = "end"
) -> list:
    """
    Shift all timestamps in segments by offset
    
    Args:
        segments: List of segments with timestamps
        offset: Time offset in seconds (positive or negative)
        start_key: Key name for start time
        end_key: Key name for end time
        
    Returns:
        Updated segments list
    """
    for segment in segments:
        if start_key in segment:
            segment[start_key] = max(0, segment[start_key] + offset)
        if end_key in segment:
            segment[end_key] = max(0, segment[end_key] + offset)
    
    return segments


def merge_overlapping_segments(
    segments: list,
    overlap_threshold: float = 0.1,
    start_key: str = "start",
    end_key: str = "end",
    text_key: str = "text"
) -> list:
    """
    Merge segments with overlapping timestamps
    
    Args:
        segments: List of segments to merge
        overlap_threshold: Maximum gap to consider as overlap
        start_key: Key name for start time
        end_key: Key name for end time
        text_key: Key name for text content
        
    Returns:
        Merged segments list
    """
    if not segments:
        return []
    
    # Sort by start time
    sorted_segments = sorted(segments, key=lambda x: x.get(start_key, 0))
    
    merged = []
    current = sorted_segments[0].copy()
    
    for segment in sorted_segments[1:]:
        # Check if segments overlap or are close enough
        if segment[start_key] - current[end_key] <= overlap_threshold:
            # Merge segments
            current[end_key] = max(current[end_key], segment[end_key])
            current[text_key] = current[text_key] + " " + segment[text_key]
        else:
            # Save current and start new
            merged.append(current)
            current = segment.copy()
    
    # Don't forget the last segment
    merged.append(current)
    
    return merged


def estimate_reading_time(
    text: str,
    words_per_minute: int = 150,
    min_duration: float = 1.0
) -> float:
    """
    Estimate reading time for text
    
    Args:
        text: Text to estimate reading time for
        words_per_minute: Average reading speed
        min_duration: Minimum duration in seconds
        
    Returns:
        Estimated reading time in seconds
    """
    word_count = len(text.split())
    reading_time = (word_count / words_per_minute) * 60
    return max(reading_time, min_duration)


def adjust_segment_timing(
    segments: list,
    min_duration: float = 1.0,
    max_duration: float = 7.0,
    start_key: str = "start",
    end_key: str = "end",
    text_key: str = "text"
) -> list:
    """
    Adjust segment timing based on text length
    
    Args:
        segments: List of segments to adjust
        min_duration: Minimum segment duration
        max_duration: Maximum segment duration
        start_key: Key name for start time
        end_key: Key name for end time
        text_key: Key name for text content
        
    Returns:
        Adjusted segments list
    """
    for i, segment in enumerate(segments):
        current_duration = segment[end_key] - segment[start_key]
        
        # Estimate ideal duration based on text
        ideal_duration = estimate_reading_time(
            segment.get(text_key, ""),
            min_duration=min_duration
        )
        ideal_duration = min(ideal_duration, max_duration)
        
        # Only adjust if current duration is too short or too long
        if current_duration < min_duration or current_duration > max_duration * 1.5:
            # Adjust end time
            segment[end_key] = segment[start_key] + ideal_duration
            
            # Make sure we don't overlap with next segment
            if i < len(segments) - 1:
                next_start = segments[i + 1][start_key]
                if segment[end_key] > next_start - 0.1:
                    segment[end_key] = next_start - 0.1
    
    return segments