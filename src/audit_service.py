"""
Audit logging service for tracking user actions
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from database import db


class AuditService:
    """Service for logging and retrieving audit records"""

    @staticmethod
    def log_action(
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        description: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        status_code: int = 200,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> int:
        """
        Log an audit event

        Args:
            action: Action performed (e.g., 'complaint.create', 'case.update')
            entity_type: Type of entity (e.g., 'complaint', 'case', 'document')
            entity_id: ID of the affected entity
            user_id: User/officer ID who performed the action
            user_role: Role of the user (e.g., 'officer', 'admin')
            ip_address: IP address of the request
            user_agent: User agent string from the request
            description: Human-readable description of the action
            changes: Before/after values for updates (dict with 'before' and 'after' keys)
            metadata: Additional context data
            endpoint: API endpoint that was called
            http_method: HTTP method (GET, POST, PUT, DELETE)
            status_code: HTTP response status code
            success: Whether the action succeeded
            error_message: Error message if action failed

        Returns:
            ID of the created audit log entry
        """
        query = """
        INSERT INTO audit_logs (
            user_id, user_role, ip_address, user_agent,
            action, entity_type, entity_id,
            description, changes, metadata,
            endpoint, http_method, status_code,
            success, error_message
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s
        ) RETURNING id;
        """

        # Convert dicts to JSON strings
        changes_json = json.dumps(changes) if changes else None
        metadata_json = json.dumps(metadata) if metadata else None

        try:
            with db.get_cursor() as cursor:
                cursor.execute(query, (
                    user_id, user_role, ip_address, user_agent,
                    action, entity_type, entity_id,
                    description, changes_json, metadata_json,
                    endpoint, http_method, status_code,
                    success, error_message
                ))
                result = cursor.fetchone()
                return result['id']
        except Exception as e:
            print(f"❌ Error logging audit action: {e}")
            # Don't raise - audit logging should not break the main flow
            return -1

    @staticmethod
    def get_logs(
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with filters

        Args:
            user_id: Filter by user ID
            action: Filter by action type
            entity_type: Filter by entity type
            entity_id: Filter by specific entity ID
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            ip_address: Filter by IP address
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of audit log entries
        """
        # Build dynamic query based on filters
        conditions = []
        params = []

        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)

        if action:
            conditions.append("action = %s")
            params.append(action)

        if entity_type:
            conditions.append("entity_type = %s")
            params.append(entity_type)

        if entity_id is not None:
            conditions.append("entity_id = %s")
            params.append(entity_id)

        if start_date:
            conditions.append("timestamp >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("timestamp <= %s")
            params.append(end_date)

        if ip_address:
            conditions.append("ip_address = %s")
            params.append(ip_address)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
        SELECT
            id, user_id, user_role,
            CAST(ip_address AS TEXT) as ip_address,
            user_agent,
            action, entity_type, entity_id,
            description, changes, metadata,
            timestamp, endpoint, http_method, status_code,
            success, error_message
        FROM audit_logs
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT %s OFFSET %s;
        """

        params.extend([limit, offset])

        try:
            results = db.execute_query(query, tuple(params))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"❌ Error retrieving audit logs: {e}")
            return []

    @staticmethod
    def get_entity_history(entity_type: str, entity_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get the complete audit history for a specific entity

        Args:
            entity_type: Type of entity (e.g., 'complaint', 'case')
            entity_id: ID of the entity
            limit: Maximum number of results

        Returns:
            List of audit log entries for the entity
        """
        return AuditService.get_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )

    @staticmethod
    def get_user_activity(user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all activity for a specific user/officer

        Args:
            user_id: User/officer ID
            limit: Maximum number of results

        Returns:
            List of audit log entries for the user
        """
        return AuditService.get_logs(user_id=user_id, limit=limit)

    @staticmethod
    def get_recent_activity(limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent activity across all users

        Args:
            limit: Maximum number of results

        Returns:
            List of recent audit log entries
        """
        return AuditService.get_logs(limit=limit)

    @staticmethod
    def get_logs_by_ip(ip_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all activity from a specific IP address

        Args:
            ip_address: IP address to filter by
            limit: Maximum number of results

        Returns:
            List of audit log entries from the IP
        """
        return AuditService.get_logs(ip_address=ip_address, limit=limit)

    @staticmethod
    def get_action_stats() -> Dict[str, Any]:
        """
        Get statistics about audit log actions

        Returns:
            Dictionary with action counts and other statistics
        """
        query = """
        SELECT
            COUNT(*) as total_logs,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT ip_address) as unique_ips,
            COUNT(CASE WHEN success = TRUE THEN 1 END) as successful_actions,
            COUNT(CASE WHEN success = FALSE THEN 1 END) as failed_actions
        FROM audit_logs;
        """

        try:
            result = db.execute_query(query)
            if result:
                return dict(result[0])
            return {}
        except Exception as e:
            print(f"❌ Error getting audit stats: {e}")
            return {}

    @staticmethod
    def get_action_breakdown() -> List[Dict[str, Any]]:
        """
        Get breakdown of actions by type

        Returns:
            List of action types with counts
        """
        query = """
        SELECT
            action,
            entity_type,
            COUNT(*) as count,
            COUNT(CASE WHEN success = TRUE THEN 1 END) as success_count,
            COUNT(CASE WHEN success = FALSE THEN 1 END) as error_count
        FROM audit_logs
        GROUP BY action, entity_type
        ORDER BY count DESC
        LIMIT 50;
        """

        try:
            results = db.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"❌ Error getting action breakdown: {e}")
            return []


# Helper function to track changes
def track_changes(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """
    Track changes between before and after states

    Args:
        before: State before the change
        after: State after the change

    Returns:
        Dictionary with 'before', 'after', and 'changed_fields' keys
    """
    changed_fields = []

    # Find all keys that exist in either dict
    all_keys = set(before.keys()) | set(after.keys())

    for key in all_keys:
        before_value = before.get(key)
        after_value = after.get(key)

        if before_value != after_value:
            changed_fields.append({
                'field': key,
                'before': before_value,
                'after': after_value
            })

    return {
        'before': before,
        'after': after,
        'changed_fields': changed_fields
    }
