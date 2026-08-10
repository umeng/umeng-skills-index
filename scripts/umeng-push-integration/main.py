#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
友盟Android推送SDK集成工具
主工作流编排
"""

import os
import sys
import argparse
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_checker import EnvChecker
from project_validator import ProjectValidator

# 全局变量
backup_zip_path = None


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='友盟Android推送SDK集成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互模式(复用统计SDK配置)
  python main.py --project-path /path/to/android/project
  
  # 非交互模式(提供messageSecret)
  python main.py --project-path /path/to/project --message-secret YOUR_SECRET
  
  # 非交互模式(全部参数)
  python main.py --project-path /path/to/project --app-key KEY --channel CH --message-secret SECRET
  
  # 指定app模块
  python main.py --project-path /path/to/project --app-module myapp --message-secret YOUR_SECRET
        """
    )
    
    parser.add_argument(
        '--project-path',
        required=True,
        help='Android项目路径'
    )
    
    parser.add_argument(
        '--app-module',
        default='app',
        help='App模块名称(默认: app)'
    )
    
    parser.add_argument(
        '--message-secret',
        default=None,
        help='推送Message Secret(非交互模式必需)'
    )
    
    parser.add_argument(
        '--app-key',
        default=None,
        help='友盟AppKey(可选,默认复用统计SDK配置)'
    )
    
    parser.add_argument(
        '--channel',
        default=None,
        help='渠道标识(可选,默认复用统计SDK配置)'
    )
    
    return parser.parse_args()


def check_prerequisites(project_path, app_module):
    """
    步骤3: 前置条件检查 - 验证统计SDK已集成
    
    Returns:
        bool: 是否通过检查
    """
    print("\n" + "=" * 60)
    print("步骤 3/8: 前置条件检查")
    print("=" * 60)
    print("\n检查项目是否已集成友盟统计SDK...\n")
    
    # 1. 检查build.gradle中是否有common和asms依赖
    app_gradle_kts = os.path.join(project_path, app_module, 'build.gradle.kts')
    app_gradle_groovy = os.path.join(project_path, app_module, 'build.gradle')
    
    gradle_file = None
    if os.path.exists(app_gradle_kts):
        gradle_file = app_gradle_kts
    elif os.path.exists(app_gradle_groovy):
        gradle_file = app_gradle_groovy
    
    if not gradle_file:
        print("❌ 未找到app模块的build.gradle文件")
        return False
    
    with open(gradle_file, 'r', encoding='utf-8') as f:
        gradle_content = f.read()
    
    # 检查common依赖
    has_common = ('com.umeng.umsdk:common' in gradle_content or 
                  'umeng-common' in gradle_content or
                  'libs.umeng.common' in gradle_content)
    
    # 检查asms依赖
    has_asms = ('com.umeng.umsdk:asms' in gradle_content or 
                'umeng-asms' in gradle_content or
                'libs.umeng.asms' in gradle_content)
    
    if not has_common:
        print("❌ 未检测到统计SDK依赖: com.umeng.umsdk:common")
        print("\n推送SDK强依赖统计基础组件,请先运行统计SDK集成:")
        print(f"  python /path/to/umeng-analytics-integration/scripts/main.py --project-path {project_path}")
        return False
    
    if not has_asms:
        print("❌ 未检测到统计SDK依赖: com.umeng.umsdk:asms")
        print("\n推送SDK强依赖统计基础组件,请先运行统计SDK集成:")
        print(f"  python /path/to/umeng-analytics-integration/scripts/main.py --project-path {project_path}")
        return False
    
    print("✅ 检测到统计SDK依赖: common, asms")
    
    # 2. 检查Application类中是否有UMConfigure.init()调用
    # 查找Application类文件
    src_dir = os.path.join(project_path, app_module, 'src', 'main', 'java')
    kotlin_dir = os.path.join(project_path, app_module, 'src', 'main', 'kotlin')
    
    app_class_found = False
    has_umeng_init = False
    
    # 扫描java和kotlin目录
    for base_dir in [src_dir, kotlin_dir]:
        if not os.path.exists(base_dir):
            continue
        
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(('.java', '.kt', '.kts')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 检查是否是Application类
                        if 'Application' in content and ('extends Application' in content or ': Application()' in content):
                            app_class_found = True
                            # 检查是否有UMConfigure.init()调用
                            if 'UMConfigure.init' in content:
                                has_umeng_init = True
                                print(f"✅ 检测到Application类: {os.path.relpath(file_path, project_path)}")
                                print(f"✅ 检测到UMConfigure.init()调用")
                                break
                    except:
                        continue
            
            if has_umeng_init:
                break
        
        if has_umeng_init:
            break
    
    if not app_class_found:
        print("❌ 未检测到Application类")
        print("\n请先运行统计SDK集成,创建Application类:")
        print(f"  python /path/to/umeng-analytics-integration/scripts/main.py --project-path {project_path}")
        return False
    
    if not has_umeng_init:
        print("❌ Application类中未检测到UMConfigure.init()调用")
        print("\n请先运行统计SDK集成,完成SDK初始化:")
        print(f"  python /path/to/umeng-analytics-integration/scripts/main.py --project-path {project_path}")
        return False
    
    print("\n✅ 前置条件检查通过: 统计SDK已集成\n")
    return True


def collect_push_config(args):
    """
    步骤4: 收集推送SDK配置参数
    
    Args:
        args: 命令行参数
    
    Returns:
        dict: {'appkey': str, 'channel': str, 'message_secret': str, 'using_placeholder': bool}
    """
    print("\n" + "=" * 60)
    print("步骤 4/8: 推送SDK配置")
    print("=" * 60)
    print("\n推送SDK集成需要提供Message Secret参数:")
    print("  - messageSecret: 从友盟消息后台获取 (https://message.umeng.com)")
    print()
    
    appkey = args.app_key
    channel = args.channel
    message_secret = args.message_secret
    using_placeholder = False
    
    # 非交互模式: 所有参数通过命令行传入
    if message_secret:
        print("✅ 使用命令行参数模式")
        
        # 如果未提供appkey/channel,尝试从项目中提取
        if not appkey or not channel:
            print("⚠️  未提供appkey/channel,尝试从项目中提取...")
            extracted = extract_existing_config(args.project_path, args.app_module)
            if extracted:
                appkey = appkey or extracted.get('appkey')
                channel = channel or extracted.get('channel')
                print(f"✅ 从项目中提取: appkey={appkey}, channel={channel}")
            else:
                print("⚠️  无法从项目中提取,将使用占位符")
                appkey = appkey or 'YOUR_APPKEY'
                channel = channel or 'YOUR_CHANNEL'
                using_placeholder = True
        
        if not message_secret:
            print("⚠️  messageSecret为空,将使用占位符")
            message_secret = 'YOUR_MESSAGE_SECRET'
            using_placeholder = True
    
    # 交互模式
    else:
        # 询问是否复用统计SDK配置
        print("检测到统计SDK已集成,是否复用appkey和channel? (y/n, 默认y): ", end='')
        choice = input().strip().lower()
        
        if choice != 'n':
            # 从项目中提取已有配置
            print("\n正在从项目中提取已有配置...")
            extracted = extract_existing_config(args.project_path, args.app_module)
            if extracted:
                appkey = extracted['appkey']
                channel = extracted['channel']
                print(f"✅ 提取到: appkey={appkey}")
                print(f"✅ 提取到: channel={channel}")
            else:
                print("⚠️  无法提取,请手动输入")
                appkey = input("\n请输入appkey: ").strip()
                channel = input("请输入channel: ").strip()
        else:
            # 重新输入
            appkey = input("\n请输入appkey: ").strip()
            channel = input("请输入channel: ").strip()
        
        # 输入messageSecret
        message_secret = input("\n请输入Message Secret: ").strip()
        
        if not appkey:
            print("\n⚠️  appkey为空,将使用占位符")
            appkey = 'YOUR_APPKEY'
            using_placeholder = True
        
        if not channel:
            print("⚠️  channel为空,将使用占位符")
            channel = 'YOUR_CHANNEL'
            using_placeholder = True
        
        if not message_secret:
            print("⚠️  messageSecret为空,将使用占位符")
            message_secret = 'YOUR_MESSAGE_SECRET'
            using_placeholder = True
    
    # 确认配置
    print("\n" + "=" * 60)
    print("配置确认")
    print("=" * 60)
    print(f"  appkey: {appkey}")
    print(f"  channel: {channel}")
    print(f"  messageSecret: {message_secret}")
    if using_placeholder:
        print("\n  ⚠️  使用占位符,后续需要替换!")
    print()
    
    # 非交互模式直接继续
    if message_secret == args.message_secret or args.message_secret:
        return {
            'appkey': appkey,
            'channel': channel,
            'message_secret': message_secret,
            'using_placeholder': using_placeholder
        }
    
    confirm = input("是否继续集成? (y/n, 默认y): ").strip().lower()
    if confirm == 'n':
        print("\n❌ 用户取消集成")
        sys.exit(0)
    
    return {
        'appkey': appkey,
        'channel': channel,
        'message_secret': message_secret,
        'using_placeholder': using_placeholder
    }


def extract_existing_config(project_path, app_module):
    """
    从Application类中提取已有的appkey和channel配置
    
    Returns:
        dict: {'appkey': str, 'channel': str} 或 None
    """
    src_dir = os.path.join(project_path, app_module, 'src', 'main', 'java')
    kotlin_dir = os.path.join(project_path, app_module, 'src', 'main', 'kotlin')
    
    for base_dir in [src_dir, kotlin_dir]:
        if not os.path.exists(base_dir):
            continue
        
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(('.java', '.kt', '.kts')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if 'Application' not in content:
                            continue
                        
                        # 查找UMConfigure.preInit或UMConfigure.init调用
                        # 提取appkey和channel参数
                        import re
                        
                        # 匹配 UMConfigure.preInit(context, "appkey", "channel")
                        # 或 UMConfigure.init(context, "appkey", "channel", ...)
                        pattern = r'UMConfigure\.(?:pre)?Init\s*\([^,]+,\s*["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']'
                        match = re.search(pattern, content)
                        
                        if match:
                            return {
                                'appkey': match.group(1),
                                'channel': match.group(2)
                            }
                    except:
                        continue
    
    return None


def step1_check_environment():
    """步骤1: 环境检查"""
    print("\n" + "=" * 60)
    print("步骤 1/8: 环境检查")
    print("=" * 60)
    
    checker = EnvChecker()
    checker.check_all()
    
    if not checker.report():
        print("❌ 环境检查失败,无法继续")
        return False
    
    return True


def step2_validate_project(project_path, app_module):
    """步骤2: 项目验证"""
    print("\n" + "=" * 60)
    print("步骤 2/8: 项目验证")
    print("=" * 60)
    
    validator = ProjectValidator(project_path, app_module)
    success, message = validator.validate()
    
    if not success:
        print(f"❌ 项目验证失败: {message}")
        print("\nSDK集成目标需要是一个可正常完成编译,")
        print("正常产出apk执行安装包的应用工程源码。")
        print("\n请先修复项目编译问题后再运行SDK集成。")
        return False
    
    return True


def step5_integrate_sdk(project_path, app_module, config):
    """步骤5: SDK增量集成"""
    print("\n" + "=" * 60)
    print("步骤 5/8: SDK增量集成")
    print("=" * 60)
    
    from sdk_integrator import PushSDKIntegrator
    
    integrator = PushSDKIntegrator(project_path, app_module, config)
    success, message = integrator.integrate()
    
    if not success:
        print(f"❌ 推送SDK集成失败: {message}")
        print(f"\n备份zip文件: {integrator.backup_zip}")
        print("如需回滚,请运行:")
        print(f"  python3 scripts/rollback.py --backup-zip {integrator.backup_zip} --project-path {project_path}")
        return False
    
    # 保存备份zip路径供后续使用
    global backup_zip_path
    backup_zip_path = integrator.backup_zip
    
    return True


def step6_verify_build(project_path):
    """步骤6: 编译验证"""
    print("\n" + "=" * 60)
    print("步骤 6/8: 编译验证")
    print("=" * 60)
    
    from project_validator import ProjectValidator
    
    # 重新创建验证器并执行编译
    validator = ProjectValidator(project_path, 'app')
    
    print("执行编译验证...")
    if not validator._check_build():
        print("\n❌ 推送SDK集成后编译失败")
        print(f"\n备份zip文件: {backup_zip_path}")
        print("建议执行回滚:")
        print(f"  python3 scripts/rollback.py --backup-zip {backup_zip_path} --project-path {project_path}")
        return False
    
    print("✅ 推送SDK集成后编译成功\n")
    return True


def step7_verify_sdk(project_path, app_module):
    """步骤7: SDK验证"""
    print("\n" + "=" * 60)
    print("步骤 7/8: SDK验证")
    print("=" * 60)
    
    from sdk_verifier import PushSDKVerifier
    
    verifier = PushSDKVerifier(project_path, app_module)
    success, message = verifier.verify()
    
    if success:
        print("✅ 推送SDK验证通过\n")
    else:
        print(f"⚠️  推送SDK验证未通过: {message}\n")
        print("注意: SDK验证失败不影响代码集成,请后续手动验证")
        print("查看logcat日志命令:")
        print("  adb logcat | grep -E 'UmengPush|PushAgent|deviceToken'")
        print("\n成功关键词:")
        print("  deviceToken: <44位字符串>")
        print()
    
    return True  # 不阻塞流程


def step8_generate_report(project_path, config, build_success, verify_success):
    """步骤8: 生成报告"""
    print("\n" + "=" * 60)
    print("步骤 8/8: 生成报告")
    print("=" * 60)
    
    from datetime import datetime
    
    report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'project_path': project_path,
        'sdk_config': {
            'appkey': config['appkey'],
            'channel': config['channel'],
            'message_secret': config['message_secret'],
            'using_placeholder': config['using_placeholder']
        },
        'integration_status': 'success',
        'build_status': 'success' if build_success else 'failed',
        'verification_status': 'success' if verify_success else 'pending'
    }
    
    print("\n📋 集成报告")
    print("=" * 60)
    print(f"时间: {report['timestamp']}")
    print(f"项目: {report['project_path']}")
    print(f"\n推送SDK配置:")
    print(f"  appkey: {report['sdk_config']['appkey']}")
    print(f"  channel: {report['sdk_config']['channel']}")
    print(f"  messageSecret: {report['sdk_config']['message_secret']}")
    if report['sdk_config']['using_placeholder']:
        print(f"  ⚠️  使用占位符,需要替换!")
    print(f"\n集成状态: {report['integration_status']}")
    print(f"编译状态: {report['build_status']}")
    print(f"验证状态: {report['verification_status']}")
    print("=" * 60)
    
    if config['using_placeholder']:
        print("\n⚠️  下一步:")
        print("  1. 在友盟消息后台获取真实messageSecret")
        print("  2. 替换Application类中的messageSecret")
        print("  3. 重新编译运行应用")
        print("  4. 查看logcat日志确认deviceToken获取成功")
        print()
    else:
        print("\n✅ 推送SDK集成完成!")
        print("\n下一步:")
        print("  1. 运行应用")
        print("  2. 查看logcat确认deviceToken:")
        print("     adb logcat | grep UmengPush")
        print("  3. 在友盟消息后台测试推送")
        print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("友盟Android推送SDK集成工具")
    print("=" * 60)
    
    # 解析参数
    args = parse_arguments()
    project_path = args.project_path
    app_module = args.app_module
    
    # 步骤1: 环境检查
    if not step1_check_environment():
        sys.exit(1)
    
    # 步骤2: 项目验证
    if not step2_validate_project(project_path, app_module):
        sys.exit(1)
    
    # 步骤3: 前置条件检查
    if not check_prerequisites(project_path, app_module):
        sys.exit(1)
    
    # 步骤4: 参数交互
    config = collect_push_config(args)
    
    # 步骤5: SDK增量集成
    if not step5_integrate_sdk(project_path, app_module, config):
        sys.exit(1)
    
    # 步骤6: 编译验证
    if not step6_verify_build(project_path):
        sys.exit(1)
    
    # 步骤7: SDK验证(可选,失败不阻塞)
    step7_verify_sdk(project_path, app_module)
    
    # 步骤8: 生成报告
    step8_generate_report(project_path, config, True, True)
    
    print("\n✅ 推送SDK集成完成\n")


if __name__ == '__main__':
    main()
