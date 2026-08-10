#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
友盟Android APM SDK集成工具
主工作流编排（9步）
"""

import os
import sys
import argparse
from datetime import datetime

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_checker import EnvChecker
from project_validator import ProjectValidator
from plugin_configurator import GradlePluginConfigurator
from sdk_integrator import APMSDKIntegrator

# 全局变量
backup_zip_path = None
modified_files = []


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='友盟Android APM SDK集成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互模式
  python main.py --project-path /path/to/android/project
  
  # 非交互模式
  python main.py --project-path /path/to/project --non-interactive
  
  # 指定app模块
  python main.py --project-path /path/to/project --app-module myapp
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
        '--non-interactive',
        action='store_true',
        help='跳过确认提示直接集成'
    )
    
    return parser.parse_args()


def extract_existing_config(project_path, app_module):
    """
    从Application类中提取已有的appkey和channel配置
    
    Returns:
        dict: {'appkey': str, 'channel': str} 或 None
    """
    import re
    
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
                        pattern = r'UMConfigure\.(?:pre)?[Ii]nit\s*\([^,]+,\s*["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']'
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
    """步骤1: 🔍 环境检查"""
    print("\n" + "=" * 60)
    print("步骤 1/9: 🔍 环境检查")
    print("=" * 60)
    
    checker = EnvChecker()
    checker.check_all()
    
    if not checker.report():
        print("❌ 环境检查失败,无法继续")
        return False
    
    return True


def step2_validate_project(project_path, app_module):
    """步骤2: 📂 项目验证"""
    print("\n" + "=" * 60)
    print("步骤 2/9: 📂 项目验证")
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


def step3_check_prerequisites(project_path, app_module):
    """
    步骤3: 📋 前置条件检查 - 验证统计SDK已集成
    
    Returns:
        dict: {'appkey': str, 'channel': str} 或 None(检查失败时)
    """
    print("\n" + "=" * 60)
    print("步骤 3/9: 📋 前置条件检查")
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
        return None
    
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
        print("\nAPM SDK强依赖统计基础组件,请先运行统计SDK集成:")
        print(f"  python /path/to/umeng-analytics-integration/scripts/main.py --project-path {project_path}")
        return None
    
    if not has_asms:
        print("❌ 未检测到统计SDK依赖: com.umeng.umsdk:asms")
        print("\nAPM SDK强依赖统计基础组件,请先运行统计SDK集成:")
        print(f"  python /path/to/umeng-analytics-integration/scripts/main.py --project-path {project_path}")
        return None
    
    print("✅ 检测到统计SDK依赖: common, asms")
    
    # 2. 检查Application类中是否有UMConfigure.init()调用
    src_dir = os.path.join(project_path, app_module, 'src', 'main', 'java')
    kotlin_dir = os.path.join(project_path, app_module, 'src', 'main', 'kotlin')
    
    app_class_found = False
    has_umeng_init = False
    
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
                        
                        if 'Application' in content and ('extends Application' in content or ': Application()' in content):
                            app_class_found = True
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
        return None
    
    if not has_umeng_init:
        print("❌ Application类中未检测到UMConfigure.init()调用")
        print("\n请先运行统计SDK集成,完成SDK初始化:")
        print(f"  python /path/to/umeng-analytics-integration/scripts/main.py --project-path {project_path}")
        return None
    
    # 3. 从Application中提取已有的appkey和channel
    config = extract_existing_config(project_path, app_module)
    if config:
        print(f"✅ 从项目中提取到: appkey={config['appkey']}, channel={config['channel']}")
    else:
        print("⚠️  未能从项目中提取appkey/channel,将使用占位符")
        config = {'appkey': 'YOUR_APPKEY', 'channel': 'YOUR_CHANNEL'}
    
    print("\n✅ 前置条件检查通过: 统计SDK已集成\n")
    return config


def step4_create_backup(project_path, app_module, config):
    """步骤4: 💾 创建备份"""
    print("\n" + "=" * 60)
    print("步骤 4/9: 💾 创建备份")
    print("=" * 60)
    
    global backup_zip_path
    
    # 使用APMSDKIntegrator创建备份（内部会创建zip）
    integrator = APMSDKIntegrator(project_path, app_module, config)
    integrator._create_backup_zip()
    backup_zip_path = integrator.backup_zip
    
    return integrator


def step5_configure_gradle_plugins(project_path, app_module):
    """步骤5: 🔌 Gradle插件配置"""
    print("\n" + "=" * 60)
    print("步骤 5/9: 🔌 Gradle插件配置")
    print("=" * 60)
    
    global modified_files
    
    configurator = GradlePluginConfigurator(project_path, app_module)
    
    # 提取包名用于efs whiteList
    import re
    package_name = ""
    manifest_path = os.path.join(project_path, app_module, 'src', 'main', 'AndroidManifest.xml')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'package\s*=\s*"([^"]+)"', content)
        if match:
            package_name = match.group(1)
    
    success, message = configurator.configure_all(package_name)
    
    if not success:
        print(f"❌ Gradle插件配置失败: {message}")
        return False
    
    # 记录修改的文件
    root_gradle_kts = os.path.join(project_path, 'build.gradle.kts')
    root_gradle_groovy = os.path.join(project_path, 'build.gradle')
    if os.path.exists(root_gradle_kts):
        modified_files.append(os.path.relpath(root_gradle_kts, project_path))
    elif os.path.exists(root_gradle_groovy):
        modified_files.append(os.path.relpath(root_gradle_groovy, project_path))
    
    app_gradle_kts = os.path.join(project_path, app_module, 'build.gradle.kts')
    app_gradle_groovy = os.path.join(project_path, app_module, 'build.gradle')
    if os.path.exists(app_gradle_kts):
        modified_files.append(os.path.relpath(app_gradle_kts, project_path))
    elif os.path.exists(app_gradle_groovy):
        modified_files.append(os.path.relpath(app_gradle_groovy, project_path))
    
    return True


def step6_integrate_sdk(integrator):
    """步骤6: 📦 SDK增量集成"""
    print("\n" + "=" * 60)
    print("步骤 6/9: 📦 SDK增量集成")
    print("=" * 60)
    
    global modified_files
    
    success, message = integrator.integrate()
    
    if not success:
        print(f"❌ APM SDK集成失败: {message}")
        print(f"\n备份zip文件: {integrator.backup_zip}")
        print("如需回滚,请运行:")
        print(f"  python3 scripts/rollback.py --backup-zip {integrator.backup_zip} --project-path {integrator.project_path}")
        return False
    
    # 记录修改的文件
    manifest_path = os.path.join(integrator.project_path, integrator.app_module, 'src', 'main', 'AndroidManifest.xml')
    proguard_path = os.path.join(integrator.project_path, integrator.app_module, 'proguard-rules.pro')
    
    if os.path.exists(manifest_path):
        rel_path = os.path.relpath(manifest_path, integrator.project_path)
        if rel_path not in modified_files:
            modified_files.append(rel_path)
    
    if os.path.exists(proguard_path):
        rel_path = os.path.relpath(proguard_path, integrator.project_path)
        if rel_path not in modified_files:
            modified_files.append(rel_path)
    
    # 查找并记录Application类文件
    app_file = integrator._find_application_file()
    if app_file:
        rel_path = os.path.relpath(app_file, integrator.project_path)
        if rel_path not in modified_files:
            modified_files.append(rel_path)
    
    return True


def step7_confirm_integration(args, integrator):
    """步骤7: ✅ 集成确认 - 展示变更摘要供用户确认"""
    print("\n" + "=" * 60)
    print("步骤 7/9: ✅ 集成确认")
    print("=" * 60)
    
    print("\n以下文件已被修改：")
    for f in modified_files:
        print(f"  📝 {f}")
    
    print(f"\n备份文件: {backup_zip_path}")
    
    if not args.non_interactive:
        confirm = input("\n确认继续编译验证？(y/n): ")
        if confirm.lower() != 'y':
            print("\n用户取消，开始回滚...")
            integrator.restore_from_backup()
            sys.exit(0)
    else:
        print("\n(非交互模式，自动继续)")
    
    return True


def step8_verify_build(project_path):
    """步骤8: 🔨 编译验证"""
    print("\n" + "=" * 60)
    print("步骤 8/9: 🔨 编译验证")
    print("=" * 60)
    
    validator = ProjectValidator(project_path, 'app')
    
    print("\n执行编译验证...")
    if not validator._check_build():
        print("\n❌ APM SDK集成后编译失败")
        print(f"\n备份zip文件: {backup_zip_path}")
        print("建议执行回滚:")
        print(f"  python3 scripts/rollback.py --backup-zip {backup_zip_path} --project-path {project_path}")
        
        return False
    
    print("✅ APM SDK集成后编译成功\n")
    return True


def step9_verify_sdk(project_path, app_module):
    """步骤9: 📱 SDK验证"""
    print("\n" + "=" * 60)
    print("步骤 9/9: 📱 SDK验证")
    print("=" * 60)
    
    from sdk_verifier import APMSDKVerifier
    
    verifier = APMSDKVerifier(project_path, app_module)
    success, message = verifier.verify()
    
    if success:
        print("✅ APM SDK验证通过\n")
    else:
        print(f"⚠️  APM SDK验证未通过: {message}\n")
        print("注意: SDK验证失败不影响代码集成,请后续手动验证")
        print("查看logcat日志命令:")
        print('  adb logcat | grep "UMCrash"')
        print("\n成功关键词:")
        print("  可接入免费的网络分析能力")
        print()
    
    return True  # 不阻塞流程


def generate_report(project_path, config, build_success):
    """生成集成报告"""
    print("\n" + "=" * 60)
    print("📋 集成报告")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    using_placeholder = config.get('appkey', '') == 'YOUR_APPKEY'
    
    print(f"\n时间: {timestamp}")
    print(f"项目: {project_path}")
    print(f"\nAPM SDK配置:")
    print(f"  appkey: {config.get('appkey', 'N/A')}")
    print(f"  channel: {config.get('channel', 'N/A')}")
    if using_placeholder:
        print(f"  ⚠️  使用占位符,需要替换!")
    print(f"\n修改的文件:")
    for f in modified_files:
        print(f"  📝 {f}")
    print(f"\n编译状态: {'成功' if build_success else '失败'}")
    print(f"备份文件: {backup_zip_path}")
    print("=" * 60)
    
    print("\n✅ APM SDK集成完成!")
    print("\n下一步:")
    print("  1. 运行应用")
    print("  2. 查看logcat确认APM初始化:")
    print('     adb logcat | grep "UMCrash"')
    print("  3. 在友盟U-APM后台查看数据上报")
    print()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("友盟Android APM SDK集成工具")
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
    
    # 步骤3: 前置条件检查（验证统计SDK已集成,并提取appkey/channel）
    config = step3_check_prerequisites(project_path, app_module)
    if config is None:
        sys.exit(1)
    
    # 步骤4: 创建备份
    integrator = step4_create_backup(project_path, app_module, config)
    
    # 步骤5: Gradle插件配置
    if not step5_configure_gradle_plugins(project_path, app_module):
        sys.exit(1)
    
    # 步骤6: SDK增量集成
    if not step6_integrate_sdk(integrator):
        sys.exit(1)
    
    # 步骤7: 集成确认
    if not step7_confirm_integration(args, integrator):
        sys.exit(1)
    
    # 步骤8: 编译验证
    build_success = step8_verify_build(project_path)
    if not build_success:
        sys.exit(1)
    
    # 步骤9: SDK验证（可选,失败不阻塞）
    step9_verify_sdk(project_path, app_module)
    
    # 生成报告
    generate_report(project_path, config, build_success)


if __name__ == '__main__':
    main()
