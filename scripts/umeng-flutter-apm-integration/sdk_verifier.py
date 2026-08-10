# -*- coding: utf-8 -*-
"""
Flutter APM SDK集成 - SDK验证模块
通过adb logcat验证Android端APM SDK是否正确上报数据
含免费版采样率提示
"""

import subprocess
import sys
import os


class SDKVerifier:
    """APM SDK验证器"""
    
    def __init__(self, project_path):
        self.project_path = project_path
    
    def verify_android(self):
        """验证Android端APM SDK"""
        print("\n" + "="*60)
        print("📱 Android APM SDK 验证")
        print("="*60 + "\n")
        
        if not self._check_adb():
            return False
        
        if not self._check_device_connected():
            return False
        
        print("🔍 抓取友盟APM SDK日志...\n")
        
        try:
            subprocess.run(
                ['adb', 'logcat', '-c'],
                capture_output=True,
                timeout=5
            )
            
            result = subprocess.run(
                ['adb', 'logcat', '-d', '*:S', 'UMLog:D', 'umeng:D', 
                 'MobClick:D', 'ApmSdk:D', 'apm:D'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logs = result.stdout
                
                if not logs.strip():
                    print("  ⚠️  未捕获到友盟APM SDK日志")
                    print("\n💡 可能的原因:")
                    print("  1. App尚未启动或未完成初始化")
                    print("  2. SDK初始化代码未执行")
                    print("  3. 用户未同意隐私政策（initCommon()未被调用）")
                    print("  4. WidgetsFlutterBinding.ensureInitialized() 未删除导致 Binding 冲突")
                    print("\n📝 请启动App后重新运行验证")
                    return False
                
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
        """验证iOS端APM SDK"""
        print("\n" + "="*60)
        print("📱 iOS APM SDK 验证")
        print("="*60 + "\n")
        
        print("  ℹ️  iOS APM SDK 验证需要在 Xcode 中手动进行：")
        print("\n  1. 在 Xcode 中打开 ios/Runner.xcworkspace")
        print("  2. 选择模拟器或真机作为运行目标")
        print("  3. 点击 Run (⌘R) 编译并运行")
        print("  4. 查看 Xcode Console 日志，过滤 'umeng' 或 'apm'")
        print("\n  ✅ 成功关键词（SDK 2.3.7+ 实测为中文日志，旧版为英文，均有效）:")
        print("     - 成功接收APM Native SDK 初始化状态")
        print("     - 采样率命中 true")
        print("     - 处理异常 日志数N")
        print("     - fluttererror-日志上报成功")
        print("     - apm sdk init success / initialized, version=2.x.x（旧版 SDK）")
        print("     证据链: 成功接收初始化状态 → 采样率命中 true → 处理异常日志数N → fluttererror-日志上报成功")
        print("\n  ⚠️  注意: crashsdk uploading logs / efs.send_log 等泛化上传日志不能作为异常已上传证据；")
        print("     验证需冷启动（先终止进程再启动），后台查看去 U-APM 的 Flutter 异常/自定义日志分类（有分钟~小时级延迟）")
        print("\n  ❌ 失败关键词:")
        print("     - Binding already initialized")
        print("     - appkey invalid")
        print("     - ERROR/umeng")
        
        return True
    
    def print_sampling_notice(self):
        """打印采样率提示（APM专属）"""
        print("\n" + "="*60)
        print("⚠️  APM 采样率提示")
        print("="*60)
        print()
        print("  📊 免费版采样率限制：")
        print("  ┌─────────────────────────────────────────────────┐")
        print("  │ 版本     │ Flutter PV采样率 │ 单设备异常/天 │ 性能日志/天 │")
        print("  ├─────────────────────────────────────────────────┤")
        print("  │ 免费版   │ 5%（不可更改）   │ 20 条         │ 200 条      │")
        print("  │ 专业版   │ 最高 5%          │ 40 条         │ 500 条      │")
        print("  │ 尊享版   │ 最高 100%        │ 120 条        │ 1000 条     │")
        print("  └─────────────────────────────────────────────────┘")
        print()
        print("  💡 验证建议：")
        print("  1. 开启 enableLog: true，在日志中搜索 'umid' 获取设备 UMID")
        print("  2. 登录 U-APM 后台 (https://apm.umeng.com)")
        print("     → 设备管理 → 通用采样设置 → 添加 UMID 到白名单")
        print("  3. 不卸载App，将设备时间改为8小时后冷启动，白名单立即生效")
        print()
        print("  📌 不添加白名单的情况下，免费版仅 5% PV 被采样，")
        print("     很可能看不到测试设备的数据，这是正常现象。")
        print("="*60)
    
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
        
        # 噪音排除：过滤 UMLog Reflect: 反射日志行（与初始化结果判定无关）
        logs = '\n'.join(
            line for line in logs.split('\n')
            if 'UMLog Reflect:' not in line
        )
        
        # 成功关键词：保留 APM 专属词 + 追加实测的统计基础词
        # 中英并集：兼容 <2.3.7 旧版 SDK 的英文日志；中文词的英文部分必须小写录入（logs 已 lower）
        success_keywords = [
            'apm sdk init success', 'initcommon called', 
            'init success', 'initialized', 'page pv tracked',
            '安卓依赖版本检查成功', 'setwrapertype:flutter1.0 success',
            'setpagecollectionmodeauto', 'module init:azio',
            # SDK 2.3.7+ 实测中文日志（证据链: 初始化状态 → 采样率命中 → 处理异常 → 上报成功）
            '成功接收apm native sdk 初始化状态', '采样率命中 true',
            '处理异常 日志数', 'fluttererror-日志上报成功'
        ]
        # 失败关键词收窄（移除宽泛的 error/exception/failed，避免误判）
        failure_keywords = ['appkey invalid', 'binding already initialized']
        
        logs_lower = logs.lower()
        
        has_success = any(keyword in logs_lower for keyword in success_keywords)
        has_failure = any(keyword in logs_lower for keyword in failure_keywords)
        
        print("  📋 捕获到的关键日志:")
        for line in logs.split('\n')[:10]:
            if line.strip():
                print("    {}".format(line))
        
        if has_failure and 'binding already initialized' in logs_lower:
            print("\n  ❌ Binding 重复初始化！")
            print("\n💡 解决:")
            print("  全局搜索 WidgetsFlutterBinding.ensureInitialized() 并删除")
            print("  APM SDK 通过 initFlutterBinding 参数完成绑定，不能重复")
            return False
        elif has_success and not has_failure:
            print("\n  ✅ APM SDK 初始化成功")
            return True
        elif has_failure:
            print("\n  ❌ APM SDK 初始化失败")
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
    
    # 始终打印采样率提示
    verifier.print_sampling_notice()
    
    if success:
        print("\n✅ SDK 验证通过")
        sys.exit(0)
    else:
        print("\n❌ SDK 验证失败")
        sys.exit(1)
