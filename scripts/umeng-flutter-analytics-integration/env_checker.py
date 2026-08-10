# -*- coding: utf-8 -*-
"""
Flutter统计SDK集成 - 环境检测模块
检测Flutter SDK、Dart SDK、Android SDK、CocoaPods等必需工具
"""

import platform
import subprocess
import shutil
import sys
import os


class EnvChecker:
    """环境检测器"""
    
    def __init__(self):
        self.results = []
        self.all_passed = True
    
    def check_all(self, project_path=None):
        """执行所有环境检查
        
        Args:
            project_path: 可选，Flutter项目路径，用于Gradle兼容性检测
        """
        print("\n" + "="*60)
        print("🔍 开始环境检查...")
        print("="*60 + "\n")
        
        self._check_flutter()
        self._check_dart()
        self._check_android_sdk()
        
        # CocoaPods仅在macOS上检查
        if platform.system() == 'Darwin':
            self._check_cocoapods()
            self._check_xcode()
        
        # Gradle兼容性检查（需要项目路径）
        self._check_gradle_compatibility(project_path)
        
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
                # 解析版本号
                version_line = result.stdout.split('\n')[0]
                version = self._extract_version(version_line)
                
                # 版本下限校验
                min_flutter = '2.0.0'
                if version != 'unknown' and not self._version_gte(version, min_flutter):
                    self._add_result(
                        'Flutter SDK',
                        False,
                        '❌ Flutter {} 版本过低 (要求 >= {})'.format(version, min_flutter),
                        'critical',
                        '请升级Flutter SDK:\n'
                        '  flutter upgrade\n'
                        '  或访问 https://flutter.dev/docs/get-started/install 下载最新版本'
                    )
                else:
                    self._add_result(
                        'Flutter SDK',
                        True,
                        '✅ {} (>= {})'.format(version_line.strip(), min_flutter),
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
                version_output = result.stdout.strip() or result.stderr.strip()
                version = self._extract_version(version_output)
                
                # 版本下限校验
                min_dart = '2.12.0'
                if version != 'unknown' and not self._version_gte(version, min_dart):
                    self._add_result(
                        'Dart SDK',
                        False,
                        '❌ Dart {} 版本过低 (要求 >= {} 空安全)'.format(version, min_dart),
                        'critical',
                        '请升级Dart SDK (通常随Flutter SDK一起升级):\n'
                        '  flutter upgrade\n'
                        '  请确保Flutter SDK版本 >= 2.0.0'
                    )
                else:
                    self._add_result(
                        'Dart SDK',
                        True,
                        '✅ {} (>= {} 空安全)'.format(version_output, min_dart),
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
        # 检查ANDROID_HOME或ANDROID_SDK_ROOT环境变量
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
            # 尝试检查adb是否可用
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
        """检测 Xcode / xcodebuild（仅 macOS）"""
        if platform.system() != 'Darwin':
            return  # 非 macOS 跳过
        
        xcodebuild_path = shutil.which('xcodebuild')
        if xcodebuild_path:
            # 尝试获取版本
            try:
                result = subprocess.run(
                    ['xcodebuild', '-version'],
                    capture_output=True, text=True, timeout=10
                )
                version_info = result.stdout.split('\n')[0] if result.returncode == 0 else 'unknown'
            except Exception:
                version_info = 'available'
            self._add_result('Xcode', True,
                            '✅ {}'.format(version_info), 'warning', '')
        else:
            self._add_result('Xcode', False,
                            '❌ 未检测到 xcodebuild', 'warning',
                            '请安装 Xcode 并运行 xcode-select --install')
    
    def _check_gradle_compatibility(self, project_path=None):
        """检测 Gradle 版本兼容性"""
        if not project_path:
            return
        
        # 检查 android 目录下的 gradle-wrapper.properties
        wrapper_path = os.path.join(project_path, 'android', 'gradle', 'wrapper', 'gradle-wrapper.properties')
        if not os.path.exists(wrapper_path):
            return
        
        try:
            with open(wrapper_path, 'r') as f:
                content = f.read()
            
            # 提取 Gradle 版本
            import re
            match = re.search(r'gradle-(\d+\.\d+(?:\.\d+)?)', content)
            if match:
                gradle_version = match.group(1)
                major = int(gradle_version.split('.')[0])
                if major >= 9:
                    self._add_result('Gradle 兼容性', False,
                        '⚠️ Gradle {} 已移除 jcenter()，友盟插件可能不兼容'.format(gradle_version),
                        'warning',
                        '建议使用 Gradle 7.x 或 8.x，或等待友盟 SDK 更新仓库配置')
                else:
                    self._add_result('Gradle 兼容性', True,
                        '✅ Gradle {}'.format(gradle_version), 'info', '')
        except Exception as e:
            self._add_result('Gradle 兼容性', True,
                '⏭️ Gradle 兼容性检查跳过: {}'.format(str(e)), 'info', '')
    
    def _extract_version(self, version_line):
        """从版本行提取版本号"""
        import re
        match = re.search(r'(\d+\.\d+\.\d+)', version_line)
        return match.group(1) if match else 'unknown'
    
    def _version_gte(self, version_str, min_version):
        """检查版本是否 >= 最低版本要求"""
        try:
            v_parts = [int(x) for x in version_str.split('.')[:3]]
            m_parts = [int(x) for x in min_version.split('.')[:3]]
            # 补齐长度
            while len(v_parts) < 3:
                v_parts.append(0)
            while len(m_parts) < 3:
                m_parts.append(0)
            return v_parts >= m_parts
        except (ValueError, AttributeError):
            return True  # 解析失败时不阻塞
    
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
    checker = EnvChecker()
    checker.check_all()
