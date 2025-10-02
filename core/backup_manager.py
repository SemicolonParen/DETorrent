import os
import shutil
import subprocess
import tempfile
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional
import json
import hashlib
from datetime import datetime

class BackupManager:
    def __init__(self):
        self.backup_directory = os.path.join(tempfile.gettempdir(), "detorrent_backups")
        self.active_backups = {}
        self.backup_metadata = {}
        
    def create_system_backup(self, backup_path: str) -> Dict:
        try:
            if not os.path.exists(backup_path):
                os.makedirs(backup_path, exist_ok=True)
            
            backup_id = self._generate_backup_id()
            backup_info = {
                'id': backup_id,
                'path': backup_path,
                'timestamp': datetime.now().isoformat(),
                'status': 'in_progress'
            }
            
            self.active_backups[backup_id] = backup_info
            
            if os.name == 'nt':
                result = self._create_windows_backup(backup_path, backup_id)
            else:
                result = self._create_unix_backup(backup_path, backup_id)
            
            if result['success']:
                backup_info['status'] = 'completed'
                self.backup_metadata[backup_id] = backup_info
                return {'success': True, 'backup_id': backup_id, 'path': backup_path}
            else:
                backup_info['status'] = 'failed'
                return {'success': False, 'error': result['error']}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _generate_backup_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"detorrent_backup_{timestamp}"
    
    def _create_windows_backup(self, backup_path: str, backup_id: str) -> Dict:
        try:
            backup_items = [
                'C:\\Windows\\System32\\config',
                'C:\\Windows\\Boot',
                'C:\\Windows\\System32\\drivers',
                'C:\\ProgramData\\Microsoft\\Windows\\Start Menu',
                'C:\\Users'
            ]
            
            backup_file = os.path.join(backup_path, f"{backup_id}.zip")
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in backup_items:
                    if os.path.exists(item):
                        if os.path.isfile(item):
                            zipf.write(item, os.path.basename(item))
                        else:
                            for root, dirs, files in os.walk(item):
                                for file in files:
                                    try:
                                        file_path = os.path.join(root, file)
                                        arcname = os.path.relpath(file_path, item)
                                        zipf.write(file_path, arcname)
                                    except PermissionError:
                                        continue
            
            return {'success': True, 'backup_file': backup_file}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_unix_backup(self, backup_path: str, backup_id: str) -> Dict:
        try:
            backup_items = [
                '/etc',
                '/boot',
                '/home',
                '/var/log',
                '/usr/local'
            ]
            
            backup_file = os.path.join(backup_path, f"{backup_id}.tar.gz")
            
            with tarfile.open(backup_file, 'w:gz') as tarf:
                for item in backup_items:
                    if os.path.exists(item):
                        tarf.add(item, arcname=os.path.basename(item))
            
            return {'success': True, 'backup_file': backup_file}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def restore_system_backup(self, backup_path: str) -> Dict:
        try:
            if not os.path.exists(backup_path):
                return {'success': False, 'error': 'Backup path does not exist'}
            
            backup_files = self._find_backup_files(backup_path)
            if not backup_files:
                return {'success': False, 'error': 'No backup files found'}
            
            latest_backup = max(backup_files, key=os.path.getmtime)
            
            if os.name == 'nt':
                result = self._restore_windows_backup(latest_backup)
            else:
                result = self._restore_unix_backup(latest_backup)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _find_backup_files(self, backup_path: str) -> List[str]:
        backup_files = []
        
        for file in os.listdir(backup_path):
            if file.endswith(('.zip', '.tar.gz')):
                backup_files.append(os.path.join(backup_path, file))
        
        return backup_files
    
    def _restore_windows_backup(self, backup_file: str) -> Dict:
        try:
            if not backup_file.endswith('.zip'):
                return {'success': False, 'error': 'Invalid backup file format'}
            
            temp_extract_dir = tempfile.mkdtemp(prefix="detorrent_restore_")
            
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_extract_dir)
            
            restore_commands = [
                f'robocopy "{temp_extract_dir}" "C:\\Windows\\System32\\config" /E /Y',
                f'robocopy "{temp_extract_dir}" "C:\\Windows\\Boot" /E /Y',
                f'robocopy "{temp_extract_dir}" "C:\\Users" /E /Y'
            ]
            
            for command in restore_commands:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode not in [0, 1]:
                    return {'success': False, 'error': f'Restore command failed: {result.stderr}'}
            
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
            return {'success': True, 'message': 'Windows backup restored successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _restore_unix_backup(self, backup_file: str) -> Dict:
        try:
            if not backup_file.endswith('.tar.gz'):
                return {'success': False, 'error': 'Invalid backup file format'}
            
            temp_extract_dir = tempfile.mkdtemp(prefix="detorrent_restore_")
            
            with tarfile.open(backup_file, 'r:gz') as tarf:
                tarf.extractall(temp_extract_dir)
            
            restore_commands = [
                f'sudo cp -r "{temp_extract_dir}/etc" "/etc"',
                f'sudo cp -r "{temp_extract_dir}/boot" "/boot"',
                f'sudo cp -r "{temp_extract_dir}/home" "/home"'
            ]
            
            for command in restore_commands:
                result = subprocess.run(command.split(), capture_output=True, text=True)
                if result.returncode != 0:
                    return {'success': False, 'error': f'Restore command failed: {result.stderr}'}
            
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
            return {'success': True, 'message': 'Unix backup restored successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_backups(self, backup_directory: str = None) -> List[Dict]:
        try:
            if backup_directory is None:
                backup_directory = self.backup_directory
            
            if not os.path.exists(backup_directory):
                return []
            
            backups = []
            
            for file in os.listdir(backup_directory):
                if file.endswith(('.zip', '.tar.gz')):
                    file_path = os.path.join(backup_directory, file)
                    stat_info = os.stat(file_path)
                    
                    backup_info = {
                        'name': file,
                        'path': file_path,
                        'size': stat_info.st_size,
                        'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                    }
                    
                    backups.append(backup_info)
            
            return sorted(backups, key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            return [{'error': str(e)}]
    
    def delete_backup(self, backup_path: str) -> Dict:
        try:
            if not os.path.exists(backup_path):
                return {'success': False, 'error': 'Backup file does not exist'}
            
            os.remove(backup_path)
            return {'success': True, 'message': 'Backup deleted successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_backup(self, backup_path: str) -> Dict:
        try:
            if not os.path.exists(backup_path):
                return {'success': False, 'error': 'Backup file does not exist'}
            
            if backup_path.endswith('.zip'):
                return self._verify_zip_backup(backup_path)
            elif backup_path.endswith('.tar.gz'):
                return self._verify_tar_backup(backup_path)
            else:
                return {'success': False, 'error': 'Unsupported backup format'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _verify_zip_backup(self, backup_path: str) -> Dict:
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                file_list = zipf.namelist()
                corrupted_files = zipf.testzip()
            
            return {
                'success': True,
                'file_count': len(file_list),
                'corrupted_files': corrupted_files,
                'integrity': 'good' if corrupted_files is None else 'corrupted'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _verify_tar_backup(self, backup_path: str) -> Dict:
        try:
            with tarfile.open(backup_path, 'r:gz') as tarf:
                file_list = tarf.getnames()
            
            return {
                'success': True,
                'file_count': len(file_list),
                'integrity': 'good'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_backup_metadata(self, backup_id: str) -> Dict:
        return self.backup_metadata.get(backup_id, {})
    
    def cleanup_old_backups(self, backup_directory: str = None, days_to_keep: int = 30) -> Dict:
        try:
            if backup_directory is None:
                backup_directory = self.backup_directory
            
            if not os.path.exists(backup_directory):
                return {'success': True, 'message': 'No backups to clean up'}
            
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0
            
            for file in os.listdir(backup_directory):
                if file.endswith(('.zip', '.tar.gz')):
                    file_path = os.path.join(backup_directory, file)
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
            
            return {'success': True, 'message': f'Cleaned up {deleted_count} old backups'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
