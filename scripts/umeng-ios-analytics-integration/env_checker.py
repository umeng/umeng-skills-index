# -*- coding: utf-8 -*-
"""
iOS统计SDK集成 - 环境检测模块
检测macOS系统、Xcode、CocoaPods等必需工具
"""

import platform
import subprocess
import sys
from datetime import datetime


class EnvChecker:
    """环境检测器"""
    
    def __init__(self):
        self.results = []
        self.all_passed = True
    
    def check_all(self):
        """执行所有环境检查"""
        print("\n" + "="*60)
        print("🔍 开始环境检查...")
        print("="*60 + "\n")
        
        self._check_macos()
        self._check_xcode()
        self._check_cocoapods()
        
        self._print_report()
        
        return self.all_passed
    
    def _check_macos(self):
        """检测macOS系统"""
        system = platform.system()
        if system == 'Darwin':
            version = platform.mac_ver()[0]
            self._add_result(
                'macOS系统',
                True,
                '{} {} {}'.format('✅', system, version),
                'critical',
                ''
            )
        else:
            self._add_result(
                'macOS系统',
                False,
                '❌ 当前系统: {}'.format(system),
                'critical',
                '此工具仅支持macOS系统，请在macOS环境下运行'
            )
    
    def _check_xcode(self):
        """检测Xcode是否安装"""
        try:
            result = subprocess.run(
                ['xcode-select', '-p'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                xcode_path = result.stdout.strip()
                self._add_result(
                    'Xcode',
                    True,
                    '✅ 已安装 ({})'.format(xcode_path),
                    'critical',
                    ''
                )
            else:
                self._add_result(
                    'Xcode',
                    False,
                    '❌ 未安装或未配置',
                    'critical',
                    '安装方法:\n'
                    '  方法1: App Store搜索"Xcode"安装\n'
                    '  方法2: 执行命令: xcode-select --install'
                )
        except FileNotFoundError:
            self._add_result(
                'Xcode',
                False,
                '❌ xcode-select命令不存在',
                'critical',
                '安装方法:\n'
                '  方法1: App Store搜索"Xcode"安装\n'
                '  方法2: 执行命令: xcode-select --install'
            )
        except Exception as e:
            self._add_result(
                'Xcode',
                False,
                '❌ 检测失败: {}'.format(str(e)),
                'critical',
                '请手动检查Xcode是否正确安装'
            )
    
    def _check_cocoapods(self):
        """检测CocoaPods是否安装"""
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
                    '✅ 版本 {}'.format(version),
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
            print(f"\n{result['message']}")
            
            if not result['passed']:
                print(f"\n  🔧 安装指引:")
                print(result['install_guide'])
        
        print("\n" + "-" * 60)
        
        if self.all_passed:
            print("✅ 环境检查通过，所有必需工具已就绪\n")
        else:
            print("❌ 环境检查失败，请先安装缺失的工具\n")
            print("安装完成后，请重新运行此脚本。")
            sys.exit(1)


if __name__ == '__main__':
    checker = EnvChecker()
    checker.check_all()
