# -*- coding: utf-8 -*-
"""
iOS统计SDK集成 - SDK集成模块
负责Podfile修改、pod install执行、代码注入
"""

import os
import re
import shutil
import subprocess
import sys


class SDKIntegrator:
    """iOS统计SDK集成器"""
    
    def __init__(self, project_path, config):
        self.project_path = project_path
        self.config = config
        self.app_key = config.get('app_key', 'YOUR_UMENG_APPKEY')
        self.channel = config.get('channel', 'App Store')
        self.target = config.get('target')
        
        # 友盟SDK依赖（v1.0仅包含核心统计SDK，不含UMCCommonLog）
        self.umeng_pods = [
            "pod 'UMCommon'",
            "pod 'UMDevice'"
        ]
    
    def integrate(self):
        """执行SDK集成"""
        print("\n" + "="*60)
        print("📦 开始SDK集成...")
        print("="*60 + "\n")
        
        # 步骤1: 修改Podfile
        if not self._update_podfile():
            return False
        
        # 步骤2: 执行pod install
        if not self._run_pod_install():
            return False
        
        # 步骤3: 修复项目配置（Sandbox权限问题）
        self._fix_project_settings()
        
        # 步骤4: 注入初始化代码
        if not self._inject_init_code():
            return False
        
        print("\n✅ SDK集成完成\n")
        return True
    
    def _update_podfile(self):
        """修改Podfile添加友盟SDK依赖"""
        print("📝 修改Podfile...")
        
        podfile_path = os.path.join(self.project_path, 'Podfile')
        
        # 如果Podfile不存在，创建一个新的
        if not os.path.exists(podfile_path):
            print("  📄 Podfile不存在，创建新的Podfile")
            self._create_podfile(podfile_path)
        else:
            print("  📄 找到现有Podfile")
            self._modify_podfile(podfile_path)
        
        return True
    
    def _create_podfile(self, podfile_path):
        """创建新的Podfile"""
        target_name = self._get_target_name()
        
        podfile_content = """# Uncomment the next line to define a global platform for your project
platform :ios, '14.0'

target '{target}' do
  use_frameworks!
  
  # 友盟统计SDK
  {pods}
  
  # 自动修正Pods的iOS部署目标版本
  post_install do |installer|
    installer.pods_project.targets.each do |target|
      target.build_configurations.each do |config|
        if config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'].to_f < 14.0
          config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '14.0'
        end
      end
    end
  end
end
""".format(
            target=target_name,
            pods='\n  '.join(self.umeng_pods)
        )
        
        with open(podfile_path, 'w', encoding='utf-8') as f:
            f.write(podfile_content)
        
        print("  ✅ Podfile创建成功")
    
    def _modify_podfile(self, podfile_path):
        """修改现有Podfile"""
        with open(podfile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经包含友盟SDK
        has_umeng = any(pod in content for pod in ['UMCommon', 'UMDevice', 'UMCCommonLog'])
        
        if has_umeng:
            print("  ⚠️  Podfile已包含友盟SDK依赖，跳过添加")
            return
        
        # 获取target名称
        target_name = self._get_target_name()
        
        # 在target块中添加依赖
        # 匹配 target 'xxx' do ... end
        pattern = r"(target\s+['\"]{}['\"]\s+do\s+)(.*?)(\nend)".format(target_name)
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            # 在target块末尾添加依赖
            new_content = content[:match.end(2)] + '\n\n  # 友盟统计SDK\n  ' + '\n  '.join(self.umeng_pods) + content[match.end(2):]
            
            with open(podfile_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("  ✅ Podfile修改成功")
        else:
            # 如果没有找到target块，追加到文件末尾
            print("  ⚠️  未找到target块，追加到文件末尾")
            
            with open(podfile_path, 'a', encoding='utf-8') as f:
                f.write("\n\ntarget '{}' do\n".format(target_name))
                f.write("  # 友盟统计SDK\n")
                f.write('  ' + '\n  '.join(self.umeng_pods) + '\n')
                f.write("end\n")
            
            print("  ✅ Podfile修改成功")
    
    def _parse_pbxproj_targets(self, pbxproj_path):
        """从 project.pbxproj 解析应用类型的 PBXNativeTarget 名称列表"""
        targets = []
        try:
            with open(pbxproj_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取 PBXNativeTarget section
            section_match = re.search(
                r'/\* Begin PBXNativeTarget section \*/(.*?)/\* End PBXNativeTarget section \*/',
                content, re.DOTALL
            )
            if not section_match:
                return targets
            
            section = section_match.group(1)
            
            # 按 target 块分割（每个块以 }; 结束）
            blocks = re.split(r'\n\t\t\};', section)
            for block in blocks:
                name_match = re.search(r'\bname\s*=\s*"?([^";]+)"?\s*;', block)
                product_type_match = re.search(r'productType\s*=\s*"([^"]+)"', block)
                if name_match:
                    name = name_match.group(1)
                    # 优先返回 application 类型的 target
                    if product_type_match:
                        if 'application' in product_type_match.group(1):
                            targets.insert(0, name)
                        else:
                            targets.append(name)
                    else:
                        targets.append(name)
        except Exception:
            pass
        return targets
    
    def _get_target_name(self):
        """获取target名称"""
        if self.target:
            return self.target
        
        # 从 .xcodeproj/project.pbxproj 中解析真实 target 名称
        for item in os.listdir(self.project_path):
            if item.endswith('.xcodeproj'):
                pbxproj_path = os.path.join(self.project_path, item, 'project.pbxproj')
                if os.path.exists(pbxproj_path):
                    targets = self._parse_pbxproj_targets(pbxproj_path)
                    if targets:
                        return targets[0]  # 返回第一个应用类型 target
                # fallback: 从文件名推断
                return item.replace('.xcodeproj', '')
        
        # 最终回退到目录名
        return os.path.basename(self.project_path)
    
    def _run_pod_install(self):
        """执行pod install"""
        print("\n🔧 执行pod install...")
        print("  这可能需要几分钟，请耐心等待...\n")
        
        try:
            result = subprocess.run(
                ['pod', 'install'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print("  ✅ pod install成功")
                
                # 检查是否生成了.xcworkspace
                workspace_files = [f for f in os.listdir(self.project_path) 
                                  if f.endswith('.xcworkspace')]
                if workspace_files:
                    print("  ✅ 生成Workspace: {}".format(workspace_files[0]))
                
                # 验证依赖是否正确安装
                if not self._verify_pods_installed():
                    print("  ⚠️  警告: 依赖验证失败，请检查Podfile配置")
                    return False
                
                return True
            else:
                print("  ❌ pod install失败")
                print("\n错误信息:")
                if result.stderr:
                    for line in result.stderr.split('\n')[-20:]:
                        if line.strip():
                            print("    {}".format(line))
                return False
                
        except subprocess.TimeoutExpired:
            print("  ❌ pod install超时（超过5分钟）")
            return False
        except Exception as e:
            print("  ❌ pod install出错: {}".format(str(e)))
            return False
    
    def _verify_pods_installed(self):
        """验证Pods依赖是否正确安装"""
        print("\n🔍 验证Pods依赖...")
        
        pods_dir = os.path.join(self.project_path, 'Pods')
        
        # 检查Pods目录是否存在
        if not os.path.exists(pods_dir):
            print("  ❌ Pods目录不存在")
            return False
        
        # 检查友盟SDK是否存在
        umcommon_dir = os.path.join(pods_dir, 'UMCommon')
        if not os.path.exists(umcommon_dir):
            print("  ❌ UMCommon SDK未安装")
            print("\n💡 可能的原因:")
            print("  1. Podfile配置有误")
            print("  2. CocoaPods源无法访问（需要翻墙）")
            print("  3. 网络问题导致下载失败")
            print("\n🔧 解决建议:")
            print("  1. 检查Podfile文件内容")
            print("  2. 运行 'pod repo update' 更新源")
            print("  3. 删除Pods目录后重新运行 'pod install'")
            print("  4. 如果网络问题，考虑使用镜像源")
            return False
        
        # 检查UMCommon.framework是否存在
        umcommon_framework = os.path.join(
            pods_dir, 
            'UMCommon', 
            'UMCommon_{}-{}'.format(
                self._get_target_name(),
                'Debug-iphonesimulator'  # 简化检查
            )
        )
        
        # 只需检查UMCommon目录有内容即可
        if os.path.exists(umcommon_dir):
            contents = os.listdir(umcommon_dir)
            if len(contents) > 0:
                print("  ✅ UMCommon SDK已安装")
                return True
            else:
                print("  ❌ UMCommon目录为空")
                return False
        
        print("  ✅ Pods依赖验证通过")
        return True
    
    def _fix_project_settings(self):
        """修复项目Build Settings中的问题"""
        print("🔧 修复项目配置...")
        
        # 1. 修复ENABLE_USER_SCRIPT_SANDBOXING问题
        # CocoaPods的脚本需要在Sandbox关闭时才能正常运行
        project_name = self._get_target_name()
        pbxproj_path = os.path.join(
            self.project_path,
            '{}.xcodeproj'.format(project_name),
            'project.pbxproj'
        )
        
        if os.path.exists(pbxproj_path):
            with open(pbxproj_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            
            # 检查是否已有ENABLE_USER_SCRIPT_SANDBOXING设置
            if 'ENABLE_USER_SCRIPT_SANDBOXING' in content:
                # 将YES改为NO
                new_content = content.replace(
                    'ENABLE_USER_SCRIPT_SANDBOXING = YES',
                    'ENABLE_USER_SCRIPT_SANDBOXING = NO'
                )
                if new_content != content:
                    with open(pbxproj_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print("  ✅ 已关闭User Script Sandboxing")
                    modified = True
                else:
                    print("  ✅ ENABLE_USER_SCRIPT_SANDBOXING 已关闭，跳过（重复检测）")
                    modified = True
            else:
                # 在Build Settings中添加
                # 在所有Debug和Release配置块中添加
                pattern = r'(buildSettings = \{\n(?:\s+\w+ = [^;]+;\n)*?)(\s+\};)'
                
                def add_sandbox_setting(match):
                    block = match.group(1)
                    # 检查是否是target的buildSettings（包含PRODUCT_BUNDLE_IDENTIFIER）
                    if 'PRODUCT_BUNDLE_IDENTIFIER' in block:
                        return block + '\t\t\tENABLE_USER_SCRIPT_SANDBOXING = NO;\n' + match.group(2)
                    return match.group(0)
                
                new_content = re.sub(pattern, add_sandbox_setting, content)
                if new_content != content:
                    with open(pbxproj_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print("  ✅ 已添加ENABLE_USER_SCRIPT_SANDBOXING = NO")
                    modified = True
            
            if not modified:
                print("  ℹ️  项目配置无需修改")
        else:
            print("  ⚠️  未找到project.pbxproj文件")
    
    def _inject_init_code(self):
        """注入SDK初始化代码"""
        print("\n💉 注入SDK初始化代码...")
        
        # 检测项目类型
        project_type = self._detect_project_type()
        
        if project_type == 'swiftui':
            return self._inject_swiftui_code()
        elif project_type == 'swift':
            return self._inject_swift_code()
        elif project_type == 'objc':
            return self._inject_objc_code()
        else:
            print("  ❌ 无法识别项目类型")
            return False
    
    def _detect_project_type(self):
        """检测项目类型"""
        project_name = self._get_target_name()
        source_dir = os.path.join(self.project_path, project_name)
        
        if not os.path.exists(source_dir):
            # 尝试查找
            for item in os.listdir(self.project_path):
                item_path = os.path.join(self.project_path, item)
                if os.path.isdir(item_path) and not item.endswith(('.xcodeproj', '.xcworkspace', 'Pods')):
                    source_dir = item_path
                    break
        
        if not os.path.exists(source_dir):
            return 'unknown'
        
        # 查找SwiftUI App文件
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.swift'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '@main' in content and 'App' in content:
                            return 'swiftui'
                        elif 'AppDelegate' in file and 'UIApplicationDelegate' in content:
                            return 'swift'
                elif file.endswith('.m') and 'AppDelegate' in file:
                    return 'objc'
        
        return 'unknown'
    
    def _inject_swiftui_code(self):
        """SwiftUI项目代码注入"""
        print("  📱 项目类型: SwiftUI")
        
        project_name = self._get_target_name()
        source_dir = os.path.join(self.project_path, project_name)
        
        # 查找SwiftUI App文件
        app_file = None
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.swift'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '@main' in content and 'App' in content:
                            app_file = file_path
                            break
            if app_file:
                break
        
        if not app_file:
            print("  ❌ 未找到SwiftUI App文件")
            return False
        
        print("  📄 找到App文件: {}".format(os.path.basename(app_file)))
        
        # 备份原文件
        backup_path = app_file + '.backup'
        shutil.copy2(app_file, backup_path)
        print("  💾 已备份: {}".format(os.path.basename(backup_path)))
        
        # 读取原文件
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加import语句
        if 'import UMCommon' not in content:
            # 在最后一个import后添加
            import_pattern = r'(import\s+\w+\n)'
            imports = re.findall(import_pattern, content)
            if imports:
                last_import = imports[-1]
                content = content.replace(
                    last_import,
                    last_import + 'import UMCommon\n'
                )
                print("  ✅ 添加import语句")
        else:
            print("  ✅ import UMCommon 已存在，跳过（重复检测）")
        
        # 检查是否已有AppDelegate
        if 'class AppDelegate' not in content:
            # 添加AppDelegate类
            app_delegate_code = """
class AppDelegate: NSObject, UIApplicationDelegate {{
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {{
        // 友盟统计SDK初始化
        UMConfigure.initWithAppkey("{app_key}", channel: "{channel}")
        return true
    }}
}}
""".format(app_key=self.app_key, channel=self.channel)
            
            # 在文件末尾添加
            content = content.rstrip() + '\n' + app_delegate_code
            print("  ✅ 创建AppDelegate类")
        else:
            print("  ✅ AppDelegate 类已存在，跳过（重复检测）")
        
        # 添加UIApplicationDelegateAdaptor
        if '@UIApplicationDelegateAdaptor' not in content:
            # 在@main struct内部添加
            struct_pattern = r'(@main\s+struct\s+\w+:\s+App\s*\{)'
            match = re.search(struct_pattern, content)
            if match:
                insert_pos = match.end()
                content = content[:insert_pos] + '\n    @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate\n' + content[insert_pos:]
                print("  ✅ 添加UIApplicationDelegateAdaptor")
        else:
            print("  ✅ @UIApplicationDelegateAdaptor 已存在，跳过（重复检测）")
        
        # 写入文件
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ SwiftUI代码注入成功")
        return True
    
    def _inject_swift_code(self):
        """Swift AppDelegate代码注入"""
        print("  📱 项目类型: Swift")
        
        project_name = self._get_target_name()
        source_dir = os.path.join(self.project_path, project_name)
        
        # 查找AppDelegate.swift
        app_delegate_file = None
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file == 'AppDelegate.swift':
                    app_delegate_file = os.path.join(root, file)
                    break
            if app_delegate_file:
                break
        
        if not app_delegate_file:
            print("  ❌ 未找到AppDelegate.swift")
            return False
        
        print("  📄 找到AppDelegate: {}".format(os.path.basename(app_delegate_file)))
        
        # 备份原文件
        backup_path = app_delegate_file + '.backup'
        shutil.copy2(app_delegate_file, backup_path)
        print("  💾 已备份: {}".format(os.path.basename(backup_path)))
        
        # 读取原文件
        with open(app_delegate_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加import语句
        if 'import UMCommon' not in content:
            import_pattern = r'(import\s+\w+\n)'
            imports = re.findall(import_pattern, content)
            if imports:
                last_import = imports[-1]
                content = content.replace(
                    last_import,
                    last_import + 'import UMCommon\n'
                )
                print("  ✅ 添加import语句")
        else:
            print("  ✅ import UMCommon 已存在，跳过（重复检测）")
        
        # 在didFinishLaunchingWithOptions中添加初始化代码
        init_code = """
        // 友盟统计SDK初始化
        UMConfigure.initWithAppkey("{app_key}", channel: "{channel}")
""".format(app_key=self.app_key, channel=self.channel)
        
        # 查找didFinishLaunchingWithOptions方法
        method_pattern = r'(func application\(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: \[UIApplication\.LaunchOptionsKey: Any\]\?\) -> Bool\s*\{)'
        match = re.search(method_pattern, content)
        
        if match:
            # 幂等检查：初始化代码是否已存在
            if 'UMConfigure.initWithAppkey' in content:
                print("  ✅ 初始化代码已存在，跳过注入（重复检测）")
            else:
                # 在方法开始处添加
                insert_pos = match.end()
                content = content[:insert_pos] + init_code + content[insert_pos:]
                print("  ✅ 添加SDK初始化代码")
        else:
            print("  ⚠️  未找到didFinishLaunchingWithOptions方法")
            return False
        
        # 写入文件
        with open(app_delegate_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ Swift代码注入成功")
        return True
    
    def _inject_objc_code(self):
        """Objective-C AppDelegate代码注入"""
        print("  📱 项目类型: Objective-C")
        
        project_name = self._get_target_name()
        source_dir = os.path.join(self.project_path, project_name)
        
        # 查找AppDelegate.m
        app_delegate_file = None
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file == 'AppDelegate.m':
                    app_delegate_file = os.path.join(root, file)
                    break
            if app_delegate_file:
                break
        
        if not app_delegate_file:
            print("  ❌ 未找到AppDelegate.m")
            return False
        
        print("  📄 找到AppDelegate: {}".format(os.path.basename(app_delegate_file)))
        
        # 备份原文件
        backup_path = app_delegate_file + '.backup'
        shutil.copy2(app_delegate_file, backup_path)
        print("  💾 已备份: {}".format(os.path.basename(backup_path)))
        
        # 读取原文件
        with open(app_delegate_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加import语句
        if '#import <UMCommon/UMCommon.h>' not in content:
            # 在最后一个#import后添加
            import_pattern = r'(#import\s+[^\n]+\n)'
            imports = re.findall(import_pattern, content)
            if imports:
                last_import = imports[-1]
                content = content.replace(
                    last_import,
                    last_import + '#import <UMCommon/UMCommon.h>\n'
                )
                print("  ✅ 添加import语句")
        else:
            print("  ✅ UMCommon import 语句已存在，跳过（重复检测）")
        
        # 在didFinishLaunchingWithOptions中添加初始化代码
        init_code = """
    // 友盟统计SDK初始化
    [UMConfigure initWithAppkey:@"{app_key}" channel:@"{channel}"];
""".format(app_key=self.app_key, channel=self.channel)
        
        # 查找didFinishLaunchingWithOptions方法
        method_pattern = r'(-\s*\(BOOL\)\s*application:\s*\(UIApplication\s*\*\)\s*application\s+didFinishLaunchingWithOptions:\s*\(NSDictionary\s*\*\)\s*launchOptions\s*\{)'
        match = re.search(method_pattern, content)
        
        if match:
            # 幂等检查：初始化代码是否已存在
            if 'UMConfigure initWithAppkey' in content:
                print("  ✅ 初始化代码已存在，跳过注入（重复检测）")
            else:
                # 在方法开始处添加
                insert_pos = match.end()
                content = content[:insert_pos] + init_code + content[insert_pos:]
                print("  ✅ 添加SDK初始化代码")
        else:
            print("  ⚠️  未找到didFinishLaunchingWithOptions方法")
            return False
        
        # 写入文件
        with open(app_delegate_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ Objective-C代码注入成功")
        return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python sdk_integrator.py <project_path> [--app-key KEY] [--channel CHANNEL]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    config = {
        'app_key': 'YOUR_UMENG_APPKEY',
        'channel': 'App Store'
    }
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--app-key' and i + 1 < len(sys.argv):
            config['app_key'] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--channel' and i + 1 < len(sys.argv):
            config['channel'] = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    integrator = SDKIntegrator(project_path, config)
    if integrator.integrate():
        print("\n✅ SDK集成成功")
    else:
        print("\n❌ SDK集成失败")
        sys.exit(1)
