# -*- coding: utf-8 -*-
"""
iOS统计SDK集成 - 真机检测模块
检测是否连接iPhone真机用于SDK验证
"""

import subprocess
import sys


class DeviceDetector:
    """iOS真机检测器"""
    
    def __init__(self):
        self.devices = []
    
    def detect_devices(self):
        """检测已连接的iPhone真机"""
        print("\n" + "="*60)
        print("📱 检测iPhone真机...")
        print("="*60 + "\n")
        
        # 方法1: 使用xcrun xctrace list devices
        devices = self._detect_with_xctrace()
        
        if not devices:
            # 方法2: 使用idevice_id（需要安装libimobiledevice）
            devices = self._detect_with_idevice_id()
        
        self.devices = devices
        
        if devices:
            print("\n✅ 检测到 {} 台已连接的iPhone设备:\n".format(len(devices)))
            for i, device in enumerate(devices, 1):
                print("  {}. {} ({})".format(i, device['name'], device['udid']))
                print("     版本: {}".format(device['version']))
                print()
            return True
        else:
            print("\n❌ 未检测到已连接的iPhone真机")
            print("\n💡 提示:")
            print("  1. 请使用USB线连接iPhone到Mac")
            print("  2. 在iPhone上信任此电脑")
            print("  3. 确保iPhone已解锁")
            print("  4. 如果是首次连接，需要在iPhone上点击\"信任此电脑\"")
            print("\n⚠️  友盟UMCCommonLog库不支持x86_64模拟器架构")
            print("   必须使用真机进行SDK验证")
            return False
    
    def get_first_device(self):
        """获取第一台设备"""
        if self.devices:
            return self.devices[0]
        return None
    
    def _detect_with_xctrace(self):
        """使用xcrun xctrace检测设备"""
        try:
            result = subprocess.run(
                ['xcrun', 'xctrace', 'list', 'devices'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            devices = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                # 匹配格式: iPhone (14.2.1) XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
                # 或者是: iPhone 14 Pro (16.0) XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
                if 'iPhone' in line and '(' in line and ')' in line:
                    # 跳过模拟器
                    if 'Simulator' in line or 'Apple Watch' in line:
                        continue
                    
                    # 提取信息
                    parts = line.split('(')
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        version_and_udid = parts[1]
                        
                        version_parts = version_and_udid.split(')')
                        if len(version_parts) >= 2:
                            version = version_parts[0].strip()
                            udid = version_parts[1].strip()
                            
                            # UDIM应该是有效的UUID格式
                            if len(udid) > 10:  # 简单验证
                                devices.append({
                                    'name': name,
                                    'version': version,
                                    'udid': udid
                                })
            
            return devices
            
        except Exception as e:
            print("  ⚠️  xctrace检测失败: {}".format(str(e)))
            return []
    
    def _detect_with_idevice_id(self):
        """使用idevice_id检测设备（需要libimobiledevice）"""
        try:
            result = subprocess.run(
                ['idevice_id', '-l'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            devices = []
            udid_list = result.stdout.strip().split('\n')
            
            for udid in udid_list:
                udid = udid.strip()
                if udid:
                    # 获取设备名称
                    name_result = subprocess.run(
                        ['ideviceinfo', '-u', udid, '-k', 'DeviceName'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    version_result = subprocess.run(
                        ['ideviceinfo', '-u', udid, '-k', 'ProductVersion'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    name = name_result.stdout.strip() if name_result.returncode == 0 else 'Unknown'
                    version = version_result.stdout.strip() if version_result.returncode == 0 else 'Unknown'
                    
                    devices.append({
                        'name': name,
                        'version': version,
                        'udid': udid
                    })
            
            return devices
            
        except FileNotFoundError:
            print("  ⚠️  idevice_id未安装（需要libimobiledevice）")
            print("     安装方法: brew install libimobiledevice")
            return []
        except Exception as e:
            print("  ⚠️  idevice_id检测失败: {}".format(str(e)))
            return []


if __name__ == '__main__':
    detector = DeviceDetector()
    if detector.detect_devices():
        print("\n✅ 可以继续进行SDK验证")
        sys.exit(0)
    else:
        print("\n❌ 请连接iPhone真机后再运行验证")
        sys.exit(1)
