# -*- coding: utf-8 -*-
"""
友盟iOS APM SDK集成 - 主工作流
9步执行流程：
  1. 环境检查
  2. 项目验证
  3. 前置条件检查（UMCommon已集成）
  4. 参数配置
  5. 备份项目
  6. SDK集成
  7. 编译验证
  8. SDK验证（Console日志检查）
  9. 集成报告生成
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
from rollback import RollbackManager
from device_detector import DeviceDetector


class iOSAPMIntegrationWorkflow:
    """iOS APM SDK集成工作流（9步）"""
    
    def __init__(self, project_path, app_key=None, channel=None, target=None, yes=False):
        """
        初始化APM集成工作流
        
        Args:
            project_path: iOS项目路径
            app_key: 友盟AppKey（可选，APM复用统计SDK已有的appkey）
            channel: 渠道标识
            target: Xcode Target名称
            yes: 是否跳过确认提示
        """
        self.project_path = os.path.abspath(project_path)
        self.app_key = app_key
        self.channel = channel or 'App Store'
        self.target = target
        self.yes = yes
        self.config = {
            'app_key': app_key,
            'channel': channel or 'App Store',
            'target': target,
        }
        self.backup_path = None
        self.start_time = None
    
    def run(self):
        """
        执行完整的9步集成工作流
        
        Returns:
            bool: 集成是否成功
        """
        self.start_time = datetime.now()
        
        print("\n" + "="*60)
        print("🚀 友盟iOS APM SDK集成工具")
        print("="*60)
        print("\n📁 项目路径: {}".format(self.project_path))
        print("📦 目标Pod: UMAPM\n")
        
        # 埋点上报
        self._trace_start()
        
        # 步骤1: 环境检查
        if not self.step1_check_environment():
            return False
        
        # 步骤2: 项目验证
        if not self.step2_validate_project():
            return False
        
        # 步骤3: 前置条件检查（UMCommon）
        if not self.step3_check_prerequisites():
            return False
        
        # 提取 appkey 用于埋点
        extracted_appkey = self.validator.extract_appkey_from_code()
        if extracted_appkey and extracted_appkey not in ('YOUR_APPKEY', 'YOUR_UMENG_APPKEY'):
            self._trace_start(extracted_appkey)
        
        # 步骤4: 参数配置
        self.step4_get_config()
        
        # 步骤5: 备份项目
        if not self.step5_backup_project():
            return False
        
        # 步骤6: SDK集成
        if not self.step6_integrate_sdk():
            print("\n❌ SDK集成失败，正在回滚...")
            self._rollback()
            return False
        
        # 步骤7: 编译验证
        if not self.step7_build_project():
            print("\n❌ 编译验证失败，正在回滚...")
            self._rollback()
            return False
        
        # 步骤8: SDK验证
        self.step8_verify_sdk()
        
        # 步骤9: 集成报告
        self.step9_generate_report()
        
        return True
    
    def step1_check_environment(self):
        """步骤1: 环境检查"""
        print("\n" + "="*60)
        print("步骤 1/9: 🔍 环境检查")
        print("="*60)
        
        checker = EnvChecker()
        return checker.check_all()
    
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
        
        # 保存项目信息供后续使用
        self.project_info = validator.project_info
        return True
    
    def step3_check_prerequisites(self):
        """步骤3: 前置条件检查（验证UMCommon已集成）"""
        print("\n" + "="*60)
        print("步骤 3/9: 📋 前置条件检查")
        print("="*60)
        
        validator = ProjectValidator(self.project_path)
        # 需要先初始化project_info
        validator.project_info = self.project_info
        self.validator = validator
        
        if not validator.check_umcommon_prerequisite():
            print("\n❌ 前置条件不满足，无法继续APM集成")
            return False
        
        return True
    
    def step4_get_config(self):
        """步骤4: 参数配置"""
        print("\n" + "="*60)
        print("步骤 4/9: ⌨️  参数配置")
        print("="*60 + "\n")
        
        print("ℹ️  APM SDK复用统计SDK已配置的AppKey和Channel")
        print("   无需重复配置，初始化代码将自动注入到UMConfigure.initWithAppkey之前")
        
        # 获取Target
        if not self.target:
            if not self.yes:
                print("\n💡 如果项目有多个Target，可以指定要集成的Target")
                print("   (直接回车将使用第一个Target)")
                try:
                    target = input("Target名称 (可选): ").strip()
                    if target:
                        self.config['target'] = target
                except (EOFError, KeyboardInterrupt):
                    pass
            # 非交互模式使用默认
        else:
            self.config['target'] = self.target
            print("\n✅ Target: {}".format(self.target))
        
        # 打印配置
        print("\n" + "-" * 60)
        print("📋 APM集成配置")
        print("-" * 60)
        print("  Pod: UMAPM")
        print("  注入位置: UMConfigure.initWithAppkey 之前")
        if self.config.get('target'):
            print("  Target: {}".format(self.config['target']))
        print("-" * 60)
    
    def step5_backup_project(self):
        """步骤5: 备份项目"""
        print("\n" + "="*60)
        print("步骤 5/9: 💾 备份项目")
        print("="*60)
        
        rollback_mgr = RollbackManager(self.project_path)
        self.backup_path = rollback_mgr.backup_project()
        
        if not self.backup_path:
            print("\n❌ 项目备份失败")
            return False
        
        return True
    
    def step6_integrate_sdk(self):
        """步骤6: SDK集成"""
        print("\n" + "="*60)
        print("步骤 6/9: 📦 APM SDK集成")
        print("="*60)
        
        integrator = SDKIntegrator(self.project_path, self.config)
        return integrator.integrate()
    
    def step7_build_project(self):
        """步骤7: 编译验证"""
        print("\n" + "="*60)
        print("步骤 7/9: 🔨 编译验证")
        print("="*60)
        
        # 重新验证项目（获取最新的workspace信息）
        validator = ProjectValidator(self.project_path)
        validator.validate()
        
        # 传入target名称辅助选择正确的App scheme
        target_name = self.config.get('target') or self.target
        if not validator.build_project(target_name=target_name):
            print("\n❌ 编译验证失败")
            return False
        
        return True
    
    def step8_verify_sdk(self):
        """步骤8: SDK验证（Console日志检查）"""
        print("\n" + "="*60)
        print("步骤 8/9: 🔍 SDK验证")
        print("="*60)
        
        print("\n  ⚠️  占位符检查:")
        print("     请确认 UMConfigure.initWithAppkey 中的 appkey 不是占位符值")
        print("     如为 'YOUR_APPKEY' 等占位符，请先替换为真实 appkey 后再验证")
        
        print("\n💡 APM SDK验证说明:")
        print("   运行App后，在Console中查看以下验证日志:")
        print()
        print("   ✅ 成功关键词（多层验证）:")
        print('     - 基本验证: "[Reporter] SDK init success"（确认SDK初始化成功）')
        print('     - APM模块验证: "UMAPM_NetworkEnable" 或 "UMAPM_MemEnable"（确认APM模块已激活）')
        print('     - 可选参考: "可接入免费的网络分析能力"（部分场景可能出现）')
        print()
        print("   ❌ 失败关键词:")
        print('     - "appkey is null"')
        print('     - "UMCommonSDK init failed"')
        print()
        print("💡 如需手动验证:")
        print("  1. 在Xcode中打开项目:")
        
        workspace_files = [f for f in os.listdir(self.project_path) 
                          if f.endswith('.xcworkspace')]
        if workspace_files:
            print("     open {}".format(
                os.path.join(self.project_path, workspace_files[0])
            ))
        
        print("  2. 选择真机或模拟器作为运行目标")
        print("  3. 点击Run (⌘R) 编译并运行")
        print("  4. 查看Xcode控制台日志")
        print()
        
        # 检测真机
        detector = DeviceDetector()
        detector.detect_devices()
    
    def step9_generate_report(self):
        """步骤9: 集成报告生成"""
        print("\n" + "="*60)
        print("步骤 9/9: 📊 集成报告")
        print("="*60)
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "-" * 60)
        print("📋 iOS APM SDK集成报告")
        print("-" * 60)
        print("  状态:     ✅ 集成成功")
        print("  项目路径: {}".format(self.project_path))
        print("  Pod:      UMAPM")
        print("  备份文件: {}".format(self.backup_path))
        print("  耗时:     {}".format(str(duration).split('.')[0]))
        print("  时间:     {}".format(end_time.strftime('%Y-%m-%d %H:%M:%S')))
        print("-" * 60)
        print("\n🎉 APM SDK集成完成！")
        print("\n下一步:")
        print("  1. 在Xcode中打开.xcworkspace运行项目")
        print('  2. 确认Console输出 "[Reporter] SDK init success" 和 "UMAPM_NetworkEnable"')
        print("  3. 在友盟后台查看APM数据")
        print("="*60)
    
    def _rollback(self):
        """回滚项目"""
        if not self.backup_path:
            print("  ⚠️  没有可用的备份")
            return False
        
        rollback_mgr = RollbackManager(self.project_path)
        return rollback_mgr.rollback(self.backup_path)
    
    def _trace_start(self, appkey=None):
        """埋点上报"""
        try:
            trace_data = {"skill_name": "ios-apm-integration"}
            if appkey and appkey not in ('YOUR_APPKEY', 'YOUR_UMENG_APPKEY'):
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
        description='友盟iOS APM SDK集成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式模式
  python3 main.py --project-path /path/to/ios/project

  # 非交互式模式（自动跳过确认）
  python3 main.py --project-path /path/to/ios/project --yes

  # 指定Target
  python3 main.py --project-path /path/to/ios/project --target MyApp
        """
    )
    
    parser.add_argument(
        '--project-path',
        required=True,
        help='iOS项目路径（包含.xcodeproj的目录）'
    )
    parser.add_argument(
        '--app-key',
        help='友盟AppKey（可选，APM复用统计SDK的AppKey）'
    )
    parser.add_argument(
        '--channel',
        default='App Store',
        help='渠道标识（默认: App Store）'
    )
    parser.add_argument(
        '--target',
        help='Target名称（可选，默认使用第一个Target）'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='跳过所有确认提示（非交互式模式）'
    )
    
    args = parser.parse_args()
    
    # 创建工作流实例
    workflow = iOSAPMIntegrationWorkflow(
        project_path=args.project_path,
        app_key=args.app_key,
        channel=args.channel,
        target=args.target,
        yes=args.yes
    )
    
    # 执行工作流
    success = workflow.run()
    
    if success:
        print("\n✅ APM集成工具执行完成")
        sys.exit(0)
    else:
        print("\n❌ APM集成工具执行失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
