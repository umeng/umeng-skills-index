# -*- coding: utf-8 -*-
"""
iOS APM SDK集成 - SDK集成模块
负责Podfile修改（添加UMAPM）、pod install执行、APM初始化代码注入
关键差异：在已存在的 UMConfigure.initWithAppkey 调用之前注入APM配置
"""

import os
import re
import shutil
import subprocess
import sys


class SDKIntegrator:
    """iOS APM SDK集成器"""
    
    def __init__(self, project_path, config):
        """
        初始化APM SDK集成器
        
        Args:
            project_path: iOS项目路径
            config: 配置字典 {'app_key', 'channel', 'target'}
        """
        self.project_path = project_path
        self.config = config
        self.target = config.get('target')
        
        # APM Pod依赖
        self.apm_pod = "pod 'UMAPM'"
    
    def integrate(self):
        """
        执行APM SDK集成
        
        Returns:
            bool: 集成是否成功
        """
        print("\n" + "="*60)
        print("📦 开始APM SDK集成...")
        print("="*60 + "\n")
        
        # 步骤1: 修改Podfile（添加UMAPM）
        if not self._update_podfile():
            return False
        
        # 步骤2: 执行pod install
        if not self._run_pod_install():
            return False
        
        # 步骤3: 验证UMAPM Pod已安装
        if not self._verify_umapm_installed():
            return False
        
        # 步骤4: 修补UMAPM modulemap（解决Swift项目编译问题）
        self._patch_umapm_modulemap()
        
        # 步骤5: 修复项目配置（Sandbox权限问题）
        self._fix_project_settings()
        
        # 步骤6: 注入APM初始化代码
        if not self._inject_apm_code():
            return False
        
        print("\n✅ APM SDK集成完成\n")
        return True
    
    def _update_podfile(self):
        """修改Podfile添加UMAPM依赖"""
        print("📝 修改Podfile（添加UMAPM）...")
        
        podfile_path = os.path.join(self.project_path, 'Podfile')
        
        if not os.path.exists(podfile_path):
            print("  ❌ Podfile不存在，APM SDK需要在统计SDK之后集成")
            print("  请先运行 ios-analytics-integration Skill")
            return False
        
        with open(podfile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 幂等检查：若Podfile已包含UMAPM则跳过
        if 'UMAPM' in content:
            print("  ⚠️  Podfile已包含UMAPM依赖，跳过添加")
            return True
        
        # 获取target名称
        target_name = self._get_target_name()
        
        # 在target块中添加UMAPM依赖
        # 策略：在UMCommon/UMDevice之后添加
        pattern = r"(pod\s+['\"]UMCommon['\"][^\n]*\n)"
        match = re.search(pattern, content)
        
        if match:
            # 在UMCommon行后面添加UMAPM
            insert_pos = match.end()
            indent = '  '  # 保持缩进一致
            
            # 检测原文缩进
            line_start = content.rfind('\n', 0, match.start()) + 1
            original_line = content[line_start:match.start()]
            if original_line:
                indent = original_line  # 使用相同前缀空白
            
            new_content = content[:insert_pos] + "  # 友盟APM性能监控SDK\n  {}\n".format(self.apm_pod) + content[insert_pos:]
            
            with open(podfile_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("  ✅ Podfile已添加 pod 'UMAPM'")
        else:
            # 没找到UMCommon行，尝试在target块末尾添加
            target_pattern = r"(target\s+['\"]{}['\"]\s+do\s+)(.*?)(\nend)".format(
                re.escape(target_name)
            )
            match = re.search(target_pattern, content, re.DOTALL)
            
            if match:
                new_content = (content[:match.end(2)] + 
                             '\n\n  # 友盟APM性能监控SDK\n  ' + self.apm_pod + 
                             content[match.end(2):])
                
                with open(podfile_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("  ✅ Podfile已添加 pod 'UMAPM'（在target块末尾）")
            else:
                # 最后手段：追加到文件末尾
                with open(podfile_path, 'a', encoding='utf-8') as f:
                    f.write("\n  # 友盟APM性能监控SDK\n  {}\n".format(self.apm_pod))
                
                print("  ⚠️  追加 pod 'UMAPM' 到Podfile末尾")
        
        return True
    
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
                    print("  ✅ Workspace: {}".format(workspace_files[0]))
                
                return True
            else:
                print("  ❌ pod install失败")
                print("\n错误信息:")
                if result.stderr:
                    for line in result.stderr.split('\n')[-20:]:
                        if line.strip():
                            print("    {}".format(line))
                if result.stdout:
                    for line in result.stdout.split('\n')[-10:]:
                        if line.strip() and ('error' in line.lower() or 'Error' in line):
                            print("    {}".format(line))
                return False
                
        except subprocess.TimeoutExpired:
            print("  ❌ pod install超时（超过5分钟）")
            return False
        except Exception as e:
            print("  ❌ pod install出错: {}".format(str(e)))
            return False
    
    def _verify_umapm_installed(self):
        """验证UMAPM Pod是否正确安装"""
        print("\n🔍 验证UMAPM Pod...")
        
        pods_dir = os.path.join(self.project_path, 'Pods')
        
        if not os.path.exists(pods_dir):
            print("  ❌ Pods目录不存在")
            return False
        
        umapm_dir = os.path.join(pods_dir, 'UMAPM')
        if os.path.exists(umapm_dir):
            contents = os.listdir(umapm_dir)
            if len(contents) > 0:
                print("  ✅ UMAPM SDK已安装（Pods/UMAPM 存在）")
                return True
            else:
                print("  ❌ Pods/UMAPM 目录为空")
                return False
        else:
            print("  ❌ Pods/UMAPM 目录不存在")
            print("\n💡 可能的原因:")
            print("  1. Podfile中UMAPM拼写有误")
            print("  2. CocoaPods源无法访问")
            print("  3. 网络问题导致下载失败")
            print("\n🔧 解决建议:")
            print("  1. 运行 'pod repo update' 更新源")
            print("  2. 删除Pods目录后重新运行 'pod install'")
            return False
    
    def _fix_project_settings(self):
        """修复项目Build Settings中的Sandbox问题"""
        print("\n🔧 修复项目配置...")
        
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
            
            if 'ENABLE_USER_SCRIPT_SANDBOXING' in content:
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
            
            if not modified:
                print("  ℹ️  项目配置无需修改")
        else:
            print("  ⚠️  未找到project.pbxproj文件")
    
    def _inject_apm_code(self):
        """注入APM初始化代码"""
        print("\n💉 注入APM初始化代码...")
        
        project_type = self._detect_project_type()
        
        if project_type == 'swiftui':
            return self._inject_swift_apm_code()
        elif project_type == 'swift':
            return self._inject_swift_apm_code()
        elif project_type == 'objc':
            return self._inject_objc_apm_code()
        else:
            print("  ❌ 无法识别项目类型")
            return False
    
    def _detect_project_type(self):
        """检测项目类型"""
        project_name = self._get_target_name()
        source_dir = os.path.join(self.project_path, project_name)
        
        if not os.path.exists(source_dir):
            for item in os.listdir(self.project_path):
                item_path = os.path.join(self.project_path, item)
                if os.path.isdir(item_path) and not item.endswith(
                    ('.xcodeproj', '.xcworkspace', 'Pods', 'backups')
                ):
                    source_dir = item_path
                    break
        
        if not os.path.exists(source_dir):
            return 'unknown'
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.swift'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if '@main' in content and 'App' in content:
                            return 'swiftui'
                        elif 'AppDelegate' in file and 'UIApplicationDelegate' in content:
                            return 'swift'
                    except (IOError, UnicodeDecodeError):
                        continue
                elif file.endswith('.m') and 'AppDelegate' in file:
                    return 'objc'
        
        return 'unknown'
    
    def _find_app_delegate_swift(self):
        """查找Swift AppDelegate文件"""
        project_name = self._get_target_name()
        source_dir = os.path.join(self.project_path, project_name)
        
        if not os.path.exists(source_dir):
            for item in os.listdir(self.project_path):
                item_path = os.path.join(self.project_path, item)
                if os.path.isdir(item_path) and not item.endswith(
                    ('.xcodeproj', '.xcworkspace', 'Pods', 'backups')
                ):
                    source_dir = item_path
                    break
        
        if not os.path.exists(source_dir):
            return None
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.swift'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # 找到包含UMConfigure.initWithAppkey调用的文件
                        if 'UMConfigure.initWithAppkey' in content:
                            return file_path
                    except (IOError, UnicodeDecodeError):
                        continue
        
        return None
    
    def _find_app_delegate_objc(self):
        """查找Objective-C AppDelegate文件"""
        project_name = self._get_target_name()
        source_dir = os.path.join(self.project_path, project_name)
        
        if not os.path.exists(source_dir):
            for item in os.listdir(self.project_path):
                item_path = os.path.join(self.project_path, item)
                if os.path.isdir(item_path) and not item.endswith(
                    ('.xcodeproj', '.xcworkspace', 'Pods', 'backups')
                ):
                    source_dir = item_path
                    break
        
        if not os.path.exists(source_dir):
            return None
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.m'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if '[UMConfigure initWithAppkey' in content:
                            return file_path
                    except (IOError, UnicodeDecodeError):
                        continue
        
        return None
    
    def _inject_swift_apm_code(self):
        """Swift/SwiftUI项目APM代码注入"""
        print("  📱 项目类型: Swift")
        
        # 查找包含UMConfigure.initWithAppkey调用的Swift文件
        app_delegate_file = self._find_app_delegate_swift()
        
        if not app_delegate_file:
            print("  ❌ 未找到包含UMConfigure.initWithAppkey的Swift文件")
            return False
        
        print("  📄 找到目标文件: {}".format(os.path.basename(app_delegate_file)))
        
        # 备份原文件
        backup_path = app_delegate_file + '.apm_backup'
        shutil.copy2(app_delegate_file, backup_path)
        print("  💾 已备份: {}".format(os.path.basename(backup_path)))
        
        # 读取原文件
        with open(app_delegate_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 幂等检查：若已包含APM配置则跳过
        if 'UMAPMConfig' in content or 'UMCrashConfigure' in content:
            print("  ⚠️  源码已包含APM配置，跳过注入")
            return True
        
        # A. 注入import语句
        if 'import UMAPM' not in content:
            import_pattern = r'(import\s+\w+\n)'
            imports = re.findall(import_pattern, content)
            if imports:
                last_import = imports[-1]
                content = content.replace(
                    last_import,
                    last_import + 'import UMAPM\n',
                    1
                )
                print("  ✅ 添加 import UMAPM")
        else:
            print("  ✅ import UMAPM 已存在，跳过（重复检测）")
        
        # B. 在UMConfigure.initWithAppkey之前注入APM配置
        apm_config_code = (
            "\n        // 友盟APM性能监控配置（必须在UMConfigure.initWithAppkey之前调用）\n"
            "        let config = UMAPMConfig.default()\n"
            "        config.crashAndBlockMonitorEnable = true\n"
            "        config.launchMonitorEnable = true\n"
            "        config.memMonitorEnable = true\n"
            "        config.oomMonitorEnable = true\n"
            "        config.networkEnable = true\n"
            "        config.javaScriptBridgeEnable = true\n"
            "        config.pageMonitorEnable = true\n"
            "        config.logCollectEnable = true\n"
            "        UMCrashConfigure.setAPMConfig(config)\n"
        )
        
        # 查找UMConfigure.initWithAppkey调用位置
        init_pattern = r'(\s*)(UMConfigure\.initWithAppkey\()'
        match = re.search(init_pattern, content)
        
        if match:
            insert_pos = match.start()
            content = content[:insert_pos] + apm_config_code + content[insert_pos:]
            print("  ✅ 在UMConfigure.initWithAppkey之前注入APM配置")
        else:
            print("  ❌ 未找到UMConfigure.initWithAppkey调用")
            return False
        
        # 写入文件
        with open(app_delegate_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ Swift APM代码注入成功")
        return True
    
    def _inject_objc_apm_code(self):
        """Objective-C项目APM代码注入"""
        print("  📱 项目类型: Objective-C")
        
        # 查找包含[UMConfigure initWithAppkey:]调用的.m文件
        app_delegate_file = self._find_app_delegate_objc()
        
        if not app_delegate_file:
            print("  ❌ 未找到包含[UMConfigure initWithAppkey:]的.m文件")
            return False
        
        print("  📄 找到目标文件: {}".format(os.path.basename(app_delegate_file)))
        
        # 备份原文件
        backup_path = app_delegate_file + '.apm_backup'
        shutil.copy2(app_delegate_file, backup_path)
        print("  💾 已备份: {}".format(os.path.basename(backup_path)))
        
        # 读取原文件
        with open(app_delegate_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 幂等检查
        if 'UMAPMConfig' in content or 'UMCrashConfigure' in content:
            print("  ⚠️  源码已包含APM配置，跳过注入")
            return True
        
        # A. 注入import语句
        if '#import <UMAPM/UMCrashConfigure.h>' not in content:
            import_pattern = r'(#import\s+[^\n]+\n)'
            imports = re.findall(import_pattern, content)
            if imports:
                last_import = imports[-1]
                content = content.replace(
                    last_import,
                    last_import + '#import <UMAPM/UMAPMConfig.h>\n#import <UMAPM/UMCrashConfigure.h>\n',
                    1
                )
                print("  ✅ 添加 #import <UMAPM/UMAPMConfig.h>")
                print("  ✅ 添加 #import <UMAPM/UMCrashConfigure.h>")
        else:
            print("  ✅ UMAPM import 语句已存在，跳过（重复检测）")
        
        # B. 在[UMConfigure initWithAppkey:]之前注入APM配置
        apm_config_code = (
            "\n    // 友盟APM性能监控配置（必须在[UMConfigure initWithAppkey:]之前调用）\n"
            "    UMAPMConfig *config = [UMAPMConfig defaultConfig];\n"
            "    config.crashAndBlockMonitorEnable = YES;\n"
            "    config.launchMonitorEnable = YES;\n"
            "    config.memMonitorEnable = YES;\n"
            "    config.oomMonitorEnable = YES;\n"
            "    config.networkEnable = YES;\n"
            "    config.javaScriptBridgeEnable = YES;\n"
            "    config.pageMonitorEnable = YES;\n"
            "    config.logCollectEnable = YES;\n"
            "    [UMCrashConfigure setAPMConfig:config];\n"
        )
        
        # 查找[UMConfigure initWithAppkey:]调用位置
        init_pattern = r'(\s*)(\[UMConfigure\s+initWithAppkey:)'
        match = re.search(init_pattern, content)
        
        if match:
            insert_pos = match.start()
            content = content[:insert_pos] + apm_config_code + content[insert_pos:]
            print("  ✅ 在[UMConfigure initWithAppkey:]之前注入APM配置")
        else:
            print("  ❌ 未找到[UMConfigure initWithAppkey:]调用")
            return False
        
        # 写入文件
        with open(app_delegate_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ Objective-C APM代码注入成功")
        return True
    
    def _patch_umapm_modulemap(self):
        """修补UMAPM xcframework缺失的module.modulemap（解决Swift项目import UMAPM编译失败）"""
        print("\n🔧 检查UMAPM modulemap...")
        
        pods_dir = os.path.join(self.project_path, 'Pods')
        if not os.path.exists(pods_dir):
            print("  ⚠️  Pods目录不存在，跳过modulemap修补")
            return
        
        umapm_dir = os.path.join(pods_dir, 'UMAPM')
        if not os.path.exists(umapm_dir):
            print("  ⚠️  Pods/UMAPM目录不存在，跳过modulemap修补")
            return
        
        # 定位xcframework路径：Pods/UMAPM/UMAPM_*/UMAPM.xcframework/
        xcframework_path = None
        for item in os.listdir(umapm_dir):
            item_path = os.path.join(umapm_dir, item)
            if os.path.isdir(item_path) and item.startswith('UMAPM_'):
                candidate = os.path.join(item_path, 'UMAPM.xcframework')
                if os.path.exists(candidate):
                    xcframework_path = candidate
                    break
        
        if not xcframework_path:
            print("  ⚠️  未找到UMAPM.xcframework路径，跳过modulemap修补")
            return
        
        patched_count = 0
        skipped_count = 0
        
        # 遍历xcframework下的每个架构目录
        for arch_dir in os.listdir(xcframework_path):
            arch_path = os.path.join(xcframework_path, arch_dir)
            if not os.path.isdir(arch_path):
                continue
            
            framework_path = os.path.join(arch_path, 'UMAPM.framework')
            if not os.path.exists(framework_path):
                continue
            
            modulemap_path = os.path.join(framework_path, 'Modules', 'module.modulemap')
            
            # 若已存在则跳过
            if os.path.exists(modulemap_path):
                print(f"  ✅ module.modulemap 已存在，无需修补")
                skipped_count += 1
                continue
            
            # 扫描Headers目录获取所有.h文件名
            headers_dir = os.path.join(framework_path, 'Headers')
            if not os.path.exists(headers_dir):
                continue
            
            header_files = sorted([f for f in os.listdir(headers_dir) if f.endswith('.h')])
            if not header_files:
                continue
            
            # 生成modulemap内容
            header_lines = '\n'.join('  header "{}"'.format(h) for h in header_files)
            modulemap_content = 'framework module UMAPM {{\n{}\n  export *\n}}\n'.format(header_lines)
            
            # 创建Modules目录并写入modulemap
            modules_dir = os.path.join(framework_path, 'Modules')
            os.makedirs(modules_dir, exist_ok=True)
            
            with open(modulemap_path, 'w', encoding='utf-8') as f:
                f.write(modulemap_content)
            
            patched_count += 1
        
        if patched_count > 0:
            print("  ✅ 已修补{}个架构slice的module.modulemap".format(patched_count))
        elif skipped_count > 0:
            print("  ℹ️  所有架构slice已存在modulemap，无需修补")
        else:
            print("  ⚠️  未找到需要修补的UMAPM.framework目录")
    
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


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python sdk_integrator.py <project_path> [--target TARGET]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    config = {
        'target': None
    }
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--target' and i + 1 < len(sys.argv):
            config['target'] = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    integrator = SDKIntegrator(project_path, config)
    if integrator.integrate():
        print("\n✅ APM SDK集成成功")
    else:
        print("\n❌ APM SDK集成失败")
        sys.exit(1)
