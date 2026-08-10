# -*- coding: utf-8 -*-
"""
友盟Flutter APM SDK集成 - 主工作流
9步执行流程：
  1. 环境检查
  2. 项目验证
  3. 前置条件检查（umeng_common_sdk 已集成？）
  4. 参数配置
  5. 集成路径决策（纯Flutter App / Native崩溃 / Module）
  6. 项目备份
  7. SDK集成
  8. 编译验证
  9. 集成报告
"""

import argparse
import json
import subprocess
import sys
import os
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_checker import EnvChecker
from project_validator import ProjectValidator
from sdk_integrator import SDKIntegrator
from sdk_verifier import SDKVerifier
from rollback import RollbackManager
from device_detector import DeviceDetector


class FlutterAPMIntegrationWorkflow:
    """Flutter APM SDK集成工作流（9步）"""
    
    def __init__(self, project_path, android_key=None, ios_key=None,
                 channel=None, native_crash=False, skip_build=False, yes=False,
                 build_timeout=1800, no_trace=False, rollback_on_failure=False):
        """
        初始化APM集成工作流
        
        Args:
            project_path: Flutter项目路径
            android_key: Android平台友盟AppKey
            ios_key: iOS平台友盟AppKey
            channel: 渠道标识
            native_crash: 是否启用Native崩溃采集
            skip_build: 是否跳过编译验证
            yes: 是否跳过确认提示
            build_timeout: 编译超时时间（秒），默认1800（30分钟）
            no_trace: 是否禁用 umeng-cli trace 埋点上报
            rollback_on_failure: 编译验证失败时是否自动回滚（默认关闭，保留集成代码便于排查）
        """
        self.project_path = os.path.abspath(project_path)
        self.android_key = android_key
        self.ios_key = ios_key
        self.channel = channel or 'Umeng'
        self.native_crash = native_crash
        self.skip_build = skip_build
        self.yes = yes
        self.build_timeout = build_timeout
        self.no_trace = no_trace
        self.rollback_on_failure = rollback_on_failure
        self.config = {
            'android_key': android_key,
            'ios_key': ios_key,
            'channel': channel or 'Umeng',
            'native_crash': native_crash,
            'skip_build': skip_build,
            'yes': yes,
        }
        self.backup_path = None
        self.start_time = None
        self.project_info = {}
        self.integration_path = 'pure_flutter'  # 默认：纯Flutter App
    
    def run(self):
        """执行完整的9步集成工作流"""
        self.start_time = datetime.now()
        
        print("\n" + "="*60)
        print("🚀 友盟Flutter APM SDK集成工具")
        print("="*60)
        print("\n📁 项目路径: {}".format(self.project_path))
        print("📦 目标SDK: umeng_apm_sdk")
        if self.no_trace:
            print("📡 埋点上报: 已禁用（--no-trace）")
        else:
            print("📡 埋点上报: 已启用（使用 --no-trace 可关闭）")
        print()
        
        # 埋点上报
        self._trace_start()
        
        # 步骤1: 环境检查
        if not self.step1_check_environment():
            return False
        
        # 步骤2: 项目验证
        if not self.step2_validate_project():
            return False
        
        # 步骤3: 前置条件检查（umeng_common_sdk）
        if not self.step3_check_prerequisites():
            return False
        
        # 步骤4: 参数配置
        self.step4_get_config()
        
        # 步骤5: 集成路径决策
        self.step5_decide_integration_path()
        
        # 步骤6: 备份项目
        if not self.step6_backup_project():
            return False
        
        # 步骤7: SDK集成
        if not self.step7_integrate_sdk():
            print("\n❌ SDK集成失败，正在回滚...")
            self._rollback()
            return False
        
        # 步骤8: 编译验证
        if not self.step8_build_project():
            if self.rollback_on_failure:
                print("\n❌ 编译验证失败，正在回滚...")
                self._rollback()
            else:
                print("\n❌ 编译验证失败（已保留集成代码）")
                print("  📋 完整构建日志: build/umeng_integration_build.log")
                print("  💡 排查修复后可手动重新编译；如需回滚请运行 rollback.py")
            return False
        
        # 步骤8.5: SDK 运行时验证
        self.step8b_verify_sdk()
        
        # 步骤9: 集成报告
        self.step9_generate_report()
        
        return True
    
    # ------------------------------------------------------------------
    # 步骤1: 环境检查
    # ------------------------------------------------------------------
    
    def step1_check_environment(self):
        """步骤1: 环境检查"""
        print("\n" + "="*60)
        print("步骤 1/9: 🔍 环境检查")
        print("="*60)
        
        checker = EnvChecker(project_path=self.project_path)
        return checker.check_all()
    
    # ------------------------------------------------------------------
    # 步骤2: 项目验证
    # ------------------------------------------------------------------
    
    def step2_validate_project(self):
        """步骤2: 项目验证"""
        print("\n" + "="*60)
        print("步骤 2/9: 📂 项目验证")
        print("="*60)
        
        if not os.path.exists(self.project_path):
            print("\n❌ 项目路径不存在: {}".format(self.project_path))
            return False
        
        validator = ProjectValidator(self.project_path)
        
        if not validator.validate():
            print("\n❌ 项目验证失败")
            return False
        
        self.project_info = validator.project_info
        
        # 提取 appkey 用于补报埋点
        extracted_appkey = self.config.get('android_key') or self.config.get('ios_key')
        if extracted_appkey and extracted_appkey not in ('YOUR_ANDROID_APPKEY', 'YOUR_IOS_APPKEY'):
            self._trace_start(extracted_appkey)
        
        return True
    
    # ------------------------------------------------------------------
    # 步骤3: 前置条件检查
    # ------------------------------------------------------------------
    
    def step3_check_prerequisites(self):
        """步骤3: 前置条件检查（验证 umeng_common_sdk 已集成）"""
        print("\n" + "="*60)
        print("步骤 3/9: 📋 前置条件检查")
        print("="*60)
        
        validator = ProjectValidator(self.project_path)
        validator.project_info = self.project_info
        
        if not validator.check_umcommon_prerequisite():
            print("\n❌ 前置条件不满足，无法继续APM集成")
            return False
        
        # 提取版本信息
        validator.extract_version_from_pubspec()
        validator.check_flutter_boost()
        
        # 更新 project_info
        self.project_info = validator.project_info
        self.config['project_name'] = self.project_info.get('project_name', 'my_flutter_app')
        self.config['project_version'] = self.project_info.get('project_version', '1.0.0+1')
        self.config['has_flutter_boost'] = self.project_info.get('has_flutter_boost', False)
        self.config['android_namespace'] = self.project_info.get('android_namespace')
        
        return True
    
    # ------------------------------------------------------------------
    # 步骤4: 参数配置
    # ------------------------------------------------------------------
    
    def step4_get_config(self):
        """步骤4: 参数配置"""
        print("\n" + "="*60)
        print("步骤 4/9: ⚙️  参数配置")
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
            if not self.yes:
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
        print("📋 APM集成配置")
        print("-" * 60)
        print("  Android AppKey: {}".format(self.config['android_key']))
        print("  iOS AppKey:     {}".format(self.config['ios_key']))
        print("  Channel:        {}".format(self.config['channel']))
        print("  Native崩溃:     {}".format('✅ 启用' if self.native_crash else '❌ 不启用'))
        print("  项目名称:       {}".format(self.config.get('project_name', 'unknown')))
        print("  项目版本:       {}".format(self.config.get('project_version', 'unknown')))
        print("  Flutter Boost:  {}".format('✅ 检测到' if self.config.get('has_flutter_boost') else '❌ 未检测到'))
        print("-" * 60)
        
        if (self.config['android_key'] != 'YOUR_ANDROID_APPKEY' and 
            self.config['ios_key'] != 'YOUR_IOS_APPKEY'):
            print("\n⚠️  请确认 Android 和 iOS AppKey 没有填反！")
    
    # ------------------------------------------------------------------
    # 步骤5: 集成路径决策
    # ------------------------------------------------------------------
    
    def step5_decide_integration_path(self):
        """步骤5: 集成路径决策"""
        print("\n" + "="*60)
        print("步骤 5/9: 🔀 集成路径决策")
        print("="*60 + "\n")
        
        print("请选择集成路径：")
        print()
        print("  1. 纯 Flutter App（最常见，只监控 Dart 异常）")
        print("     跳过 Native 端配置，最短路径")
        print()
        print("  2. 需要 Native 崩溃采集")
        print("     同时监控 Java/OC 层崩溃，需配置 Android MyApplication + iOS AppDelegate")
        print()
        print("  3. Flutter Module 嵌入原生工程")
        print("     projectType=1，必须执行 Native 端配置")
        print()
        
        if self.yes or self.native_crash:
            # 非交互模式：根据 --native-crash 参数决定
            if self.native_crash:
                self.integration_path = 'native_crash'
                print("✅ 使用 --native-crash 参数，选择路径 2: Native 崩溃采集")
            else:
                self.integration_path = 'pure_flutter'
                print("✅ 非交互模式，默认选择路径 1: 纯 Flutter App")
        else:
            try:
                choice = input("请输入选项 (1/2/3，默认 1): ").strip()
                
                if choice == '2':
                    self.integration_path = 'native_crash'
                    self.native_crash = True
                    self.config['native_crash'] = True
                    print("\n✅ 选择路径 2: Native 崩溃采集")
                elif choice == '3':
                    self.integration_path = 'flutter_module'
                    self.native_crash = True
                    self.config['native_crash'] = True
                    self.config['project_type'] = 1
                    print("\n✅ 选择路径 3: Flutter Module")
                else:
                    self.integration_path = 'pure_flutter'
                    print("\n✅ 选择路径 1: 纯 Flutter App")
            except (EOFError, KeyboardInterrupt):
                self.integration_path = 'pure_flutter'
                print("\n✅ 默认选择路径 1: 纯 Flutter App")
        
        print("\n" + "-" * 60)
        print("📋 集成路径: {}".format(self._get_path_display_name()))
        print("-" * 60)
    
    def _get_path_display_name(self):
        """获取路径显示名称"""
        path_names = {
            'pure_flutter': '纯 Flutter App（步骤 1→2→3→6→7→8→9）',
            'native_crash': 'Native 崩溃采集（步骤 1→2→3→6→7[含Native]→8→9）',
            'flutter_module': 'Flutter Module（步骤 1→2→3→6→7[含Native+projectType=1]→8→9）',
        }
        return path_names.get(self.integration_path, self.integration_path)
    
    # ------------------------------------------------------------------
    # 步骤6: 备份项目
    # ------------------------------------------------------------------
    
    def step6_backup_project(self):
        """步骤6: 备份项目"""
        print("\n" + "="*60)
        print("步骤 6/9: 💾 项目备份")
        print("="*60)
        
        rollback_mgr = RollbackManager(self.project_path)
        self.backup_path = rollback_mgr.backup_project()
        
        if not self.backup_path:
            print("\n❌ 项目备份失败")
            return False
        
        return True
    
    # ------------------------------------------------------------------
    # 步骤7: SDK集成
    # ------------------------------------------------------------------
    
    def step7_integrate_sdk(self):
        """步骤7: SDK集成"""
        print("\n" + "="*60)
        print("步骤 7/9: 🔧 APM SDK集成")
        print("="*60)
        
        # 保存实例供 step9 报告消费 warnings / ios_skipped 等集成细节
        self.integrator = SDKIntegrator(self.project_path, self.config)
        return self.integrator.integrate()
    
    # ------------------------------------------------------------------
    # 步骤8: 编译验证
    # ------------------------------------------------------------------
    
    def step8_build_project(self):
        """步骤8: 编译验证"""
        print("\n" + "="*60)
        print("步骤 8/9: 🏗️ 编译验证")
        print("="*60)
        
        if self.skip_build:
            print("\n⏭️  跳过编译验证（--skip-build 参数）")
            return True
        
        validator = ProjectValidator(self.project_path)
        
        if not validator.build_project(timeout=self.build_timeout):
            print("\n❌ 编译验证失败")
            return False
        
        return True
    
    def step8b_verify_sdk(self):
        """步骤 8.5: SDK 运行时验证"""
        print("\n" + "="*60)
        print("步骤 8.5: SDK 运行时验证")
        print("="*60)
        
        # 设备检测：无设备时跳过运行时验证（不阻塞流程）
        detector = DeviceDetector()
        has_devices = detector.detect_devices()
        if not has_devices:
            print("\n⚠️  未检测到已连接设备，跳过运行时验证")
            print("  💡 连接设备后可手动运行验证")
            return True
        
        verifier = SDKVerifier(self.project_path)
        result = verifier.verify_android()
        # 保留采样率提示
        verifier.print_sampling_notice()
        return result
    
    # ------------------------------------------------------------------
    # 步骤9: 集成报告
    # ------------------------------------------------------------------
    
    def step9_generate_report(self):
        """步骤9: 集成报告"""
        print("\n" + "="*60)
        print("步骤 9/9: 📊 集成报告")
        print("="*60)
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # 集成器产生的待办/警示项（如待激活模板、iOS 被跳过）
        integrator_warnings = getattr(getattr(self, 'integrator', None), 'warnings', []) or []
        ios_skipped = getattr(getattr(self, 'integrator', None), 'ios_skipped', False)
        
        print("\n" + "-" * 60)
        print("📋 Flutter APM SDK集成报告")
        print("-" * 60)
        if integrator_warnings:
            print("  状态:     ✅ 集成成功（含待人工处理项，见下方待办事项）")
        else:
            print("  状态:     ✅ 集成成功")
        print("  项目路径: {}".format(self.project_path))
        print("  集成路径: {}".format(self._get_path_display_name()))
        print("  备份文件: {}".format(self.backup_path))
        print("  耗时:     {}".format(str(duration).split('.')[0]))
        print("  时间:     {}".format(end_time.strftime('%Y-%m-%d %H:%M:%S')))
        print("-" * 60)
        
        print("\n📋 集成内容:")
        print("  ✅ pubspec.yaml - 添加 umeng_apm_sdk 依赖")
        print("  ✅ lib/main.dart - APM 初始化代码（Binding替换 + NavigatorObserver）")
        print("  ✅ Android 端 - 权限 + 混淆规则")
        if self.native_crash:
            print("  ✅ Android - MyApplication (UMCrash.initConfig + preInit)")
            print("  ✅ iOS - AppDelegate (UMAPMConfig 配置)")
        if ios_skipped:
            print("  ⚠️ iOS 端 - 未配置（未找到 Podfile，pod install 被跳过，iOS 原生依赖可能缺失）")
        else:
            print("  ✅ iOS 端 - pod install")
        
        if integrator_warnings:
            print("\n⚠️ 待办事项（集成成功但以下项需人工处理，否则 APM 不会生效）:")
            for w in integrator_warnings:
                print("  - {}".format(w))
        
        print("\n📱 验证方法:")
        print("  Android: adb logcat -d | grep -i 'umeng\\|UMLog\\|apm\\|ApmSdk'")
        print("  iOS:     Xcode Console 过滤 'umeng' 或 'apm'")
        
        print("\n✅ 成功关键词（SDK 2.3.7+ 实测为中文日志，旧版为英文，均有效）:")
        print("  - 成功接收APM Native SDK 初始化状态")
        print("  - 采样率命中 true")
        print("  - 处理异常 日志数N")
        print("  - fluttererror-日志上报成功")
        print("  - apm sdk init success / initialized, version=2.x.x（旧版 SDK）")
        print("  证据链: 成功接收初始化状态 → 采样率命中 true → 处理异常日志数N → fluttererror-日志上报成功")
        
        print("\n⚠️  重要提示:")
        if self.config['android_key'] == 'YOUR_ANDROID_APPKEY':
            print("  - 请替换 lib/main.dart 中的 YOUR_ANDROID_APPKEY 为真实 AppKey")
        if self.config['ios_key'] == 'YOUR_IOS_APPKEY':
            print("  - 请替换 lib/main.dart 中的 YOUR_IOS_APPKEY 为真实 AppKey")
        print("  - 必须在用户同意隐私政策后才能调用 initCommon()")
        print("  - 确认 WidgetsFlutterBinding.ensureInitialized() 已被删除")
        print("  - 确认 ApmNavigatorObserver 已注册到 MaterialApp.navigatorObservers")
        
        # 采样率提示
        verifier = SDKVerifier(self.project_path)
        verifier.print_sampling_notice()
        
        print("\n📚 参考文档:")
        print("  - https://developer.umeng.com/docs/193624/detail/2521038")
        print("="*60)
        
        print("\n🎉 APM SDK集成完成！")
    
    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    
    def _rollback(self):
        """回滚项目"""
        if not self.backup_path:
            print("  ⚠️  没有可用的备份")
            return False
        
        rollback_mgr = RollbackManager(self.project_path)
        return rollback_mgr.rollback(self.backup_path, full=True)
    
    def _trace_start(self, appkey=None):
        """埋点上报"""
        if self.no_trace:
            return
        try:
            trace_data = {"skill_name": "flutter-apm-integration"}
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
        description='友盟Flutter APM SDK集成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式模式
  python3 main.py --project-path /path/to/flutter/project

  # 非交互式模式（纯 Flutter App）
  python3 main.py --project-path /path/to/flutter/project \\
    --android-key YOUR_ANDROID_KEY \\
    --ios-key YOUR_IOS_KEY \\
    --channel Umeng

  # 启用 Native 崩溃采集
  python3 main.py --project-path /path/to/flutter/project \\
    --android-key YOUR_ANDROID_KEY \\
    --ios-key YOUR_IOS_KEY \\
    --native-crash

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
        '--native-crash',
        action='store_true',
        help='启用Native崩溃采集（Android MyApplication + iOS AppDelegate）'
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
        help='编译超时时间（秒），默认1800（30分钟）'
    )
    parser.add_argument(
        '--no-trace',
        action='store_true',
        help='禁用 umeng-cli trace 埋点上报'
    )
    parser.add_argument(
        '--rollback-on-failure',
        action='store_true',
        help='编译验证失败时自动回滚（默认关闭，保留集成代码便于排查）'
    )
    
    args = parser.parse_args()
    
    workflow = FlutterAPMIntegrationWorkflow(
        project_path=args.project_path,
        android_key=args.android_key,
        ios_key=args.ios_key,
        channel=args.channel,
        native_crash=args.native_crash,
        skip_build=args.skip_build,
        yes=args.yes,
        build_timeout=args.timeout,
        no_trace=args.no_trace,
        rollback_on_failure=args.rollback_on_failure
    )
    
    success = workflow.run()
    
    if success:
        print("\n✅ APM集成工具执行完成")
        sys.exit(0)
    else:
        print("\n❌ APM集成工具执行失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
