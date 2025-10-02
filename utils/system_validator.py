import os
import subprocess
import platform
import ctypes
from typing import Dict, List, Optional

class SystemValidator:
    def __init__(self):
        self.validation_results = {}
        
    def validate_privileges(self) -> bool:
        try:
            if os.name == 'nt':
                return self._validate_windows_privileges()
            else:
                return self._validate_unix_privileges()
        except Exception:
            return False
    
    def _validate_windows_privileges(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    
    def _validate_unix_privileges(self) -> bool:
        try:
            return os.geteuid() == 0
        except Exception:
            return False
    
    def validate_system_compatibility(self) -> bool:
        try:
            compatibility_checks = [
                self._check_platform_support(),
                self._check_python_version(),
                self._check_required_tools(),
                self._check_disk_space(),
                self._check_memory_requirements()
            ]
            
            return all(compatibility_checks)
        except Exception:
            return False
    
    def _check_platform_support(self) -> bool:
        try:
            supported_platforms = ['Windows', 'Linux', 'Darwin']
            current_platform = platform.system()
            
            self.validation_results['platform'] = {
                'supported': current_platform in supported_platforms,
                'platform': current_platform
            }
            
            return current_platform in supported_platforms
        except Exception:
            return False
    
    def _check_python_version(self) -> bool:
        try:
            import sys
            required_version = (3, 8)
            current_version = sys.version_info[:2]
            
            self.validation_results['python'] = {
                'supported': current_version >= required_version,
                'version': f"{current_version[0]}.{current_version[1]}",
                'required': f"{required_version[0]}.{required_version[1]}"
            }
            
            return current_version >= required_version
        except Exception:
            return False
    
    def _check_required_tools(self) -> bool:
        try:
            required_tools = []
            
            if os.name == 'nt':
                required_tools = ['powershell', 'diskpart']
            else:
                required_tools = ['mount', 'umount', 'parted', 'mkfs']
            
            available_tools = []
            missing_tools = []
            
            for tool in required_tools:
                try:
                    result = subprocess.run([tool, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 or result.returncode == 1:
                        available_tools.append(tool)
                    else:
                        missing_tools.append(tool)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    missing_tools.append(tool)
            
            self.validation_results['tools'] = {
                'available': available_tools,
                'missing': missing_tools,
                'supported': len(missing_tools) == 0
            }
            
            return len(missing_tools) == 0
        except Exception:
            return False
    
    def _check_disk_space(self) -> bool:
        try:
            import shutil
            
            min_space_gb = 10
            available_space_gb = shutil.disk_usage('/').free / (1024**3)
            
            if os.name == 'nt':
                available_space_gb = shutil.disk_usage('C:').free / (1024**3)
            
            self.validation_results['disk_space'] = {
                'available_gb': available_space_gb,
                'required_gb': min_space_gb,
                'supported': available_space_gb >= min_space_gb
            }
            
            return available_space_gb >= min_space_gb
        except Exception:
            return False
    
    def _check_memory_requirements(self) -> bool:
        try:
            import psutil
            
            min_memory_gb = 4
            available_memory_gb = psutil.virtual_memory().total / (1024**3)
            
            self.validation_results['memory'] = {
                'available_gb': available_memory_gb,
                'required_gb': min_memory_gb,
                'supported': available_memory_gb >= min_memory_gb
            }
            
            return available_memory_gb >= min_memory_gb
        except Exception:
            return False
    
    def validate_iso_compatibility(self, iso_path: str) -> Dict:
        try:
            if not os.path.exists(iso_path):
                return {'compatible': False, 'error': 'ISO file does not exist'}
            
            file_size = os.path.getsize(iso_path)
            min_size_mb = 100
            
            if file_size < min_size_mb * 1024 * 1024:
                return {'compatible': False, 'error': 'ISO file too small'}
            
            file_extension = os.path.splitext(iso_path)[1].lower()
            supported_extensions = ['.iso', '.img', '.dmg', '.vdi', '.vmdk']
            
            if file_extension not in supported_extensions:
                return {'compatible': False, 'error': 'Unsupported file format'}
            
            return {
                'compatible': True,
                'size_mb': file_size / (1024 * 1024),
                'format': file_extension
            }
            
        except Exception as e:
            return {'compatible': False, 'error': str(e)}
    
    def validate_partition_compatibility(self, partition_info: Dict) -> Dict:
        try:
            if os.name == 'nt':
                return self._validate_windows_partition(partition_info)
            else:
                return self._validate_unix_partition(partition_info)
        except Exception as e:
            return {'compatible': False, 'error': str(e)}
    
    def _validate_windows_partition(self, partition_info: Dict) -> Dict:
        try:
            required_fields = ['number', 'size', 'type']
            
            for field in required_fields:
                if field not in partition_info:
                    return {'compatible': False, 'error': f'Missing field: {field}'}
            
            min_size_gb = 5
            partition_size_gb = partition_info['size'] / (1024**3)
            
            if partition_size_gb < min_size_gb:
                return {'compatible': False, 'error': 'Partition too small'}
            
            return {
                'compatible': True,
                'size_gb': partition_size_gb,
                'type': partition_info['type']
            }
            
        except Exception as e:
            return {'compatible': False, 'error': str(e)}
    
    def _validate_unix_partition(self, partition_info: Dict) -> Dict:
        try:
            required_fields = ['name', 'size', 'fstype']
            
            for field in required_fields:
                if field not in partition_info:
                    return {'compatible': False, 'error': f'Missing field: {field}'}
            
            min_size_gb = 5
            partition_size_gb = self._parse_size_to_gb(partition_info['size'])
            
            if partition_size_gb < min_size_gb:
                return {'compatible': False, 'error': 'Partition too small'}
            
            return {
                'compatible': True,
                'size_gb': partition_size_gb,
                'fstype': partition_info['fstype']
            }
            
        except Exception as e:
            return {'compatible': False, 'error': str(e)}
    
    def _parse_size_to_gb(self, size_str: str) -> float:
        try:
            size_str = size_str.upper()
            
            if 'G' in size_str:
                return float(size_str.replace('G', ''))
            elif 'M' in size_str:
                return float(size_str.replace('M', '')) / 1024
            elif 'K' in size_str:
                return float(size_str.replace('K', '')) / (1024 * 1024)
            else:
                return float(size_str) / (1024**3)
                
        except Exception:
            return 0.0
    
    def get_validation_report(self) -> Dict:
        return self.validation_results.copy()
    
    def validate_operation_safety(self, iso_path: str, target_partition: str) -> Dict:
        try:
            safety_checks = {
                'iso_compatible': self.validate_iso_compatibility(iso_path),
                'system_ready': self.validate_system_compatibility(),
                'privileges_ok': self.validate_privileges()
            }
            
            all_safe = all(
                check.get('compatible', False) or check.get('supported', False) or check
                for check in safety_checks.values()
            )
            
            return {
                'safe_to_proceed': all_safe,
                'checks': safety_checks,
                'recommendations': self._generate_recommendations(safety_checks)
            }
            
        except Exception as e:
            return {'safe_to_proceed': False, 'error': str(e)}
    
    def _generate_recommendations(self, safety_checks: Dict) -> List[str]:
        recommendations = []
        
        if not safety_checks.get('iso_compatible', {}).get('compatible', False):
            recommendations.append("Verify ISO file integrity and format")
        
        if not safety_checks.get('system_ready', False):
            recommendations.append("Check system compatibility requirements")
        
        if not safety_checks.get('privileges_ok', False):
            recommendations.append("Run application with administrator privileges")
        
        return recommendations
