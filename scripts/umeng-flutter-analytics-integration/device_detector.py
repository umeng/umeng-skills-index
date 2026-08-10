# -*- coding: utf-8 -*-
"""
Flutter统计SDK集成 - 设备检测模块
使用flutter devices检测Android和iOS双端设备
"""

import subprocess
import sys


class DeviceDetector:
    """Flutter设备检测器"""
    
    def __init__(self):
        self.android_devices = []
        self.ios_devices = []
    
    def detect_devices(self):
        """检测已连接的所有设备"""
        print("\n" + "="*60)
        print("📱 检测已连接的设备...")
        print("="*60 + "\n")
        
        # 使用flutter devices命令
        devices = self._detect_with_flutter()
        
        # 分类设备
        for device in devices:
            if device['platform'] == 'android':
                self.android_devices.append(device)
            elif device['platform'] == 'ios':
                self.ios_devices.append(device)
        
        # 打印结果
        self._print_devices()
        
        return len(devices) > 0
    
    def detect_android_devices(self):
        """仅检测Android设备"""
        print("\n" + "="*60)
        print("📱 检测 Android 设备...")
        print("="*60 + "\n")
        
        self.detect_devices()
        
        if self.android_devices:
            print("\n✅ 检测到 {} 台 Android 设备:\n".format(len(self.android_devices)))
            for i, device in enumerate(self.android_devices, 1):
                print("  {}. {}".format(i, device['name']))
                print("     ID: {}".format(device['id']))
                print("     类型: {}".format(device['type']))
                print()
            return True
        else:
            print("\n❌ 未检测到 Android 设备")
            print("\n💡 提示:")
            print("  1. 使用USB线连接Android设备")
            print("  2. 在设备上启用USB调试")
            print("  3. 在设备上授权USB调试连接")
            print("  4. 或启动Android模拟器")
            return False
    
    def detect_ios_devices(self):
        """仅检测iOS设备"""
        print("\n" + "="*60)
        print("📱 检测 iOS 设备...")
        print("="*60 + "\n")
        
        self.detect_devices()
        
        if self.ios_devices:
            print("\n✅ 检测到 {} 台 iOS 设备:\n".format(len(self.ios_devices)))
            for i, device in enumerate(self.ios_devices, 1):
                print("  {}. {}".format(i, device['name']))
                print("     ID: {}".format(device['id']))
                print("     类型: {}".format(device['type']))
                print()
            return True
        else:
            print("\n❌ 未检测到 iOS 设备")
            print("\n💡 提示:")
            print("  1. 使用USB线连接iPhone/iPad")
            print("  2. 在设备上信任此电脑")
            print("  3. 或启动iOS模拟器")
            return False
    
    def get_first_android_device(self):
        """获取第一台Android设备"""
        if self.android_devices:
            return self.android_devices[0]
        return None
    
    def get_first_ios_device(self):
        """获取第一台iOS设备"""
        if self.ios_devices:
            return self.ios_devices[0]
        return None
    
    def _detect_with_flutter(self):
        """使用flutter devices检测设备"""
        try:
            result = subprocess.run(
                ['flutter', 'devices'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return self._parse_flutter_devices(result.stdout)
            else:
                print("  ⚠️  flutter devices 命令失败")
                return []
                
        except FileNotFoundError:
            print("  ❌ flutter 命令不存在")
            print("     请确保 Flutter SDK 已正确安装")
            return []
        except subprocess.TimeoutExpired:
            print("  ❌ flutter devices 超时（超过30秒）")
            return []
        except Exception as e:
            print("  ❌ 设备检测失败: {}".format(str(e)))
            return []
    
    def _parse_flutter_devices(self, output):
        """解析flutter devices输出"""
        devices = []
        lines = output.split('\n')
        
        # 跳过标题行，解析设备列表
        for line in lines:
            # 跳过空行和标题行
            if not line.strip() or line.startswith('Found') or line.startswith('='):
                continue
            
            # 解析设备行
            # 格式: Name (mobile) • device_id • android/ios/web-javascript
            # 平台标识在第三段（•分隔），而非括号内的 mobile/web
            if '•' in line:
                parts = [p.strip() for p in line.split('•')]
                
                if len(parts) >= 3:
                    name_platform = parts[0]
                    device_id = parts[1]
                    device_type = parts[2]  # 这是真正的平台类型
                    
                    # 从 name_platform 提取设备名
                    if '(' in name_platform and ')' in name_platform:
                        name = name_platform.split('(')[0].strip()
                    else:
                        name = name_platform.strip()
                    
                    # 根据第三段判断平台
                    lower_type = device_type.lower()
                    if 'android' in lower_type:
                        platform_type = 'android'
                    elif 'ios' in lower_type:
                        platform_type = 'ios'
                    else:
                        platform_type = 'other'
                    
                    devices.append({
                        'name': name,
                        'platform': platform_type,
                        'id': device_id,
                        'type': device_type
                    })
        
        return devices
    
    def _print_devices(self):
        """打印设备列表"""
        total = len(self.android_devices) + len(self.ios_devices)
        
        if total == 0:
            print("❌ 未检测到任何设备")
            print("\n💡 提示:")
            print("  Android: 连接设备并启用USB调试，或启动Android模拟器")
            print("  iOS:     连接设备并信任此电脑，或启动iOS模拟器（仅macOS）")
            return
        
        print("\n📋 检测到的设备:\n")
        
        if self.android_devices:
            print("  🤖 Android 设备 ({}):".format(len(self.android_devices)))
            for i, device in enumerate(self.android_devices, 1):
                print("    {}. {} ({})".format(i, device['name'], device['type']))
                print("       ID: {}".format(device['id']))
            print()
        
        if self.ios_devices:
            print("  🍎 iOS 设备 ({}):".format(len(self.ios_devices)))
            for i, device in enumerate(self.ios_devices, 1):
                print("    {}. {} ({})".format(i, device['name'], device['type']))
                print("       ID: {}".format(device['id']))
            print()


if __name__ == '__main__':
    detector = DeviceDetector()
    
    if len(sys.argv) > 1:
        platform = sys.argv[1]
        
        if platform == 'android':
            success = detector.detect_android_devices()
        elif platform == 'ios':
            success = detector.detect_ios_devices()
        else:
            print("用法: python device_detector.py [android|ios]")
            print("       python device_detector.py  # 检测所有设备")
            sys.exit(1)
        
        if success:
            print("\n✅ 可以继续进行SDK验证")
            sys.exit(0)
        else:
            print("\n❌ 请连接设备后再运行验证")
            sys.exit(1)
    else:
        # 检测所有设备
        detector.detect_devices()
        sys.exit(0)
