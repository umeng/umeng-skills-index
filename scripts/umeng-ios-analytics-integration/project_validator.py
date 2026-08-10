# -*- coding: utf-8 -*-
"""
iOS统计SDK集成 - 项目验证模块
验证iOS项目结构、检测项目类型、编译验证
"""

import os
import re
import subprocess
import sys


class ProjectValidator:
    """iOS项目验证器"""
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.project_info = {
            'has_xcodeproj': False,
            'has_xcworkspace': False,
            'project_name': None,
            'project_file': None,
            'schemes': [],
            'targets': [],
            'project_type': 'unknown',  # swift, objc, swiftui
            'app_delegate_path': None,
            'app_file_path': None,  # SwiftUI App文件
            'has_podfile': False,
            'bundle_identifier': None
        }
    
    def validate(self):
        """执行项目验证"""
        print("\n" + "="*60)
        print("📂 开始项目验证...")
        print("="*60 + "\n")
        
        # 步骤1: 检查项目结构
        if not self._check_project_structure():
            return False
        
        # 步骤2: 检测项目类型
        self._detect_project_type()
        
        # 步骤3: 获取项目信息
        if not self._get_project_info():
            return False
        
        # 步骤4: 检查Podfile
        self._check_podfile()
        
        # 打印项目信息
        self._print_project_info()
        
        return True
    
    def build_project(self):
        """编译项目验证"""
        print("\n" + "="*60)
        print("🔨 开始编译验证...")
        print("="*60 + "\n")
        
        if not self.project_info['schemes']:
            print("❌ 未找到可用的scheme，无法编译")
            return False
        
        # 智能选择scheme：优先选择与项目名匹配的scheme
        scheme = self._select_main_scheme()
        
        # 检查是否有workspace（pod install后生成）
        workspace_files = [f for f in os.listdir(self.project_path) 
                          if f.endswith('.xcworkspace')]
        
        if workspace_files:
            # 使用workspace编译
            project_file = os.path.join(self.project_path, workspace_files[0])
            cmd = [
                'xcodebuild',
                '-workspace', project_file,
                '-scheme', scheme,
                '-sdk', 'iphonesimulator',
                '-configuration', 'Debug',
                'build'
            ]
            print("📦 使用Workspace编译")
        else:
            # 使用project编译
            project_file = self.project_info['project_file']
            cmd = [
                'xcodebuild',
                '-project', project_file,
                '-scheme', scheme,
                '-sdk', 'iphonesimulator',
                '-configuration', 'Debug',
                'build'
            ]
            print("📦 使用Project编译")
        
        print(f"📦 编译命令: {' '.join(cmd[:6])} ...")
        print(f"📦 Scheme: {scheme}")
        print(f"📦 这可能需要几分钟，请耐心等待...\n")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                print("\n✅ 编译成功！\n")
                return True
            else:
                print("\n❌ 编译失败！")
                print("\n错误信息:")
                # 只显示最后50行错误
                lines = result.stderr.split('\n')
                for line in lines[-50:]:
                    if line.strip():
                        print(f"  {line}")
                
                # 提供针对性的解决建议
                print("\n💡 可能的原因和解决建议:")
                
                error_output = result.stderr + result.stdout
                
                if "framework not found" in error_output.lower():
                    print("\n  🔍 检测到 'framework not found' 错误:")
                    print("  1. 确认使用.xcworkspace打开项目（不是.xcodeproj）")
                    print("  2. 检查Pods目录是否存在且包含相应framework")
                    print("  3. 尝试 Clean Build Folder (⇧⌘K)")
                    print("  4. 删除DerivedData后重新打开项目")
                    print("  5. 重新运行 'pod install'")
                elif "UMCommon" in error_output:
                    print("\n  🔍 检测到UMCommon相关错误:")
                    print("  1. 检查Podfile是否包含 pod UMCommon")
                    print("  2. 确认Pods/UMCommon目录存在")
                    print("  3. 运行 pod repo update 更新源")
                    print("  4. 删除Pods和workspace后重新 pod install")
                elif "linker command failed" in error_output.lower():
                    print("\n  🔍 检测到链接器错误:")
                    print("  1. 确认使用.xcworkspace而非.xcodeproj")
                    print("  2. 检查Build Settings中的Framework Search Paths")
                    print("  3. Clean Build Folder (⇧⌘K) 后重新编译")
                else:
                    print("\n  📝 通用解决建议:")
                    print("  1. 在Xcode中打开.xcworkspace项目")
                    print("  2. Clean Build Folder (⇧⌘K)")
                    print("  3. 检查错误详情并修复")
                    print("  4. 重新编译验证")
                
                print("\n请在Xcode中打开项目，修复编译错误后再运行此脚本。")
                return False
                
        except subprocess.TimeoutExpired:
            print("\n❌ 编译超时（超过10分钟）")
            return False
        except Exception as e:
            print(f"\n❌ 编译过程出错: {str(e)}")
            return False
    
    def _check_project_structure(self):
        """检查项目结构"""
        print("🔍 检查项目结构...")
        
        # 查找.xcodeproj
        xcodeproj_files = [f for f in os.listdir(self.project_path) 
                          if f.endswith('.xcodeproj')]
        
        if xcodeproj_files:
            self.project_info['has_xcodeproj'] = True
            self.project_info['project_name'] = xcodeproj_files[0].replace('.xcodeproj', '')
            self.project_info['project_file'] = os.path.join(self.project_path, xcodeproj_files[0])
            print(f"  ✅ 找到Xcode项目: {xcodeproj_files[0]}")
            if len(xcodeproj_files) > 1:
                print("\n⚠️  检测到多个 .xcodeproj 文件:")
                for f in xcodeproj_files:
                    print(f"   - {f}")
                print("   多个 .xcodeproj 可能导致 pod install 失败，建议删除旧的项目文件后重新运行")
        else:
            print("  ❌ 未找到.xcodeproj文件")
            return False
        
        # 查找.xcworkspace（如果存在，优先使用）
        xcworkspace_files = [f for f in os.listdir(self.project_path) 
                            if f.endswith('.xcworkspace')]
        
        if xcworkspace_files:
            self.project_info['has_xcworkspace'] = True
            self.project_info['project_file'] = os.path.join(self.project_path, xcworkspace_files[0])
            print(f"  ✅ 找到Workspace: {xcworkspace_files[0]}")
        
        return True
    
    def _detect_project_type(self):
        """检测项目类型（Swift/ObjC/SwiftUI）"""
        print("\n🔍 检测项目类型...")
        
        # 遍历项目目录查找Swift文件
        source_dir = os.path.join(self.project_path, self.project_info['project_name'])
        
        if not os.path.exists(source_dir):
            # 尝试查找其他目录
            for item in os.listdir(self.project_path):
                item_path = os.path.join(self.project_path, item)
                if os.path.isdir(item_path) and not item.endswith('.xcodeproj'):
                    source_dir = item_path
                    break
        
        swiftui_found = False
        swift_found = False
        objc_found = False
        
        if os.path.exists(source_dir):
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.endswith('.swift'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 检测@main修饰符
                            if '@main' in content and 'App' in content:
                                swiftui_found = True
                                self.project_info['app_file_path'] = file_path
                                print(f"  ✅ 发现SwiftUI App文件: {file}")
                            elif 'AppDelegate' in file and 'UIApplicationDelegate' in content:
                                swift_found = True
                                self.project_info['app_delegate_path'] = file_path
                                print(f"  ✅ 发现Swift AppDelegate: {file}")
                            else:
                                swift_found = True
                    
                    elif file.endswith('.m'):
                        objc_found = True
                        if 'AppDelegate' in file:
                            self.project_info['app_delegate_path'] = os.path.join(root, file)
                            print(f"  ✅ 发现Objective-C AppDelegate: {file}")
        
        # 判断项目类型
        if swiftui_found:
            self.project_info['project_type'] = 'swiftui'
            print(f"\n📱 项目类型: SwiftUI")
        elif swift_found:
            self.project_info['project_type'] = 'swift'
            print(f"\n📱 项目类型: Swift")
        elif objc_found:
            self.project_info['project_type'] = 'objc'
            print(f"\n📱 项目类型: Objective-C")
        else:
            self.project_info['project_type'] = 'unknown'
            print(f"\n⚠️  项目类型: 未知")
    
    def _get_project_info(self):
        """获取项目信息（schemes, targets）"""
        print("\n🔍 获取项目信息...")
        
        # 检查是否有workspace
        workspace_files = [f for f in os.listdir(self.project_path) 
                          if f.endswith('.xcworkspace')]
        
        if workspace_files:
            # 使用workspace获取schemes
            workspace_file = os.path.join(self.project_path, workspace_files[0])
            self.project_info['project_file'] = workspace_file
            cmd = ['xcodebuild', '-workspace', workspace_file, '-list']
        else:
            # 使用project获取schemes
            cmd = ['xcodebuild', '-project', self.project_info['project_file'], '-list']
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # 解析schemes和targets
                lines = output.split('\n')
                section = None
                
                for line in lines:
                    stripped = line.strip()
                    
                    # 检测段落
                    if 'Targets:' in stripped:
                        section = 'targets'
                        continue
                    elif 'Build Configurations:' in stripped:
                        section = 'configs'
                        continue
                    elif 'Schemes:' in stripped:
                        section = 'schemes'
                        continue
                    
                    # 收集数据
                    if section == 'targets' and stripped and not stripped.startswith(' '):
                        self.project_info['targets'].append(stripped)
                    elif section == 'schemes' and stripped:
                        self.project_info['schemes'].append(stripped)
                
                print(f"  ✅ 找到 {len(self.project_info['schemes'])} 个scheme(s)")
                print(f"  ✅ 找到 {len(self.project_info['targets'])} 个target(s)")
                
                if self.project_info['schemes']:
                    print(f"  📋 Schemes: {', '.join(self.project_info['schemes'])}")
                if self.project_info['targets']:
                    print(f"  📋 Targets: {', '.join(self.project_info['targets'])}")
                
                return True
            else:
                print(f"  ❌ 获取项目信息失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ 获取项目信息出错: {str(e)}")
            return False
    
    def _check_podfile(self):
        """检查Podfile"""
        podfile_path = os.path.join(self.project_path, 'Podfile')
        
        if os.path.exists(podfile_path):
            self.project_info['has_podfile'] = True
            print(f"\n  ✅ 找到Podfile")
        else:
            print(f"\n  ⚠️  未找到Podfile（将自动创建）")
    
    def _print_project_info(self):
        """打印项目信息"""
        print("\n" + "-" * 60)
        print("📋 项目信息")
        print("-" * 60)
        print(f"  项目名称: {self.project_info['project_name']}")
        print(f"  项目类型: {self.project_info['project_type']}")
        print(f"  Podfile: {'✅ 存在' if self.project_info['has_podfile'] else '❌ 不存在'}")
        print(f"  Schemes: {len(self.project_info['schemes'])}")
        print(f"  Targets: {len(self.project_info['targets'])}")
        
        if self.project_info['app_file_path']:
            print(f"  SwiftUI App: {os.path.basename(self.project_info['app_file_path'])}")
        if self.project_info['app_delegate_path']:
            print(f"  AppDelegate: {os.path.basename(self.project_info['app_delegate_path'])}")
        
        print("-" * 60)
    
    def _select_main_scheme(self):
        """智能选择主项目的scheme（而非Pods或其他库的scheme）"""
        project_name = self.project_info['project_name']
        schemes = self.project_info['schemes']
        
        # 优先选择与项目名完全匹配的scheme
        for scheme in schemes:
            if scheme.strip() == project_name:
                print(f"📦 选择主项目scheme: {scheme}")
                return scheme.strip()
        
        # 其次选择包含项目名的scheme
        for scheme in schemes:
            if project_name in scheme:
                print(f"📦 选择scheme: {scheme}")
                return scheme.strip()
        
        # 最后选择第一个非Pods的scheme
        for scheme in schemes:
            if not scheme.startswith('Pods-'):
                print(f"📦 选择scheme: {scheme}")
                return scheme.strip()
        
        # 如果都不满足，返回第一个
        print(f"📦 选择scheme: {schemes[0]}")
        return schemes[0].strip()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python project_validator.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    validator = ProjectValidator(project_path)
    
    if validator.validate():
        print("\n✅ 项目验证通过")
        
        # 测试编译
        print("\n是否进行编译验证? (y/n): ", end='')
        choice = input().strip().lower()
        if choice == 'y':
            validator.build_project()
    else:
        print("\n❌ 项目验证失败")
        sys.exit(1)
