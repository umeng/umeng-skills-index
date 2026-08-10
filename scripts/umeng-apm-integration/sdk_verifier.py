#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APM SDK验证模块
通过logcat日志验证APM SDK初始化成功
"""

import os
import sys
import subprocess
import time
import re
from typing import Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from device_manager import DeviceManager


class APMSDKVerifier:
    """APM SDK验证器"""
    
    def __init__(self, project_path: str, app_module: str):
        self.project_path = os.path.abspath(project_path)
        self.app_module = app_module
        self.device_manager = DeviceManager()
    
    def verify(self) -> Tuple[bool, str]:
        """
        验证APM SDK集成
        
        Returns:
            (是否成功, 详细信息)
        """
        print("\n🔍 开始验证APM SDK集成...\n")
        
        try:
            # 1. 检测设备
            devices = self.device_manager.detect_devices()
            
            if not devices:
                choice = self.device_manager.handle_no_device()
                
                if choice == 'emulator':
                    self.device_manager.provide_emulator_guide()
                    return False, "用户选择配置模拟器"
                elif choice == 'skip':
                    print("⚠️  跳过设备测试")
                    print("请在有设备时手动验证APM SDK是否初始化成功\n")
                    return True, "跳过验证"
                else:
                    return False, "用户选择退出"
            
            # 获取可用设备
            device_info = self.device_manager.get_available_device()
            if not device_info:
                print("❌ 无可用设备\n")
                return False, "无可用设备"
            
            device = device_info['serial']
            print(f"✅ 使用设备: {device_info['name']} ({device})\n")
            
            # 2. 安装APK
            if not self._install_apk(device):
                return False, "APK安装失败"
            
            # 3. 启动应用
            if not self._launch_app(device):
                return False, "应用启动失败"
            
            # 4. 抓取logcat日志
            logs = self._capture_logcat(device=device, timeout=30)
            
            # 5. 分析日志
            return self._analyze_logs(logs)
            
        except Exception as e:
            return False, f"验证过程出错: {str(e)}"
    
    def _check_device(self) -> str:
        """检查可用设备"""
        print("步骤 1/4: 检查设备")
        
        try:
            result = subprocess.run(
                ['adb', 'devices', '-l'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            devices = []
            for line in result.stdout.split('\n')[1:]:
                if line.strip() and not line.startswith('*'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == 'device':
                        devices.append(parts[0])
            
            if not devices:
                print("  ❌ 未检测到可用设备")
                print("  请连接Android设备或启动模拟器")
                return None
            
            device = devices[0]
            print(f"  ✅ 检测到设备: {device}\n")
            return device
            
        except FileNotFoundError:
            print("  ❌ 未找到adb工具")
            return None
        except Exception as e:
            print(f"  ❌ 设备检测失败: {str(e)}")
            return None
    
    def _install_apk(self, device: str) -> bool:
        """安装APK"""
        print("步骤 2/4: 安装APK")
        
        # 查找APK文件
        apk_path = os.path.join(
            self.project_path,
            self.app_module,
            'build',
            'outputs',
            'apk',
            'debug',
            f'{self.app_module}-debug.apk'
        )
        
        if not os.path.exists(apk_path):
            print(f"  ❌ 未找到APK文件: {apk_path}")
            print("  请先编译项目")
            return False
        
        try:
            print(f"  安装APK: {os.path.basename(apk_path)}")
            result = subprocess.run(
                ['adb', '-s', device, 'install', '-r', apk_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("  ✅ APK安装成功\n")
                return True
            else:
                print(f"  ❌ APK安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ APK安装失败: {str(e)}")
            return False
    
    def _launch_app(self, device: str) -> bool:
        """启动应用"""
        print("步骤 3/4: 启动应用")
        
        try:
            # 获取包名(从AndroidManifest.xml解析)
            package_name = self._get_package_name()
            if not package_name:
                print("  ❌ 无法获取应用包名")
                return False
            
            print(f"  启动应用: {package_name}")
            result = subprocess.run(
                ['adb', '-s', device, 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode == 0:
                print("  ✅ 应用启动成功\n")
                return True
            else:
                print(f"  ❌ 应用启动失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ 应用启动失败: {str(e)}")
            return False
    
    def _get_package_name(self) -> str:
        """从AndroidManifest.xml获取包名"""
        manifest_path = os.path.join(
            self.project_path,
            self.app_module,
            'src',
            'main',
            'AndroidManifest.xml'
        )
        
        if not os.path.exists(manifest_path):
            return None
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析package属性
            match = re.search(r'package="([^"]+)"', content)
            if match:
                return match.group(1)
            
            return None
        except:
            return None
    
    def _capture_logcat(self, device: str, timeout: int = 30) -> str:
        """抓取logcat日志"""
        print(f"步骤 4/4: 抓取logcat日志(超时{timeout}秒)")
        
        try:
            # 清空logcat
            subprocess.run(['adb', '-s', device, 'logcat', '-c'], capture_output=True, timeout=5)
            
            # 等待应用初始化
            time.sleep(3)
            
            # 抓取日志
            result = subprocess.run(
                ['adb', '-s', device, 'logcat', '-d'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            logs = result.stdout
            print(f"  ✅ 已抓取 {len(logs)} 字符的日志\n")
            return logs
            
        except Exception as e:
            print(f"  ❌ 日志抓取失败: {str(e)}")
            return ""
    
    def _analyze_logs(self, logs: str) -> Tuple[bool, str]:
        """分析日志"""
        print("分析日志...\n")
        
        if not logs:
            return False, "未获取到日志"
        
        # 过滤UMCrash相关日志
        filtered_lines = [line for line in logs.split('\n') if 'UMCrash' in line]
        
        # 成功关键词
        success_patterns = [
            r'可接入免费的网络分析能力',
            r'UMCrash init success',
            r'efs transform success',
        ]
        
        # 失败关键词（关键错误）
        error_keywords = [
            'UMCrash init failed',
            'efs transform failed',
            'UMCrash config error',
            'apm-plugin not applied',
        ]
        
        # 警告关键词（可能失败，但不一定）
        warning_keywords = [
            'UMCrash network error',
        ]
        
        # 检查失败关键词
        for keyword in error_keywords:
            if keyword in logs:
                print(f"❌ 检测到错误关键词: {keyword}")
                print("\n可能原因:")
                if 'init failed' in keyword:
                    print("  - UMCrash初始化失败")
                    print("  - 请检查UMCrash.initConfig()是否在UMConfigure.init()之前调用")
                elif 'efs transform' in keyword:
                    print("  - efs字节码插桩失败")
                    print("  - 请检查build.gradle中是否正确apply了com.efs.sdk.plugin")
                elif 'not applied' in keyword:
                    print("  - APM Gradle插件未正确配置")
                    print("  - 请检查classpath和apply plugin配置")
                elif 'config error' in keyword:
                    print("  - APM配置错误")
                    print("  - 请检查UMCrash.initConfig()的Bundle参数")
                
                return False, f"检测到错误: {keyword}"
        
        # 检查警告关键词
        for keyword in warning_keywords:
            if keyword in logs:
                print(f"⚠️  检测到警告关键词: {keyword}")
                print("  可能是网络问题，不影响SDK集成正确性")
                # 不立即返回失败，继续检查是否有成功关键词
        
        # 检查成功关键词
        for pattern in success_patterns:
            match = re.search(pattern, logs, re.IGNORECASE)
            if match:
                print(f"✅ 检测到成功关键词: {match.group(0)}")
                print("✅ APM SDK集成成功!\n")
                return True, f"APM SDK初始化成功: {match.group(0)}"
        
        # 未找到任何关键词
        print("⚠️  未检测到成功或失败关键词")
        print("\n可能原因:")
        print("  - 应用启动时间不足,SDK尚未完成初始化")
        print("  - 网络连接问题")
        print("  - APM插件未正确配置")
        print("\n建议:")
        print("  1. 手动查看logcat日志:")
        print('     adb logcat | grep "UMCrash"')
        print("  2. 检查Application类中UMCrash.initConfig()是否在UMConfigure.init()之前")
        print("  3. 检查build.gradle中efs插件配置")
        print("  4. 确保设备网络正常\n")
        
        return False, "未检测到APM初始化成功日志,需要手动验证"
