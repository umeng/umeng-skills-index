# -*- coding: utf-8 -*-
"""
Flutter APM SDK集成 - 环境检测模块
检测Flutter SDK、Dart SDK、Android SDK、CocoaPods等必需工具
"""

import platform
import re
import shutil
import subprocess
import sys
import os


class EnvChecker:
    """环境检测器"""
    
    def __init__(self, project_path=None):
        self.project_path = project_path
        self.results = []
        self.all_passed = True
    
    def check_all(self):
        """执行所有环境检查"""
        print("\n" + "="*60)
        print("🔍 开始环境检查...")
        print("="*60 + "\n")
        
        self._check_flutter()
        self._check_dart()
        self._check_android_sdk()
        
        # CocoaPods和Xcode仅在macOS上检查
        if platform.system() == 'Darwin':
            self._check_cocoapods()
            self._check_xcode()
        
        # Gradle兼容性检查（需要项目路径）
        if self.project_path:
            self._check_gradle_compatibility()
        
        self._print_report()
        
        return self.all_passed
    
    def _check_flutter(self):
        """检测Flutter SDK"""
        try:
            result = subprocess.run(
                ['flutter', '--version'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                version_str = self._extract_version(version_line)
                
                if version_str != 'unknown' and not self._version_gte(version_str, '2.0.0'):
                    self._add_result(
                        'Flutter SDK',
                        False,
                        '❌ Flutter {} 版本过低 (要求 >= 2.0.0)'.format(version_str),
                        'critical',
                        '请升级Flutter SDK:\n'
                        '  flutter upgrade'
                    )
                else:
                    self._add_result(
                        'Flutter SDK',
                        True,
                        '✅ {} (>= 2.0.0)'.format(version_line.strip()),
                        'critical',
                        ''
                    )
            else:
                self._add_result(
                    'Flutter SDK',
                    False,
                    '❌ 未安装或版本过低',
                    'critical',
                    '安装方法:\n'
                    '  1. 访问 https://flutter.dev/docs/get-started/install\n'
                    '  2. 下载并解压Flutter SDK\n'
                    '  3. 添加flutter到PATH环境变量'
                )
        except FileNotFoundError:
            self._add_result(
                'Flutter SDK',
                False,
                '❌ flutter命令不存在',
                'critical',
                '安装方法:\n'
                '  1. 访问 https://flutter.dev/docs/get-started/install\n'
                '  2. 下载并解压Flutter SDK\n'
                '  3. 添加flutter到PATH环境变量'
            )
        except Exception as e:
            self._add_result(
                'Flutter SDK',
                False,
                '❌ 检测失败: {}'.format(str(e)),
                'critical',
                '请手动检查Flutter是否正确安装'
            )
    
    def _check_dart(self):
        """检测Dart SDK"""
        try:
            result = subprocess.run(
                ['dart', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip() or result.stderr.strip()
                version_str = self._extract_version(version)
                
                if version_str != 'unknown' and not self._version_gte(version_str, '2.12.0'):
                    self._add_result(
                        'Dart SDK',
                        False,
                        '❌ Dart {} 版本过低 (要求 >= 2.12.0 空安全)'.format(version_str),
                        'critical',
                        '请升级Flutter SDK以获取更高版本的Dart:\n'
                        '  flutter upgrade'
                    )
                else:
                    self._add_result(
                        'Dart SDK',
                        True,
                        '✅ {} (>= 2.12.0 空安全)'.format(version),
                        'critical',
                        ''
                    )
            else:
                self._add_result(
                    'Dart SDK',
                    False,
                    '❌ 未安装或版本过低',
                    'critical',
                    'Dart SDK通常随Flutter SDK一起安装\n'
                    '请确保Flutter SDK版本 >= 2.0.0'
                )
        except FileNotFoundError:
            self._add_result(
                'Dart SDK',
                False,
                '❌ dart命令不存在',
                'critical',
                'Dart SDK通常随Flutter SDK一起安装\n'
                '请确保Flutter SDK版本 >= 2.0.0'
            )
        except Exception as e:
            self._add_result(
                'Dart SDK',
                False,
                '❌ 检测失败: {}'.format(str(e)),
                'critical',
                '请手动检查Dart是否正确安装'
            )
    
    def _check_android_sdk(self):
        """检测Android SDK"""
        android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        
        if android_home and os.path.exists(android_home):
            self._add_result(
                'Android SDK',
                True,
                '✅ 已配置 ({})'.format(android_home),
                'critical',
                ''
            )
        else:
            try:
                result = subprocess.run(
                    ['adb', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self._add_result(
                        'Android SDK',
                        True,
                        '✅ adb可用 (Android SDK已安装)',
                        'critical',
                        ''
                    )
                else:
                    self._add_result(
                        'Android SDK',
                        False,
                        '❌ 未配置ANDROID_HOME且adb不可用',
                        'critical',
                        '安装方法:\n'
                        '  1. 安装Android Studio\n'
                        '  2. 设置ANDROID_HOME环境变量\n'
                        '  3. macOS: export ANDROID_HOME=$HOME/Library/Android/sdk\n'
                        '  4. Linux: export ANDROID_HOME=$HOME/Android/Sdk'
                    )
            except FileNotFoundError:
                self._add_result(
                    'Android SDK',
                    False,
                    '❌ 未检测到Android SDK',
                    'critical',
                    '安装方法:\n'
                    '  1. 安装Android Studio\n'
                    '  2. 设置ANDROID_HOME环境变量\n'
                    '  3. macOS: export ANDROID_HOME=$HOME/Library/Android/sdk\n'
                    '  4. Linux: export ANDROID_HOME=$HOME/Android/Sdk'
                )
            except Exception as e:
                self._add_result(
                    'Android SDK',
                    False,
                    '❌ 检测失败: {}'.format(str(e)),
                    'critical',
                    '请手动检查Android SDK是否正确安装'
                )
    
    def _check_cocoapods(self):
        """检测CocoaPods（仅macOS）"""
        try:
            result = subprocess.run(
                ['pod', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self._add_result(
                    'CocoaPods',
                    True,
                    '✅ 版本 {} (>= 1.10)'.format(version),
                    'critical',
                    ''
                )
            else:
                self._add_result(
                    'CocoaPods',
                    False,
                    '❌ 未安装',
                    'critical',
                    '安装方法:\n'
                    '  方法1: sudo gem install cocoapods\n'
                    '  方法2: brew install cocoapods'
                )
        except FileNotFoundError:
            self._add_result(
                'CocoaPods',
                False,
                '❌ pod命令不存在',
                'critical',
                '安装方法:\n'
                '  方法1: sudo gem install cocoapods\n'
                '  方法2: brew install cocoapods'
            )
        except Exception as e:
            self._add_result(
                'CocoaPods',
                False,
                '❌ 检测失败: {}'.format(str(e)),
                'critical',
                '请手动检查CocoaPods是否正确安装'
            )
    
    def _check_xcode(self):
        """检测Xcode（仅macOS，warning级别：用户可能只做Android集成）"""
        if not shutil.which('xcodebuild'):
            self._add_result(
                'Xcode',
                False,
                '❌ 未安装 Xcode (xcodebuild 不可用)',
                'warning',
                '安装方法:\n'
                '  1. 从 Mac App Store 安装 Xcode\n'
                '  2. 或安装命令行工具: xcode-select --install'
            )
            return
        
        try:
            result = subprocess.run(
                ['xcodebuild', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0].strip()
                self._add_result(
                    'Xcode',
                    True,
                    '✅ {}'.format(version_line),
                    'warning',
                    ''
                )
            else:
                self._add_result(
                    'Xcode',
                    False,
                    '❌ xcodebuild 执行失败',
                    'warning',
                    '请确认 Xcode 已正确安装并接受许可协议:\n'
                    '  sudo xcodebuild -license accept'
                )
        except Exception as e:
            self._add_result(
                'Xcode',
                False,
                '❌ 检测失败: {}'.format(str(e)),
                'warning',
                '请手动检查Xcode是否正确安装'
            )
    
    def _check_gradle_compatibility(self):
        """检查Gradle版本兼容性"""
        if not self.project_path:
            return
        
        wrapper_props = os.path.join(
            self.project_path, 'android', 'gradle', 'wrapper', 'gradle-wrapper.properties'
        )
        
        if not os.path.exists(wrapper_props):
            return
        
        try:
            with open(wrapper_props, 'r', encoding='utf-8') as f:
                content = f.read()
            
            match = re.search(r'gradle-(\d+\.\d+(?:\.\d+)?)', content)
            if not match:
                return
            
            gradle_version = match.group(1)
            major_version = int(gradle_version.split('.')[0])
            
            if major_version >= 9:
                self._add_result(
                    'Gradle 兼容性',
                    True,
                    '⚠️  Gradle {} - jcenter 已移除，友盟插件可能不兼容'.format(gradle_version),
                    'warning',
                    '建议:\n'
                    '  1. 确认友盟SDK已迁移到 mavenCentral\n'
                    '  2. 如遇依赖解析失败，尝试降级到 Gradle 8.x\n'
                    '  3. 检查 android/build.gradle 中的仓库配置'
                )
            else:
                self._add_result(
                    'Gradle 兼容性',
                    True,
                    '✅ Gradle {} 兼容'.format(gradle_version),
                    'info',
                    ''
                )
        except Exception:
            pass
    
    def _extract_version(self, version_line):
        """从版本行提取版本号"""
        match = re.search(r'(\d+\.\d+\.\d+)', version_line)
        return match.group(1) if match else 'unknown'
    
    def _version_gte(self, version_str, min_version):
        """检查版本是否 >= 最低版本要求"""
        try:
            v_parts = [int(x) for x in version_str.split('.')[:3]]
            m_parts = [int(x) for x in min_version.split('.')[:3]]
            while len(v_parts) < 3:
                v_parts.append(0)
            while len(m_parts) < 3:
                m_parts.append(0)
            return v_parts >= m_parts
        except (ValueError, AttributeError):
            return True
    
    def _add_result(self, name, passed, message, severity, install_guide):
        """添加检测结果"""
        self.results.append({
            'name': name,
            'passed': passed,
            'message': message,
            'severity': severity,
            'install_guide': install_guide
        })
        
        if not passed and severity == 'critical':
            self.all_passed = False
    
    def _print_report(self):
        """打印检测报告"""
        print("\n📋 环境检测报告")
        print("-" * 60)
        
        for result in self.results:
            print("\n{}".format(result['message']))
            
            if not result['passed']:
                print("\n  🔧 安装指引:")
                print(result['install_guide'])
        
        print("\n" + "-" * 60)
        
        if self.all_passed:
            print("✅ 环境检查通过，所有必需工具已就绪\n")
        else:
            print("❌ 环境检查失败，请先安装缺失的工具\n")
            print("安装完成后，请重新运行此脚本。")


if __name__ == '__main__':
    project_path = sys.argv[1] if len(sys.argv) > 1 else None
    checker = EnvChecker(project_path=project_path)
    checker.check_all()
