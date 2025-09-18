# utils/monitoring.py
import logging
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import threading


class APIMonitor:
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / 'api_usage.json'
        self.daily_stats_file = self.log_dir / 'daily_stats.json'
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.ensure_log_files()

    def ensure_log_files(self):
        """Ensure log directory and files exist"""
        self.log_dir.mkdir(exist_ok=True)

        if not self.log_file.exists():
            with open(self.log_file, 'w') as f:
                json.dump([], f)

        if not self.daily_stats_file.exists():
            with open(self.daily_stats_file, 'w') as f:
                json.dump({}, f)

    def log_api_call(self, service: str, endpoint: str, success: bool, error_type: Optional[str] = None,
                     cost: float = 0, response_time: Optional[float] = None):
        """Log an API call with all relevant details"""
        with self.lock:
            try:
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'service': service,
                    'endpoint': endpoint,
                    'success': success,
                    'error_type': error_type,
                    'cost': cost,
                    'response_time': response_time
                }

                # Load existing logs
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)

                logs.append(log_entry)

                # Keep only last 1000 entries to prevent file from growing too large
                if len(logs) > 1000:
                    logs = logs[-1000:]

                # Save back to file
                with open(self.log_file, 'w') as f:
                    json.dump(logs, f, indent=2)

                # Update daily stats
                self._update_daily_stats(log_entry)

            except Exception as e:
                self.logger.error(f"Failed to log API call: {e}")

    def _update_daily_stats(self, log_entry: Dict):
        """Update daily statistics"""
        try:
            today = datetime.utcnow().date().isoformat()

            # Load existing daily stats
            with open(self.daily_stats_file, 'r') as f:
                daily_stats = json.load(f)

            if today not in daily_stats:
                daily_stats[today] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_cost': 0.0,
                    'services': {},
                    'error_types': {}
                }

            stats = daily_stats[today]
            service = log_entry['service']

            # Update counters
            stats['total_calls'] += 1
            if log_entry['success']:
                stats['successful_calls'] += 1
            else:
                stats['failed_calls'] += 1

            stats['total_cost'] += log_entry.get('cost', 0)

            # Update service stats
            if service not in stats['services']:
                stats['services'][service] = {
                    'calls': 0,
                    'success': 0,
                    'failed': 0,
                    'cost': 0.0
                }

            stats['services'][service]['calls'] += 1
            if log_entry['success']:
                stats['services'][service]['success'] += 1
            else:
                stats['services'][service]['failed'] += 1
            stats['services'][service]['cost'] += log_entry.get('cost', 0)

            # Update error type stats
            if not log_entry['success'] and log_entry.get('error_type'):
                error_type = log_entry['error_type']
                if error_type not in stats['error_types']:
                    stats['error_types'][error_type] = 0
                stats['error_types'][error_type] += 1

            # Clean up old daily stats (keep only last 30 days)
            cutoff_date = (datetime.utcnow() - timedelta(days=30)).date().isoformat()
            daily_stats = {k: v for k, v in daily_stats.items() if k >= cutoff_date}

            # Save updated stats
            with open(self.daily_stats_file, 'w') as f:
                json.dump(daily_stats, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to update daily stats: {e}")

    def get_daily_stats(self, date: Optional[str] = None) -> Dict:
        """Get daily statistics for a specific date or today"""
        try:
            if date is None:
                date = datetime.utcnow().date().isoformat()

            with open(self.daily_stats_file, 'r') as f:
                daily_stats = json.load(f)

            return daily_stats.get(date, {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_cost': 0.0,
                'services': {},
                'error_types': {}
            })

        except Exception as e:
            self.logger.error(f"Failed to get daily stats: {e}")
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_cost': 0.0,
                'services': {},
                'error_types': {},
                'error': str(e)
            }

    def get_weekly_stats(self) -> Dict:
        """Get statistics for the last 7 days"""
        try:
            with open(self.daily_stats_file, 'r') as f:
                daily_stats = json.load(f)

            # Get last 7 days
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=6)

            weekly_stats = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_cost': 0.0,
                'daily_breakdown': {},
                'services': {},
                'error_types': {}
            }

            for i in range(7):
                current_date = (start_date + timedelta(days=i)).isoformat()
                day_stats = daily_stats.get(current_date, {})

                weekly_stats['daily_breakdown'][current_date] = day_stats

                # Aggregate totals
                weekly_stats['total_calls'] += day_stats.get('total_calls', 0)
                weekly_stats['successful_calls'] += day_stats.get('successful_calls', 0)
                weekly_stats['failed_calls'] += day_stats.get('failed_calls', 0)
                weekly_stats['total_cost'] += day_stats.get('total_cost', 0.0)

                # Aggregate services
                for service, service_stats in day_stats.get('services', {}).items():
                    if service not in weekly_stats['services']:
                        weekly_stats['services'][service] = {
                            'calls': 0,
                            'success': 0,
                            'failed': 0,
                            'cost': 0.0
                        }

                    weekly_stats['services'][service]['calls'] += service_stats.get('calls', 0)
                    weekly_stats['services'][service]['success'] += service_stats.get('success', 0)
                    weekly_stats['services'][service]['failed'] += service_stats.get('failed', 0)
                    weekly_stats['services'][service]['cost'] += service_stats.get('cost', 0.0)

                # Aggregate error types
                for error_type, count in day_stats.get('error_types', {}).items():
                    if error_type not in weekly_stats['error_types']:
                        weekly_stats['error_types'][error_type] = 0
                    weekly_stats['error_types'][error_type] += count

            return weekly_stats

        except Exception as e:
            self.logger.error(f"Failed to get weekly stats: {e}")
            return {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_cost': 0.0,
                'daily_breakdown': {},
                'services': {},
                'error_types': {},
                'error': str(e)
            }

    def get_recent_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent error logs"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)

            # Filter for errors and get most recent
            error_logs = [log for log in logs if not log['success']]
            error_logs.sort(key=lambda x: x['timestamp'], reverse=True)

            return error_logs[:limit]

        except Exception as e:
            self.logger.error(f"Failed to get recent errors: {e}")
            return []

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up logs older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            with open(self.log_file, 'r') as f:
                logs = json.load(f)

            # Filter logs
            filtered_logs = [
                log for log in logs
                if datetime.fromisoformat(log['timestamp']) >= cutoff_date
            ]

            with open(self.log_file, 'w') as f:
                json.dump(filtered_logs, f, indent=2)

            self.logger.info(f"Cleaned up {len(logs) - len(filtered_logs)} old log entries")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")


# Initialize the monitor
api_monitor = APIMonitor()