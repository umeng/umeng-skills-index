# -*- coding: utf-8 -*-
"""
Flutter统计SDK集成 - 项目验证模块
验证Flutter项目结构、检测项目类型、编译验证
"""

import os
import re
import subprocess
import sys


class ProjectValidator:
    """Flutter项目验证器"""
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.project_info = {
            'has_pubspec': False,
            'has_android': False,
            'has_ios': False,
            'has_lib': False,
            'has_main_dart': False,
            'project_name': None,
            'android_namespace': None,
            'android_min_sdk': None,
            'ios_deployment_target': None,
            'ios_language': None,
            'uses_kotlin': True,  # 默认假设Kotlin
            'existing_umeng_sdk': False,
            'uses_spm': False,       # iOS 工程是否启用 Swift Package Manager
            'podfile_missing': False # ios/ 存在但无 Podfile（非 SPM 确认场景）
        }
    
    def validate(self):
        """执行项目验证"""
        print("\n" + "="*60)
        print("📋 开始项目验证...")
        print("="*60 + "\n")
        
        # 步骤1: 检查pubspec.yaml
        if not self._check_pubspec():
            return False
        
        # 步骤2: 检查Android目录
        if not self._check_android():
            return False
        
        # 步骤3: 检查iOS目录
        if not self._check_ios():
            return False
        
        # 步骤4: 检查lib目录
        if not self._check_lib():
            return False
        
        # 打印项目信息
        self._print_project_info()
        
        return True
    
    def build_project(self, build_timeout=1800):
        """编译项目验证
        
        Args:
            build_timeout: 编译超时时间(秒)，默认1800秒(30分钟)
        """
        print("\n" + "="*60)
        print("🏗️ 开始编译验证...")
        print("="*60 + "\n")
        
        timeout_min = build_timeout // 60
        
        # 尝试构建APK（Android）
        print("📦 构建Android APK...")
        print("  这可能需要几分钟，请耐心等待（超时: {}分钟）...\n".format(timeout_min))
        
        try:
            result = subprocess.run(
                ['flutter', 'build', 'apk', '--debug'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=build_timeout
            )
            
            # 构建日志落盘（无论成功失败）
            self._save_build_log('Android', result.stdout, result.stderr)
            
            if result.returncode == 0:
                print("  ✅ Android 构建成功\n")
            else:
                print("  ❌ Android 构建失败")
                print("\n错误信息:")
                # 只显示最后50行错误
                lines = (result.stderr or result.stdout).split('\n')
                for line in lines[-50:]:
                    if line.strip():
                        print("    {}".format(line))
                
                # 提供针对性的解决建议
                print("\n💡 可能的原因和解决建议:")
                self._print_build_error_hints(result.stderr + result.stdout)
                print("  📋 完整构建日志已保存至 build/umeng_integration_build.log")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ❌ 构建超时（超过{}分钟）".format(timeout_min))
            print("  💡 可通过 --timeout 参数增大超时时间")
            return False
        except Exception as e:
            print("  ❌ 构建过程出错: {}".format(str(e)))
            return False
        
        # iOS 编译验证（仅 macOS 下且项目包含 ios 目录）
        import platform
        if self.project_info.get('has_ios') and platform.system() == 'Darwin':
            print("  📱 正在编译 iOS 项目...")
            try:
                result = subprocess.run(
                    ['flutter', 'build', 'ios', '--debug', '--no-codesign'],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=build_timeout
                )
                # 构建日志落盘（无论成功失败）
                self._save_build_log('iOS', result.stdout, result.stderr)
                if result.returncode != 0:
                    print("  ❌ iOS 编译失败")
                    lines = (result.stderr or result.stdout).split('\n')
                    for line in lines[-30:]:
                        if line.strip():
                            print("    {}".format(line))
                    print("  📋 完整构建日志已保存至 build/umeng_integration_build.log")
                    return False
                print("  ✅ iOS 编译成功")
            except subprocess.TimeoutExpired:
                print("  ❌ iOS 构建超时（超过{}分钟）".format(timeout_min))
                print("  💡 可通过 --timeout 参数增大超时时间")
                return False
            except Exception as e:
                print("  ❌ iOS 构建出错: {}".format(str(e)))
                return False
        
        return True
    
    def _save_build_log(self, platform_name, stdout, stderr):
        """将构建日志完整写入 {project_path}/build/umeng_integration_build.log"""
        try:
            build_dir = os.path.join(self.project_path, 'build')
            if not os.path.exists(build_dir):
                os.makedirs(build_dir)
            log_path = os.path.join(build_dir, 'umeng_integration_build.log')
            log_content = (
                "=" * 60 + "\n"
                "[{}] 构建日志\n".format(platform_name)
                + "=" * 60 + "\n\n"
                "----- STDOUT -----\n" + (stdout or "") + "\n\n"
                "----- STDERR -----\n" + (stderr or "") + "\n"
            )
            # 追加写入：Android 与 iOS 日志均保留
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(log_content)
        except Exception as e:
            print("  ⚠️  构建日志保存失败: {}".format(str(e)))
    
    def _check_pubspec(self):
        """检查pubspec.yaml"""
        print("🔍 检查 pubspec.yaml...")
        
        pubspec_path = os.path.join(self.project_path, 'pubspec.yaml')
        
        if not os.path.exists(pubspec_path):
            print("  ❌ 未找到 pubspec.yaml")
            print("     这不是一个有效的Flutter项目")
            return False
        
        self.project_info['has_pubspec'] = True
        
        with open(pubspec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析项目名称
        name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
        if name_match:
            self.project_info['project_name'] = name_match.group(1).strip()
            print("  ✅ 项目名称: {}".format(self.project_info['project_name']))
        
        # 检查是否已有友盟SDK依赖
        if 'umeng_common_sdk' in content:
            self.project_info['existing_umeng_sdk'] = True
            print("  ⚠️  pubspec.yaml 已包含 umeng_common_sdk 依赖")
        
        # 检查flutter依赖
        if 'flutter:' in content and 'sdk: flutter' in content:
            print("  ✅ Flutter依赖配置正确")
        else:
            print("  ⚠️  pubspec.yaml 可能缺少Flutter SDK依赖")
        
        return True
    
    def _check_android(self):
        """检查Android目录"""
        print("\n🔍 检查 Android 目录...")
        
        android_dir = os.path.join(self.project_path, 'android')
        
        if not os.path.exists(android_dir):
            print("  ❌ 未找到 android/ 目录")
            print("     这可能不是一个完整的Flutter项目")
            return False
        
        self.project_info['has_android'] = True
        print("  ✅ android/ 目录存在")
        
        # 检查build.gradle
        build_gradle = os.path.join(android_dir, 'app', 'build.gradle')
        build_gradle_kts = os.path.join(android_dir, 'app', 'build.gradle.kts')
        
        gradle_file = None
        if os.path.exists(build_gradle_kts):
            gradle_file = build_gradle_kts
            print("  ✅ 使用 Kotlin DSL (build.gradle.kts)")
        elif os.path.exists(build_gradle):
            gradle_file = build_gradle
            print("  ✅ 使用 Groovy DSL (build.gradle)")
        
        if gradle_file:
            with open(gradle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取namespace
            namespace_match = re.search(r'namespace\s*=?\s*["\']([^"\']+)["\']', content)
            if namespace_match:
                self.project_info['android_namespace'] = namespace_match.group(1)
                print("  ✅ Namespace: {}".format(self.project_info['android_namespace']))
            
            # 提取minSdkVersion
            min_sdk_match = re.search(r'minSdkVersion\s*[:=]?\s*(\d+)', content)
            if min_sdk_match:
                self.project_info['android_min_sdk'] = int(min_sdk_match.group(1))
                if self.project_info['android_min_sdk'] >= 21:
                    print("  ✅ minSdkVersion: {} (>= 21)".format(self.project_info['android_min_sdk']))
                else:
                    print("  ❌ minSdkVersion: {} (友盟 SDK 要求 >= 21，请修改 android/app/build.gradle)".format(self.project_info['android_min_sdk']))
                    return False
        
        # 检查是否使用Kotlin
        kotlin_dir = os.path.join(android_dir, 'app', 'src', 'main', 'kotlin')
        java_dir = os.path.join(android_dir, 'app', 'src', 'main', 'java')
        
        if os.path.exists(kotlin_dir):
            self.project_info['uses_kotlin'] = True
            print("  ✅ 使用 Kotlin")
        elif os.path.exists(java_dir):
            self.project_info['uses_kotlin'] = False
            print("  ✅ 使用 Java")
        
        # 检查AndroidManifest.xml
        manifest_path = os.path.join(android_dir, 'app', 'src', 'main', 'AndroidManifest.xml')
        if os.path.exists(manifest_path):
            print("  ✅ AndroidManifest.xml 存在")
            
            # 如果没有namespace，尝试从Manifest中获取package
            if not self.project_info['android_namespace']:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest_content = f.read()
                package_match = re.search(r'package="([^"]+)"', manifest_content)
                if package_match:
                    self.project_info['android_namespace'] = package_match.group(1)
                    print("  ✅ Package: {}".format(self.project_info['android_namespace']))
        
        return True
    
    def _check_ios(self):
        """检查iOS目录"""
        print("\n🔍 检查 iOS 目录...")
        
        ios_dir = os.path.join(self.project_path, 'ios')
        
        if not os.path.exists(ios_dir):
            print("  ⚠️  未找到 ios/ 目录")
            print("     iOS 集成将被跳过")
            self.project_info['has_ios'] = False
            return True  # iOS不是必需的
        
        self.project_info['has_ios'] = True
        print("  ✅ ios/ 目录存在")
        
        # 检查Podfile
        podfile_path = os.path.join(ios_dir, 'Podfile')
        if os.path.exists(podfile_path):
            print("  ✅ Podfile 存在")
            
            with open(podfile_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取iOS部署目标
            platform_match = re.search(r"platform\s+:ios,\s*['\"]?(\d+\.?\d*)['\"]?", content)
            if platform_match:
                self.project_info['ios_deployment_target'] = platform_match.group(1)
                print("  ✅ iOS Deployment Target: {}".format(self.project_info['ios_deployment_target']))
        
        # 检查Runner目录
        runner_dir = os.path.join(ios_dir, 'Runner')
        if os.path.exists(runner_dir):
            print("  ✅ Runner/ 目录存在")
        
        # 检测iOS语言类型（Swift / Objective-C）
        swift_app = os.path.join(ios_dir, 'Runner', 'AppDelegate.swift')
        objc_app = os.path.join(ios_dir, 'Runner', 'AppDelegate.m')
        if os.path.exists(swift_app):
            self.project_info['ios_language'] = 'swift'
            print("  ✅ iOS 语言: Swift")
        elif os.path.exists(objc_app):
            self.project_info['ios_language'] = 'objc'
            print("  ✅ iOS 语言: Objective-C")
        else:
            self.project_info['ios_language'] = 'unknown'
            print("  ⚠️ iOS 语言: 未检测到 AppDelegate")
        
        # SPM 前置检测（Flutter 3.44+ 新建工程默认启用 SPM，友盟插件不支持）
        if not self._check_spm(ios_dir):
            return False
        
        return True
    
    def _check_spm(self, ios_dir):
        """检测 iOS 工程是否启用 Swift Package Manager（SPM）
        
        友盟 Flutter SDK 当前不支持 SPM，SPM 工程无 Podfile，
        pod install 会被跳过导致 iOS 原生依赖缺失。
        双档策略（避免误杀 Flutter Module / 未 build 的 CocoaPods 工程）：
        - pbxproj 含 FlutterGeneratedPluginSwiftPackage 标记 → 确认 SPM，硬失败并给出迁移步骤
        - 仅无 Podfile 且无 SPM 标记 → 强警告不阻塞（可能是尚未执行 flutter build ios 的工程）
        
        注意：本方法与 umeng-flutter-apm-integration/project_validator.py 为镜像实现，
        修改时需同步另一处。
        
        Returns:
            bool: False 表示确认 SPM 工程，应阻塞集成
        """
        # 信号1（确定性）：pbxproj 含 Flutter 生成的 SPM 包引用
        pbxproj_path = os.path.join(ios_dir, 'Runner.xcodeproj', 'project.pbxproj')
        uses_spm = False
        if os.path.exists(pbxproj_path):
            try:
                with open(pbxproj_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if 'FlutterGeneratedPluginSwiftPackage' in f.read():
                        uses_spm = True
            except Exception as e:
                print("  ⚠️  读取 project.pbxproj 失败: {}".format(e))
        
        podfile_path = os.path.join(ios_dir, 'Podfile')
        has_podfile = os.path.exists(podfile_path)
        
        if uses_spm:
            self.project_info['uses_spm'] = True
            print("  ❌ 检测到 SPM（Swift Package Manager）工程，友盟 Flutter SDK 当前不支持 SPM")
            self._print_spm_migration_guide()
            return False
        
        if not has_podfile:
            # 无 SPM 标记但缺 Podfile：可能是尚未执行 flutter build ios 的工程，仅警告不阻塞
            self.project_info['podfile_missing'] = True
            print("  ⚠️  ios/ 目录存在但未找到 Podfile，pod install 将被跳过，iOS 原生依赖可能缺失")
            print("     若为 CocoaPods 工程请先执行 flutter build ios 生成 Podfile；若为 SPM 工程请参考文档「SPM → CocoaPods 迁移」章节")
        
        return True
    
    def _print_spm_migration_guide(self):
        """打印 SPM → CocoaPods 迁移步骤"""
        print("\n💡 SPM → CocoaPods 迁移步骤（详见文档「SPM → CocoaPods 迁移」章节）:")
        print("  1. 关闭 Flutter 的 SPM 支持: flutter config --no-enable-swift-package-manager")
        print("  2. 重生成 ios/ 目录（备份后删除再执行，注意管道方式防签名证书交互卡死）:")
        print("     printf '1\\n' | flutter create --platforms=ios . < /dev/null")
        print("     或手工移除 pbxproj 中的 FlutterGeneratedPluginSwiftPackage 引用")
        print("  3. 确认 ios/Podfile 存在且 platform :ios, '13.0' 一行已取消注释")
        print("  4. 在 ios/Flutter/Debug.xcconfig 与 Release.xcconfig 首行分别添加:")
        print("     #include? \"Pods/Target Support Files/Pods-Runner/Pods-Runner.debug.xcconfig\"")
        print("     #include? \"Pods/Target Support Files/Pods-Runner/Pods-Runner.release.xcconfig\"")
        print("  5. 迁移完成后重新运行本集成脚本\n")
    
    def _check_lib(self):
        """检查lib目录"""
        print("\n🔍 检查 lib 目录...")
        
        lib_dir = os.path.join(self.project_path, 'lib')
        
        if not os.path.exists(lib_dir):
            print("  ❌ 未找到 lib/ 目录")
            return False
        
        self.project_info['has_lib'] = True
        print("  ✅ lib/ 目录存在")
        
        # 检查main.dart
        main_dart = os.path.join(lib_dir, 'main.dart')
        if os.path.exists(main_dart):
            self.project_info['has_main_dart'] = True
            print("  ✅ main.dart 存在")
        else:
            print("  ⚠️  未找到 main.dart")
        
        return True
    
    def _print_project_info(self):
        """打印项目信息"""
        print("\n" + "-" * 60)
        print("📋 项目信息")
        print("-" * 60)
        print("  项目名称: {}".format(self.project_info['project_name'] or 'unknown'))
        print("  Android:  ✅ 就绪")
        print("  iOS:      {}".format('✅ 就绪' if self.project_info['has_ios'] else '⚠️  未检测到'))
        print("  Namespace: {}".format(self.project_info['android_namespace'] or '未检测到'))
        
        if self.project_info['android_min_sdk']:
            print("  minSdk:   {}".format(self.project_info['android_min_sdk']))
        
        if self.project_info['ios_deployment_target']:
            print("  iOS Target: {}".format(self.project_info['ios_deployment_target']))
        
        if self.project_info.get('ios_language'):
            lang_display = {'swift': 'Swift', 'objc': 'Objective-C', 'unknown': '未检测到'}
            print("  iOS 语言: {}".format(lang_display.get(self.project_info['ios_language'], '未知')))
        
        if self.project_info['existing_umeng_sdk']:
            print("  友盟SDK:  ⚠️  已存在（将检查是否需要更新）")
        
        print("-" * 60)
    
    def _print_build_error_hints(self, error_output):
        """打印构建错误的针对性建议"""
        error_lower = error_output.lower()
        
        if 'duplicate class' in error_lower:
            print("\n  🔍 检测到 'duplicate class' 错误:")
            print("  1. 检查是否同时创建了 MyApplication.kt 和 MyApplication.java")
            print("  2. 只能保留一个，删除另一个")
            print("  3. 执行 flutter clean 后重新构建")
        
        elif 'namespace' in error_lower:
            print("\n  🔍 检测到 namespace 相关错误:")
            print("  1. 检查 android/app/build.gradle 中的 namespace 配置")
            print("  2. AGP 7.0+ 需要在 build.gradle 中声明 namespace")
        
        elif 'minSdkVersion' in error_lower:
            print("\n  🔍 检测到 minSdkVersion 错误:")
            print("  1. 友盟SDK要求 minSdkVersion >= 21")
            print("  2. 修改 android/app/build.gradle 中的 minSdkVersion")
        
        else:
            print("\n  📝 通用解决建议:")
            print("  1. 执行 flutter doctor 检查环境")
            print("  2. 执行 flutter clean 清理缓存")
            print("  3. 检查错误详情并修复")
            print("  4. 重新编译验证")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python project_validator.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    validator = ProjectValidator(project_path)
    
    if validator.validate():
        print("\n✅ 项目验证通过")
    else:
        print("\n❌ 项目验证失败")
        sys.exit(1)
