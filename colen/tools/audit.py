"""Audit logging for Colen tool operations.

This module provides comprehensive logging of all tool operations for security
auditing, debugging, and usage analysis.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from threading import Lock

# Default audit log path
DEFAULT_AUDIT_LOG_PATH = Path.home() / ".colen_audit.log"

# Thread-safe writing
_audit_lock = Lock()


class AuditLogger:
    """Thread-safe audit logger for tool operations."""
    
    def __init__(self, log_path: Optional[Path] = None):
        """Initialize the audit logger.
        
        Args:
            log_path: Path to the audit log file (default: ~/.colen_audit.log)
        """
        self.log_path = log_path or DEFAULT_AUDIT_LOG_PATH
        self._ensure_log_file()
    
    def _ensure_log_file(self) -> None:
        """Ensure the audit log file exists."""
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_path.exists():
                self.log_path.touch()
        except (OSError, RuntimeError) as e:
            # If we can't create the log file, continue without logging
            print(f"Warning: Could not create audit log: {e}")
    
    def log_operation(
        self,
        operation: str,
        params: Dict[str, Any],
        result: str,
        success: bool = True,
        execution_time: Optional[float] = None,
        user_confirmed: bool = False,
    ) -> None:
        """Log a tool operation.
        
        Args:
            operation: Name of the operation/tool
            params: Parameters passed to the operation
            result: Result of the operation
            success: Whether the operation succeeded
            execution_time: Time taken to execute (seconds)
            user_confirmed: Whether user confirmed the operation
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "params": self._sanitize_params(params),
            "result": result[:500] if result else "",  # Limit result length
            "success": success,
            "execution_time": execution_time,
            "user_confirmed": user_confirmed,
        }
        
        with _audit_lock:
            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except (OSError, RuntimeError) as e:
                # If logging fails, don't break the application
                print(f"Warning: Could not write to audit log: {e}")
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters for logging (remove sensitive data).
        
        Args:
            params: Original parameters
            
        Returns:
            Sanitized parameters
        """
        sanitized = {}
        sensitive_keys = {"password", "token", "key", "secret", "api_key"}
        
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, (str, int, float, bool, type(None))):
                sanitized[key] = value
            elif isinstance(value, (list, tuple)):
                sanitized[key] = f"<{type(value).__name__} with {len(value)} items>"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_params(value)
            else:
                sanitized[key] = f"<{type(value).__name__}>"
        
        return sanitized
    
    def get_recent_operations(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent operations from the audit log.
        
        Args:
            count: Number of recent operations to retrieve
            
        Returns:
            List of recent log entries
        """
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            recent_lines = lines[-count:] if len(lines) > count else lines
            return [json.loads(line) for line in recent_lines if line.strip()]
        
        except (OSError, RuntimeError, json.JSONDecodeError):
            return []
    
    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get statistics about logged operations.
        
        Returns:
            Dictionary with operation statistics
        """
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if not lines:
                return {"total": 0, "successful": 0, "failed": 0, "by_operation": {}}
            
            entries = [json.loads(line) for line in lines if line.strip()]
            
            total = len(entries)
            successful = sum(1 for e in entries if e.get("success", False))
            failed = total - successful
            
            by_operation = {}
            for entry in entries:
                op = entry.get("operation", "unknown")
                by_operation[op] = by_operation.get(op, 0) + 1
            
            return {
                "total": total,
                "successful": successful,
                "failed": failed,
                "by_operation": by_operation,
            }
        
        except (OSError, RuntimeError, json.JSONDecodeError):
            return {"total": 0, "successful": 0, "failed": 0, "by_operation": {}}
    
    def clear_log(self) -> None:
        """Clear the audit log."""
        with _audit_lock:
            try:
                self.log_path.write_text("")
            except (OSError, RuntimeError) as e:
                print(f"Warning: Could not clear audit log: {e}")


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance.
    
    Returns:
        Global AuditLogger instance
    """
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger


def log_operation(
    operation: str,
    params: Dict[str, Any],
    result: str,
    success: bool = True,
    execution_time: Optional[float] = None,
    user_confirmed: bool = False,
) -> None:
    """Convenience function to log an operation using the global logger.
    
    Args:
        operation: Name of the operation/tool
        params: Parameters passed to the operation
        result: Result of the operation
        success: Whether the operation succeeded
        execution_time: Time taken to execute (seconds)
        user_confirmed: Whether user confirmed the operation
    """
    logger = get_audit_logger()
    logger.log_operation(operation, params, result, success, execution_time, user_confirmed)