# -*- coding: utf-8 -*-
"""
iOS APM SDK集成 - 项目验证模块
验证iOS项目结构、检测项目类型、UMCommon前置条件检查、编译验证
"""

import os
import re
import subprocess
import sys


class ProjectValidator:
    """iOS项目验证器（含APM前置条件检查）"""
    
    def __init__(self, project_path):
        """
        初始化项目验证器
        
        Args:
            project_path: iOS项目路径（包含.xcodeproj的目录）
        """
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
        """
        执行项目验证
        
        Returns:
            bool: 验证是否通过
        """
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
    
    def check_umcommon_prerequisite(self):
        """
        检查UMCommon前置条件（APM必须在统计SDK之后集成）
        
        检查项：
        1. Podfile是否包含 pod 'UMCommon'
        2. Pods/目录下UMCommon是否存在
        3. 源码中是否存在 UMConfigure.initWithAppkey 调用
        
        Returns:
            bool: 前置条件是否满足
        """
        print("\n" + "="*60)
        print("📋 检查APM前置条件（UMCommon统计SDK）...")
        print("="*60 + "\n")
        
        all_passed = True
        
        # 检查1: Podfile中是否包含 UMCommon
        podfile_path = os.path.join(self.project_path, 'Podfile')
        has_umcommon_in_podfile = False
        
        if os.path.exists(podfile_path):
            with open(podfile_path, 'r', encoding='utf-8') as f:
                podfile_content = f.read()
            
            if "UMCommon" in podfile_content:
                has_umcommon_in_podfile = True
                print("  ✅ Podfile 包含 pod 'UMCommon'")
            else:
                print("  ❌ Podfile 未包含 pod 'UMCommon'")
                all_passed = False
        else:
            print("  ❌ Podfile 不存在")
            all_passed = False
        
        # 检查2: Pods/UMCommon 目录是否存在
        pods_umcommon_dir = os.path.join(self.project_path, 'Pods', 'UMCommon')
        if os.path.exists(pods_umcommon_dir):
            contents = os.listdir(pods_umcommon_dir)
            if len(contents) > 0:
                print("  ✅ Pods/UMCommon 目录存在且有内容")
            else:
                print("  ❌ Pods/UMCommon 目录为空")
                all_passed = False
        else:
            print("  ❌ Pods/UMCommon 目录不存在")
            all_passed = False
        
        # 检查3: 源码中是否存在 UMConfigure.initWithAppkey 调用
        has_init_call = self._check_umconfigure_init_call()
        if has_init_call:
            print("  ✅ 检测到 UMConfigure.initWithAppkey 调用")
        else:
            print("  ❌ 未检测到 UMConfigure.initWithAppkey 调用")
            all_passed = False
        
        # 结果判断
        if not all_passed:
            print("\n" + "-" * 60)
            print("❌ APM前置条件检查失败！")
            print("-" * 60)
            print("\n友盟APM SDK强依赖统计基础SDK（UMCommon），请先集成统计SDK：")
            print("\n  运行 ios-analytics-integration Skill 完成统计SDK集成")
            print("\n  或手动确保以下条件满足：")
            print("  1. Podfile 中包含 pod 'UMCommon'")
            print("  2. 已执行 pod install 且 Pods/UMCommon 存在")
            print("  3. AppDelegate 中已调用 UMConfigure.initWithAppkey()")
            print("-" * 60)
            return False
        
        print("\n✅ APM前置条件检查通过：统计SDK已集成\n")
        return True
    
    def extract_appkey_from_code(self):
        """从已集成的 UMConfigure.initWithAppkey 调用中提取 appkey 值"""
        import re
        
        for root, dirs, files in os.walk(self.project_path):
            # 跳过无关目录
            if any(skip in root for skip in ['Pods', '.xcframework', 'backups']):
                continue
            for file in files:
                if not file.endswith(('.swift', '.m')):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Swift: UMConfigure.initWithAppkey("xxxxx"
                    swift_match = re.search(r'UMConfigure\.initWithAppkey\("([^"]+)"', content)
                    if swift_match:
                        return swift_match.group(1)
                    # ObjC: [UMConfigure initWithAppkey:@"xxxxx"
                    objc_match = re.search(r'\[UMConfigure\s+initWithAppkey:@"([^"]+)"', content)
                    if objc_match:
                        return objc_match.group(1)
                except (IOError, UnicodeDecodeError):
                    continue
        return None
    
    def _check_umconfigure_init_call(self):
        """检查源码中是否存在UMConfigure初始化调用"""
        project_name = self.project_info.get('project_name')
        if not project_name:
            # 从目录中推断
            for item in os.listdir(self.project_path):
                if item.endswith('.xcodeproj'):
                    project_name = item.replace('.xcodeproj', '')
                    break
        
        if not project_name:
            return False
        
        # 搜索源码目录
        source_dir = os.path.join(self.project_path, project_name)
        if not os.path.exists(source_dir):
            # 尝试查找其他目录
            for item in os.listdir(self.project_path):
                item_path = os.path.join(self.project_path, item)
                if os.path.isdir(item_path) and not item.endswith(
                    ('.xcodeproj', '.xcworkspace', 'Pods', 'backups')
                ):
                    source_dir = item_path
                    break
        
        if not os.path.exists(source_dir):
            return False
        
        # 遍历源码目录查找初始化调用
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith(('.swift', '.m')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Swift: UMConfigure.initWithAppkey
                        # ObjC: [UMConfigure initWithAppkey
                        if ('UMConfigure.initWithAppkey' in content or
                                '[UMConfigure initWithAppkey' in content):
                            return True
                    except (IOError, UnicodeDecodeError):
                        continue
        
        return False
    
    def build_project(self, target_name=None):
        """
        编译项目验证
        
        Args:
            target_name: 指定的Target名称（可选，用于辅助选择正确的App scheme）
        
        Returns:
            bool: 编译是否成功
        """
        print("\n" + "="*60)
        print("🔨 开始编译验证...")
        print("="*60 + "\n")
        
        if not self.project_info['schemes']:
            print("❌ 未找到可用的scheme，无法编译")
            return False
        
        # 智能选择scheme（传入target_name辅助过滤SDK scheme）
        scheme = self._select_main_scheme(target_name=target_name)
        
        # 检查是否有workspace（pod install后生成）
        workspace_files = [f for f in os.listdir(self.project_path) 
                          if f.endswith('.xcworkspace')]
        
        if workspace_files:
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
        
        print("📦 编译命令: {} ...".format(' '.join(cmd[:6])))
        print("📦 Scheme: {}".format(scheme))
        print("📦 这可能需要几分钟，请耐心等待...\n")
        
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
                lines = result.stderr.split('\n')
                for line in lines[-50:]:
                    if line.strip():
                        print("  {}".format(line))
                
                # 提供针对性解决建议
                self._print_build_suggestions(result.stderr + result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            print("\n❌ 编译超时（超过10分钟）")
            return False
        except Exception as e:
            print("\n❌ 编译过程出错: {}".format(str(e)))
            return False
    
    def _print_build_suggestions(self, error_output):
        """打印编译错误的解决建议"""
        print("\n💡 可能的原因和解决建议:")
        
        if "framework not found" in error_output.lower():
            print("\n  🔍 检测到 'framework not found' 错误:")
            print("  1. 确认使用.xcworkspace打开项目（不是.xcodeproj）")
            print("  2. 检查Pods目录是否存在且包含相应framework")
            print("  3. 尝试 Clean Build Folder (⇧⌘K)")
            print("  4. 删除DerivedData后重新打开项目")
            print("  5. 重新运行 'pod install'")
        elif "UMAPM" in error_output:
            print("\n  🔍 检测到UMAPM相关错误:")
            print("  1. 检查Podfile是否包含 pod 'UMAPM'")
            print("  2. 确认Pods/UMAPM目录存在")
            print("  3. 运行 pod repo update 更新源")
            print("  4. 删除Pods和workspace后重新 pod install")
        elif "UMCommon" in error_output:
            print("\n  🔍 检测到UMCommon相关错误:")
            print("  1. 检查Podfile是否包含 pod 'UMCommon'")
            print("  2. 确认Pods/UMCommon目录存在")
            print("  3. 运行 pod repo update 更新源")
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
            print("  ✅ 找到Xcode项目: {}".format(xcodeproj_files[0]))
            if len(xcodeproj_files) > 1:
                print("\n⚠️  检测到多个 .xcodeproj 文件:")
                for f in xcodeproj_files:
                    print(f"   - {f}")
                print("   多个 .xcodeproj 可能导致 pod install 失败，建议删除旧的项目文件后重新运行")
        else:
            print("  ❌ 未找到.xcodeproj文件")
            return False
        
        # 查找.xcworkspace
        xcworkspace_files = [f for f in os.listdir(self.project_path) 
                            if f.endswith('.xcworkspace')]
        
        if xcworkspace_files:
            self.project_info['has_xcworkspace'] = True
            self.project_info['project_file'] = os.path.join(self.project_path, xcworkspace_files[0])
            print("  ✅ 找到Workspace: {}".format(xcworkspace_files[0]))
        
        return True
    
    def _detect_project_type(self):
        """检测项目类型（Swift/ObjC/SwiftUI）"""
        print("\n🔍 检测项目类型...")
        
        source_dir = os.path.join(self.project_path, self.project_info['project_name'])
        
        if not os.path.exists(source_dir):
            for item in os.listdir(self.project_path):
                item_path = os.path.join(self.project_path, item)
                if os.path.isdir(item_path) and not item.endswith(
                    ('.xcodeproj', '.xcworkspace', 'Pods', 'backups')
                ):
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
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            if '@main' in content and 'App' in content:
                                swiftui_found = True
                                self.project_info['app_file_path'] = file_path
                                print("  ✅ 发现SwiftUI App文件: {}".format(file))
                            elif 'AppDelegate' in file and 'UIApplicationDelegate' in content:
                                swift_found = True
                                self.project_info['app_delegate_path'] = file_path
                                print("  ✅ 发现Swift AppDelegate: {}".format(file))
                            else:
                                swift_found = True
                        except (IOError, UnicodeDecodeError):
                            continue
                    
                    elif file.endswith('.m'):
                        objc_found = True
                        if 'AppDelegate' in file:
                            self.project_info['app_delegate_path'] = os.path.join(root, file)
                            print("  ✅ 发现Objective-C AppDelegate: {}".format(file))
        
        # 判断项目类型
        if swiftui_found:
            self.project_info['project_type'] = 'swiftui'
            print("\n📱 项目类型: SwiftUI")
        elif swift_found:
            self.project_info['project_type'] = 'swift'
            print("\n📱 项目类型: Swift")
        elif objc_found:
            self.project_info['project_type'] = 'objc'
            print("\n📱 项目类型: Objective-C")
        else:
            self.project_info['project_type'] = 'unknown'
            print("\n⚠️  项目类型: 未知")
    
    def _get_project_info(self):
        """获取项目信息（schemes, targets）"""
        print("\n🔍 获取项目信息...")
        
        workspace_files = [f for f in os.listdir(self.project_path) 
                          if f.endswith('.xcworkspace')]
        
        if workspace_files:
            workspace_file = os.path.join(self.project_path, workspace_files[0])
            self.project_info['project_file'] = workspace_file
            cmd = ['xcodebuild', '-workspace', workspace_file, '-list']
        else:
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
                lines = output.split('\n')
                section = None
                
                for line in lines:
                    stripped = line.strip()
                    
                    if 'Targets:' in stripped:
                        section = 'targets'
                        continue
                    elif 'Build Configurations:' in stripped:
                        section = 'configs'
                        continue
                    elif 'Schemes:' in stripped:
                        section = 'schemes'
                        continue
                    
                    if section == 'targets' and stripped and not stripped.startswith(' '):
                        self.project_info['targets'].append(stripped)
                    elif section == 'schemes' and stripped:
                        self.project_info['schemes'].append(stripped)
                
                print("  ✅ 找到 {} 个scheme(s)".format(len(self.project_info['schemes'])))
                print("  ✅ 找到 {} 个target(s)".format(len(self.project_info['targets'])))
                
                if self.project_info['schemes']:
                    print("  📋 Schemes: {}".format(', '.join(self.project_info['schemes'])))
                if self.project_info['targets']:
                    print("  📋 Targets: {}".format(', '.join(self.project_info['targets'])))
                
                return True
            else:
                print("  ❌ 获取项目信息失败: {}".format(result.stderr))
                return False
                
        except Exception as e:
            print("  ❌ 获取项目信息出错: {}".format(str(e)))
            return False
    
    def _check_podfile(self):
        """检查Podfile"""
        podfile_path = os.path.join(self.project_path, 'Podfile')
        
        if os.path.exists(podfile_path):
            self.project_info['has_podfile'] = True
            print("\n  ✅ 找到Podfile")
        else:
            print("\n  ⚠️  未找到Podfile")
    
    def _print_project_info(self):
        """打印项目信息"""
        print("\n" + "-" * 60)
        print("📋 项目信息")
        print("-" * 60)
        print("  项目名称: {}".format(self.project_info['project_name']))
        print("  项目类型: {}".format(self.project_info['project_type']))
        print("  Podfile: {}".format('✅ 存在' if self.project_info['has_podfile'] else '❌ 不存在'))
        print("  Schemes: {}".format(len(self.project_info['schemes'])))
        print("  Targets: {}".format(len(self.project_info['targets'])))
        
        if self.project_info['app_file_path']:
            print("  SwiftUI App: {}".format(os.path.basename(self.project_info['app_file_path'])))
        if self.project_info['app_delegate_path']:
            print("  AppDelegate: {}".format(os.path.basename(self.project_info['app_delegate_path'])))
        
        print("-" * 60)
    
    def _select_main_scheme(self, target_name=None):
        """智能选择主项目的App scheme
        
        优先级：
        1. 与 target 名完全匹配的 scheme
        2. 与项目名完全匹配的 scheme
        3. 包含项目名的 scheme（排除 Pods- 前缀和已知 SDK scheme）
        4. 排除 Pods- 前缀和已知 SDK scheme 后的第一个
        5. 最终回退到第一个 scheme
        """
        project_name = self.project_info['project_name']
        schemes = self.project_info['schemes']
        
        # 已知 SDK scheme 名（pod 依赖名）
        sdk_schemes = {'UMAPM', 'UMCommon', 'UMDevice', 'UMCrash'}
        
        # 优先选择与 target 名完全匹配的 scheme
        if target_name and target_name in schemes:
            print("📦 选择Target匹配的scheme: {}".format(target_name))
            return target_name
        
        # 其次选择与项目名完全匹配的scheme
        for scheme in schemes:
            if scheme.strip() == project_name:
                print("📦 选择主项目scheme: {}".format(scheme))
                return scheme.strip()
        
        # 再次选择包含项目名的scheme（排除SDK scheme）
        for scheme in schemes:
            if project_name in scheme and scheme.strip() not in sdk_schemes:
                print("📦 选择scheme: {}".format(scheme))
                return scheme.strip()
        
        # 过滤后的候选列表：排除 Pods- 前缀和已知 SDK scheme
        candidates = [
            s.strip() for s in schemes
            if not s.startswith('Pods-') and s.strip() not in sdk_schemes
        ]
        
        if candidates:
            print("📦 选择scheme: {}".format(candidates[0]))
            return candidates[0]
        
        # 最终回退到第一个 scheme
        fallback = schemes[0].strip() if schemes else (target_name or project_name)
        print("📦 选择scheme（回退）: {}".format(fallback))
        return fallback


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python project_validator.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    validator = ProjectValidator(project_path)
    
    if validator.validate():
        print("\n✅ 项目验证通过")
        
        # 检查APM前置条件
        if validator.check_umcommon_prerequisite():
            print("\n✅ APM前置条件检查通过")
        else:
            print("\n❌ APM前置条件检查失败")
            sys.exit(1)
    else:
        print("\n❌ 项目验证失败")
        sys.exit(1)
