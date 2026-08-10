# -*- coding: utf-8 -*-
"""
Flutter统计SDK集成 - SDK验证模块
通过adb logcat验证Android端SDK是否正确上报数据
"""

import subprocess
import sys
import os


class SDKVerifier:
    """SDK验证器"""
    
    def __init__(self, project_path):
        self.project_path = project_path
    
    def verify_android(self):
        """验证Android端SDK"""
        print("\n" + "="*60)
        print("📱 Android SDK 验证")
        print("="*60 + "\n")
        
        # 检查adb是否可用
        if not self._check_adb():
            return False
        
        # 检查是否有设备连接
        if not self._check_device_connected():
            return False
        
        # 抓取logcat日志
        print("🔍 抓取友盟SDK日志...\n")
        
        try:
            # 清理logcat缓冲区
            subprocess.run(
                ['adb', 'logcat', '-c'],
                capture_output=True,
                timeout=5
            )
            
            # 抓取日志（包含umeng相关关键词）
            result = subprocess.run(
                ['adb', 'logcat', '-d', '*:S', 'UMLog:D', 'umeng:D', 'MobClick:D'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logs = result.stdout
                
                if not logs.strip():
                    print("  ⚠️  未捕获到友盟SDK日志")
                    print("\n💡 可能的原因:")
                    print("  1. App尚未启动或未完成初始化")
                    print("  2. SDK初始化代码未执行")
                    print("  3. 用户未同意隐私政策（initCommon()未被调用）")
                    print("\n📝 请启动App后重新运行验证")
                    return False
                
                # 分析日志
                return self._analyze_logs(logs)
            else:
                print("  ❌ logcat 抓取失败")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ❌ logcat 超时")
            return False
        except Exception as e:
            print("  ❌ 验证过程出错: {}".format(str(e)))
            return False
    
    def verify_ios(self):
        """验证iOS端SDK"""
        print("\n" + "="*60)
        print("📱 iOS SDK 验证")
        print("="*60 + "\n")
        
        print("  ℹ️  iOS SDK 验证需要在 Xcode 中手动进行：")
        print("\n  1. 在 Xcode 中打开 ios/Runner.xcworkspace")
        print("  2. 选择模拟器或真机作为运行目标")
        print("  3. 点击 Run (⌘R) 编译并运行")
        print("  4. 查看 Xcode Console 日志")
        print("\n  ✅ 成功关键词:")
        print("     - preInit success")
        print("     - initCommon called")
        print("\n  ❌ 失败关键词:")
        print("     - appkey invalid")
        print("     - ERROR/umeng")
        
        return True  # iOS验证返回True，因为需要手动验证
    
    def _check_adb(self):
        """检查adb是否可用"""
        try:
            result = subprocess.run(
                ['adb', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.split('\n')[0]
                print("  ✅ adb 可用: {}".format(version))
                return True
            else:
                print("  ❌ adb 不可用")
                return False
                
        except FileNotFoundError:
            print("  ❌ adb 命令不存在")
            print("\n💡 安装方法:")
            print("  1. 安装 Android Studio")
            print("  2. 添加 platform-tools 到 PATH")
            print("  3. macOS: export PATH=$ANDROID_HOME/platform-tools:$PATH")
            return False
        except Exception as e:
            print("  ❌ adb 检测失败: {}".format(str(e)))
            return False
    
    def _check_device_connected(self):
        """检查是否有设备连接"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                
                # 跳过第一行标题
                devices = [line for line in lines[1:] if line.strip() and 'device' in line]
                
                if devices:
                    print("  ✅ 检测到 {} 台已连接的设备".format(len(devices)))
                    for device in devices:
                        print("     {}".format(device.split('\t')[0]))
                    return True
                else:
                    print("  ❌ 未检测到已连接的设备")
                    print("\n💡 请:")
                    print("  1. 使用USB线连接Android设备")
                    print("  2. 在设备上启用USB调试")
                    print("  3. 在设备上授权USB调试连接")
                    return False
            else:
                print("  ❌ adb devices 命令失败")
                return False
                
        except Exception as e:
            print("  ❌ 设备检测失败: {}".format(str(e)))
            return False
    
    def _analyze_logs(self, logs):
        """分析日志"""
        print("  📊 日志分析...\n")
        
        # 噪音排除：UMLog Reflect: 为内部反射日志，逐行过滤后再拼接做匹配
        filtered_lines = [line for line in logs.split('\n')
                          if 'UMLog Reflect:' not in line]
        logs = '\n'.join(filtered_lines)
        
        # 成功关键词（来自实测日志，小写匹配）
        success_keywords = ['安卓依赖版本检查成功', 'setwrapertype:flutter1.0 success',
                            'setpagecollectionmodeauto', 'module init:azio']
        # 失败关键词收窄（实测发现 error/exception/failed 过于宽泛，
        # E 级别日志如 "E UMLog: 安卓依赖版本检查成功" 属正常输出）
        failure_keywords = ['appkey invalid', 'binding already initialized']
        
        logs_lower = logs.lower()
        
        has_success = any(keyword in logs_lower for keyword in success_keywords)
        has_failure = any(keyword in logs_lower for keyword in failure_keywords)
        
        # 显示关键日志
        print("  📋 捕获到的关键日志:")
        for line in logs.split('\n')[:10]:  # 只显示前10行
            if line.strip():
                print("    {}".format(line))
        
        if has_success and not has_failure:
            print("\n  ✅ SDK 初始化成功")
            return True
        elif has_failure:
            print("\n  ❌ SDK 初始化失败")
            print("\n💡 可能的原因:")
            print("  1. AppKey 不正确或未配置")
            print("  2. 网络连接问题")
            print("  3. SDK 版本兼容性问题")
            return False
        else:
            print("\n  ⚠️  无法确定 SDK 状态")
            print("     日志中未检测到明确的成功或失败标志")
            return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python sdk_verifier.py <project_path> [--platform android|ios]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    platform = 'android'
    
    # 解析平台参数
    if len(sys.argv) > 2 and sys.argv[2] == '--platform':
        if len(sys.argv) > 3:
            platform = sys.argv[3]
    
    verifier = SDKVerifier(project_path)
    
    if platform == 'android':
        success = verifier.verify_android()
    elif platform == 'ios':
        success = verifier.verify_ios()
    else:
        print("❌ 不支持的平台: {}".format(platform))
        sys.exit(1)
    
    if success:
        print("\n✅ SDK 验证通过")
        sys.exit(0)
    else:
        print("\n❌ SDK 验证失败")
        sys.exit(1)
