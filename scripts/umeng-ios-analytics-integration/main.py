# -*- coding: utf-8 -*-
"""
友盟iOS统计SDK集成 - 主工作流
环境检查 → 项目验证 → 参数交互 → SDK集成 → 编译验证 → SDK验证 → 生成报告
"""

import argparse
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_checker import EnvChecker
from project_validator import ProjectValidator
from sdk_integrator import SDKIntegrator
from rollback import RollbackManager
from device_detector import DeviceDetector


class iOSIntegrationWorkflow:
    """iOS统计SDK集成工作流"""
    
    def __init__(self, project_path, app_key=None, channel=None, target=None, yes=False):
        self.project_path = os.path.abspath(project_path)
        self.app_key = app_key
        self.channel = channel or 'App Store'
        self.target = target
        self.config = {
            'app_key': app_key,
            'channel': channel or 'App Store',
            'target': target,
            'yes': yes
        }
        self.backup_path = None
    
    def run(self):
        """执行集成工作流"""
        print("\n" + "="*60)
        print("🚀 友盟iOS统计SDK集成工具")
        print("="*60)
        print("\n📁 项目路径: {}\n".format(self.project_path))
        
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
            # 编译失败，回滚
            print("\n❌ 编译验证失败，正在回滚...")
            self.rollback()
            return False
        
        # 步骤7: SDK验证（预留，当前版本不实现）
        self.step7_verify_on_device()
        
        print("\n" + "="*60)
        print("✅ SDK集成完成")
        print("="*60)
        print("\n备份文件: {}".format(self.backup_path))
        
        return True
    
    def step1_check_environment(self):
        """步骤1: 环境检查"""
        print("\n" + "="*60)
        print("步骤 1/6: 🔍 环境检查")
        print("="*60)
        
        checker = EnvChecker()
        return checker.check_all()
    
    def step2_validate_project(self):
        """步骤2: 项目验证"""
        print("\n" + "="*60)
        print("步骤 2/6: 📂 项目验证")
        print("="*60)
        
        # 检查项目路径是否存在
        if not os.path.exists(self.project_path):
            print("\n❌ 项目路径不存在: {}".format(self.project_path))
            return False
        
        validator = ProjectValidator(self.project_path)
        
        if not validator.validate():
            print("\n❌ 项目验证失败")
            return False
        
        # 可选：编译验证
        if not self.config.get('yes'):
            print("\n是否进行编译验证? (这可能需要几分钟) [y/N]: ")
            try:
                if sys.version_info[0] == 2:
                    choice = raw_input().strip().lower()
                else:
                    choice = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                choice = 'n'
        else:
            choice = 'y'
        
        if choice == 'y':
            if not validator.build_project():
                print("\n❌ 编译验证失败，请先在Xcode中修复编译错误")
                return False
        
        return True
    
    def step3_get_config(self):
        """步骤3: 参数交互"""
        print("\n" + "="*60)
        print("步骤 3/6: ⌨️  参数配置")
        print("="*60 + "\n")
        
        # 获取AppKey
        if not self.app_key:
            print("请输入友盟AppKey:")
            print("  (在友盟后台创建应用后获取，或留空使用占位符)")
            app_key = input("\nAppKey: ").strip()
            
            if app_key:
                self.config['app_key'] = app_key
            else:
                self.config['app_key'] = 'YOUR_UMENG_APPKEY'
                print("\n💡 使用占位符: YOUR_UMENG_APPKEY")
                print("   集成后需要替换为真实的AppKey")
        else:
            print("✅ AppKey: {}".format(self.app_key))
        
        # 获取Channel
        if not self.channel or self.channel == 'App Store':
            if not self.config.get('yes'):
                print("\n请输入渠道标识 (默认: App Store):")
                channel = input("Channel: ").strip()
                
                if channel:
                    self.config['channel'] = channel
                else:
                    self.config['channel'] = 'App Store'
            else:
                self.config['channel'] = 'App Store'
        else:
            print("\n✅ Channel: {}".format(self.channel))
        
        # 获取Target
        if not self.target:
            if not self.config.get('yes'):
                print("\n💡 如果项目有多个Target，可以指定要集成的Target")
                print("   (直接回车将使用第一个Target)")
                try:
                    target = input("Target名称 (可选): ").strip()
                    if target:
                        self.config['target'] = target
                except (EOFError, KeyboardInterrupt):
                    # 非交互模式，使用默认
                    pass
        else:
            print("\n✅ Target: {}".format(self.target))
        
        # 打印配置
        print("\n" + "-" * 60)
        print("📋 集成配置")
        print("-" * 60)
        print("  AppKey:  {}".format(self.config['app_key']))
        print("  Channel: {}".format(self.config['channel']))
        if self.config['target']:
            print("  Target:  {}".format(self.config['target']))
        print("-" * 60)
    
    def step4_backup_project(self):
        """步骤4: 备份项目"""
        print("\n" + "="*60)
        print("步骤 4/6: 💾 备份项目")
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
        print("步骤 5/6: 📦 SDK集成")
        print("="*60)
        
        integrator = SDKIntegrator(self.project_path, self.config)
        return integrator.integrate()
    
    def step6_build_project(self):
        """步骤6: 编译验证"""
        print("\n" + "="*60)
        print("步骤 6/6: 🔨 编译验证")
        print("="*60)
        
        # 重新验证项目（获取最新的workspace信息）
        validator = ProjectValidator(self.project_path)
        validator.validate()  # 更新project_info
        
        # 直接编译，不询问
        if not validator.build_project():
            print("\n❌ 编译验证失败")
            return False
        
        return True
    
    def rollback(self):
        """回滚项目"""
        if not self.backup_path:
            print("  ⚠️  没有可用的备份")
            return False
        
        rollback_mgr = RollbackManager(self.project_path)
        return rollback_mgr.rollback(self.backup_path)
    
    def step7_verify_on_device(self):
        """步骤7: SDK验证（预留，当前版本不实现）"""
        print("\n" + "="*60)
        print("步骤 7/7: ✅ SDK验证")
        print("="*60)
        print("\n🔜 SDK验证功能将在后续版本实现")
        print("   当前版本已完成SDK集成和编译验证")
        print("\n💡 如需手动验证:")
        print("  1. 在Xcode中打开项目:")
        print("     open {}.xcworkspace".format(
            os.path.join(self.project_path, 
                        os.path.basename(self.project_path).replace('.xcodeproj', ''))
        ))
        print("  2. 选择模拟器或真机作为运行目标")
        print("  3. 点击Run (⌘R) 编译并运行")
        print("  4. 查看Xcode控制台日志")
        print("\n✅ 成功关键词:")
        print('  - "网络请求成功(Response Applog)"')
        print('  - "success": "ok"')
        print("\n❌ 失败关键词:")
        print('  - "appkey is null"')
        print('  - "CIE10001"')
        print('  - "UMCommonSDK init failed"')
        print("="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='友盟iOS统计SDK集成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式模式
  python3 main.py --project-path /path/to/ios/project

  # 非交互式模式
  python3 main.py --project-path /path/to/ios/project --app-key YOUR_KEY --channel YOUR_CHANNEL

  # 指定Target
  python3 main.py --project-path /path/to/ios/project --target MyApp
  
  # 跳过所有确认提示
  python3 main.py --project-path /path/to/ios/project --app-key YOUR_KEY --yes
        """
    )
    
    parser.add_argument(
        '--project-path',
        required=True,
        help='iOS项目路径（包含.xcodeproj的目录）'
    )
    parser.add_argument(
        '--app-key',
        help='友盟AppKey（可选，不传则交互式输入或使用占位符）'
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
    workflow = iOSIntegrationWorkflow(
        project_path=args.project_path,
        app_key=args.app_key,
        channel=args.channel,
        target=args.target,
        yes=args.yes
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
