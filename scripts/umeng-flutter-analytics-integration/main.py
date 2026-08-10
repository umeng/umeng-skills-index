# -*- coding: utf-8 -*-
"""
友盟Flutter统计SDK集成 - 主工作流
环境检查 → 项目验证 → 参数交互 → 项目备份 → SDK集成 → 编译验证 → 集成报告
"""

import argparse
import json
import subprocess
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_checker import EnvChecker
from project_validator import ProjectValidator
from sdk_integrator import SDKIntegrator
from sdk_verifier import SDKVerifier
from rollback import RollbackManager
from device_detector import DeviceDetector


class FlutterIntegrationWorkflow:
    """Flutter统计SDK集成工作流"""
    
    def __init__(self, project_path, android_key=None, ios_key=None, 
                 channel=None, skip_build=False, yes=False,
                 timeout=1800, no_trace=False, rollback_on_failure=False):
        self.project_path = os.path.abspath(project_path)
        self.android_key = android_key
        self.ios_key = ios_key
        self.channel = channel or 'Umeng'
        self.skip_build = skip_build
        self.build_timeout = timeout
        self.no_trace = no_trace
        self.rollback_on_failure = rollback_on_failure
        self.config = {
            'android_key': android_key,
            'ios_key': ios_key,
            'channel': channel or 'Umeng',
            'skip_build': skip_build,
            'yes': yes
        }
        self.backup_path = None
        self.project_info = {}
    
    def run(self):
        """执行集成工作流"""
        print("\n" + "="*60)
        print("🚀 友盟Flutter统计SDK集成工具")
        print("="*60)
        print("\n📁 项目路径: {}\n".format(self.project_path))
        
        # 埋点上报提示
        if not self.no_trace:
            print("  ℹ️  将通过 umeng-cli trace 上报使用情况（可通过 --no-trace 关闭）")
            self._trace_start()
        
        # 步骤1: 环境检查
        if not self.step1_check_environment():
            return False
        
        # 步骤2: 项目验证
        if not self.step2_validate_project():
            return False
        
        # 步骤3: 参数交互
        self.step3_get_config()
        
        # 步骤4: 备份项目
        if not self.step4_backup_project():
            return False
        
        # 步骤5: SDK集成
        if not self.step5_integrate_sdk():
            # 集成失败，回滚
            print("\n❌ SDK集成失败，正在回滚...")
            self.rollback()
            return False
        
        # 步骤6: 编译验证
        if not self.step6_build_project():
            if self.rollback_on_failure:
                print("\n❌ 编译验证失败，正在回滚...")
                self.rollback()
            else:
                print("\n❌ 编译验证失败（已保留集成代码）")
                print("  📋 完整构建日志: build/umeng_integration_build.log")
                print("  💡 排查修复后可手动重新编译；如需回滚请运行 rollback.py")
            return False
        
        # 步骤6.5: SDK 运行时验证
        if not self.step6b_verify_sdk():
            print("\n⚠️  SDK 运行时验证未通过（不影响集成，可稍后手动验证）")
        
        # 步骤7: 生成报告
        self.step7_generate_report()
        
        print("\n" + "="*60)
        print("✅ SDK集成完成")
        print("="*60)
        print("\n备份文件: {}".format(self.backup_path))
        
        return True
    
    def step1_check_environment(self):
        """步骤1: 环境检查"""
        print("\n" + "="*60)
        print("步骤 1/7: 🔍 环境检查")
        print("="*60)
        
        checker = EnvChecker()
        return checker.check_all(project_path=self.project_path)
    
    def step2_validate_project(self):
        """步骤2: 项目验证"""
        print("\n" + "="*60)
        print("步骤 2/7: 📋 项目验证")
        print("="*60)
        
        # 检查项目路径是否存在
        if not os.path.exists(self.project_path):
            print("\n❌ 项目路径不存在: {}".format(self.project_path))
            return False
        
        validator = ProjectValidator(self.project_path)
        
        if not validator.validate():
            print("\n❌ 项目验证失败")
            return False
        
        # 保存项目信息供后续步骤使用
        self.project_info = validator.project_info
        self.config['android_namespace'] = self.project_info.get('android_namespace')
        
        # 提取 appkey 用于补报埋点
        extracted_appkey = self.config.get('android_key') or self.config.get('ios_key')
        if not self.no_trace and extracted_appkey and extracted_appkey not in ('YOUR_ANDROID_APPKEY', 'YOUR_IOS_APPKEY'):
            self._trace_start(extracted_appkey)
        
        return True
    
    def step3_get_config(self):
        """步骤3: 参数交互"""
        print("\n" + "="*60)
        print("步骤 3/7: ⚙️  参数配置")
        print("="*60 + "\n")
        
        # 获取Android AppKey
        if not self.android_key:
            print("请输入 Android 平台友盟 AppKey:")
            print("  (在友盟后台创建Android应用后获取，或留空使用占位符)")
            android_key = input("\nAndroid AppKey: ").strip()
            
            if android_key:
                self.config['android_key'] = android_key
            else:
                self.config['android_key'] = 'YOUR_ANDROID_APPKEY'
                print("\n💡 使用占位符: YOUR_ANDROID_APPKEY")
                print("   集成后需要替换为真实的Android AppKey")
        else:
            print("✅ Android AppKey: {}".format(self.android_key))
        
        # 获取iOS AppKey
        if not self.ios_key:
            print("\n请输入 iOS 平台友盟 AppKey:")
            print("  (在友盟后台创建iOS应用后获取，或留空使用占位符)")
            ios_key = input("\niOS AppKey: ").strip()
            
            if ios_key:
                self.config['ios_key'] = ios_key
            else:
                self.config['ios_key'] = 'YOUR_IOS_APPKEY'
                print("\n💡 使用占位符: YOUR_IOS_APPKEY")
                print("   集成后需要替换为真实的iOS AppKey")
        else:
            print("\n✅ iOS AppKey: {}".format(self.ios_key))
        
        # 获取Channel
        if not self.channel or self.channel == 'Umeng':
            if not self.config.get('yes'):
                print("\n请输入渠道标识 (默认: Umeng):")
                channel = input("Channel: ").strip()
                
                if channel:
                    self.config['channel'] = channel
                else:
                    self.config['channel'] = 'Umeng'
            else:
                self.config['channel'] = 'Umeng'
        else:
            print("\n✅ Channel: {}".format(self.channel))
        
        # 打印配置
        print("\n" + "-" * 60)
        print("📋 集成配置")
        print("-" * 60)
        print("  Android AppKey: {}".format(self.config['android_key']))
        print("  iOS AppKey:     {}".format(self.config['ios_key']))
        print("  Channel:        {}".format(self.config['channel']))
        print("-" * 60)
        
        # 警告用户不要填反
        if (self.config['android_key'] != 'YOUR_ANDROID_APPKEY' and 
            self.config['ios_key'] != 'YOUR_IOS_APPKEY'):
            print("\n⚠️  请确认 Android 和 iOS AppKey 没有填反！")
            print("   友盟后台中 Android 和 iOS 是不同的 AppKey")
    
    def step4_backup_project(self):
        """步骤4: 备份项目"""
        print("\n" + "="*60)
        print("步骤 4/7: 💾 项目备份")
        print("="*60)
        
        rollback_mgr = RollbackManager(self.project_path)
        self.backup_path = rollback_mgr.backup_project()
        
        if not self.backup_path:
            print("\n❌ 项目备份失败")
            return False
        
        return True
    
    def step5_integrate_sdk(self):
        """步骤5: SDK集成"""
        print("\n" + "="*60)
        print("步骤 5/7: 🔧 SDK集成")
        print("="*60)
        
        integrator = SDKIntegrator(self.project_path, self.config)
        return integrator.integrate()
    
    def step6_build_project(self):
        """步骤6: 编译验证"""
        print("\n" + "="*60)
        print("步骤 6/7: 🏗️ 编译验证")
        print("="*60)
        
        if self.skip_build:
            print("\n⏭️  跳过编译验证（--skip-build 参数）")
            return True
        
        validator = ProjectValidator(self.project_path)
        
        if not validator.build_project(build_timeout=self.build_timeout):
            print("\n❌ 编译验证失败")
            return False
        
        return True
    
    def step6b_verify_sdk(self):
        """步骤 6.5: SDK 运行时验证"""
        print("\n" + "="*60)
        print("步骤 6.5: SDK 运行时验证")
        print("="*60)
        
        # 先检测已连接的设备
        detector = DeviceDetector()
        detector.detect_devices()
        if not detector.android_devices and not detector.ios_devices:
            print("  ⚠️ 未检测到已连接的设备，跳过运行时验证")
            print("  ℹ️  编译验证已通过，SDK集成成功")
            return True
        
        verifier = SDKVerifier(self.project_path)
        return verifier.verify_android()
    
    def rollback(self):
        """回滚项目"""
        if not self.backup_path:
            print("  ⚠️  没有可用的备份")
            return False
        
        rollback_mgr = RollbackManager(self.project_path)
        return rollback_mgr.rollback(self.backup_path, full=True)
    
    def step7_generate_report(self):
        """步骤7: 生成集成报告"""
        print("\n" + "="*60)
        print("步骤 7/7: 📊 集成报告")
        print("="*60)
        
        print("\n" + "="*60)
        print("✅ 友盟Flutter统计SDK集成完成")
        print("="*60)
        
        print("\n📋 集成内容:")
        print("  ✅ pubspec.yaml - 添加 umeng_common_sdk 依赖")
        print("  ✅ Android 端 - AndroidManifest 权限 + MyApplication + 混淆规则")
        print("  ✅ iOS 端 - pod install 安装原生依赖（零原生代码修改）")
        print("  ✅ Dart 层 - lib/main.dart 初始化代码")
        
        print("\n📱 验证方法:")
        print("  Android: adb logcat -d | grep -i 'umeng\\|UMLog\\|MobClick'")
        print("  iOS:     Xcode Console 过滤 'umeng'")
        
        print("\n✅ 成功关键词:")
        print("  - preInit success")
        print("  - initCommon called")
        
        print("\n⚠️  重要提示:")
        if self.config['android_key'] == 'YOUR_ANDROID_APPKEY':
            print("  - 请替换 lib/main.dart 中的 YOUR_ANDROID_APPKEY 为真实 AppKey")
        if self.config['ios_key'] == 'YOUR_IOS_APPKEY':
            print("  - 请替换 lib/main.dart 中的 YOUR_IOS_APPKEY 为真实 AppKey")
        print("  - 必须在用户同意隐私政策后才能调用 initCommon()")
        print("  - iOS 端已执行 pod install，无需修改原生代码")
        
        print("\n📚 参考文档:")
        print("  - https://developer.umeng.com/docs/119267/detail/174923")
        print("="*60)
    
    def _trace_start(self, appkey=None):
        """埋点上报"""
        try:
            trace_data = {"skill_name": "flutter-analytics-integration"}
            if appkey and appkey not in ('YOUR_ANDROID_APPKEY', 'YOUR_IOS_APPKEY'):
                trace_data["appkey"] = appkey
            subprocess.run(
                ['umeng-cli', 'trace', json.dumps(trace_data)],
                capture_output=True, text=True, timeout=5
            )
        except Exception:
            pass


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='友盟Flutter统计SDK集成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式模式
  python3 main.py --project-path /path/to/flutter/project

  # 非交互式模式
  python3 main.py --project-path /path/to/flutter/project \\
    --android-key YOUR_ANDROID_KEY \\
    --ios-key YOUR_IOS_KEY \\
    --channel Umeng

  # 跳过编译验证
  python3 main.py --project-path /path/to/flutter/project --skip-build
  
  # 跳过所有确认提示
  python3 main.py --project-path /path/to/flutter/project \\
    --android-key YOUR_ANDROID_KEY --ios-key YOUR_IOS_KEY --yes
        """
    )
    
    parser.add_argument(
        '--project-path',
        required=True,
        help='Flutter项目路径（包含pubspec.yaml的目录）'
    )
    parser.add_argument(
        '--android-key',
        help='Android平台友盟AppKey（可选，不传则交互式输入或使用占位符）'
    )
    parser.add_argument(
        '--ios-key',
        help='iOS平台友盟AppKey（可选，不传则交互式输入或使用占位符）'
    )
    parser.add_argument(
        '--channel',
        default='Umeng',
        help='渠道标识（默认: Umeng）'
    )
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='跳过编译验证步骤'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='跳过所有确认提示（非交互式模式）'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=1800,
        help='编译超时时间(秒)，默认1800秒'
    )
    parser.add_argument(
        '--no-trace',
        action='store_true',
        help='禁用 Skill 使用情况上报'
    )
    parser.add_argument(
        '--rollback-on-failure',
        action='store_true',
        help='编译失败时自动回滚（默认保留集成代码以便排查）'
    )
    
    args = parser.parse_args()
    
    # 创建工作流实例
    workflow = FlutterIntegrationWorkflow(
        project_path=args.project_path,
        android_key=args.android_key,
        ios_key=args.ios_key,
        channel=args.channel,
        skip_build=args.skip_build,
        yes=args.yes,
        timeout=args.timeout,
        no_trace=args.no_trace,
        rollback_on_failure=args.rollback_on_failure
    )
    
    # 执行工作流
    success = workflow.run()
    
    if success:
        print("\n✅ 集成工具执行完成")
        sys.exit(0)
    else:
        print("\n❌ 集成工具执行失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
