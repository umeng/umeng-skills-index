#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送SDK集成模块
在统计SDK基础上增量集成推送SDK
"""

import os
import re
import shutil
import zipfile
from datetime import datetime
from typing import Tuple, List


class PushSDKIntegrator:
    """友盟推送SDK集成器"""
    
    def __init__(self, project_path: str, app_module: str, config: dict):
        self.project_path = os.path.abspath(project_path)
        self.app_module = app_module
        self.config = config  # {'appkey': str, 'channel': str, 'message_secret': str, 'using_placeholder': bool}
        self.backup_zip = None  # 备份zip文件路径
        self.modified_files = []  # 保留但不再使用
    
    def integrate(self) -> Tuple[bool, str]:
        """
        执行推送SDK增量集成
        
        Returns:
            (是否成功, 详细信息)
        """
        print("\n📦 开始增量集成友盟推送SDK...\n")
        
        # 创建备份zip
        self._create_backup_zip()
        
        try:
            # 1. 添加推送SDK依赖
            if not self._add_push_dependency():
                return False, "推送SDK依赖添加失败"
            
            # 2. 修改初始化代码(传入messageSecret)
            if not self._modify_init_code():
                return False, "初始化代码修改失败"
            
            # 3. 添加AndroidManifest.xml meta-data配置
            if not self._add_manifest_metadata():
                return False, "AndroidManifest.xml配置添加失败"
            
            # 4. 添加推送注册代码
            if not self._add_push_register_code():
                return False, "推送注册代码添加失败"
            
            print("✅ 推送SDK增量集成完成\n")
            return True, "推送SDK集成完成"
            
        except Exception as e:
            print(f"\n❌ 推送SDK集成失败: {str(e)}\n")
            return False, f"推送SDK集成失败: {str(e)}"
    
    def _create_backup_zip(self):
        """创建工程目录的zip备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.dirname(self.project_path)
        project_name = os.path.basename(self.project_path)
        
        self.backup_zip = os.path.join(
            backup_dir,
            f'{project_name}_original_backup_{timestamp}.zip'
        )
        
        print(f"📦 开始备份整个工程目录为zip...")
        print(f"   源目录: {self.project_path}")
        print(f"   备份到: {self.backup_zip}\n")
        
        try:
            # 创建zip文件
            with zipfile.ZipFile(self.backup_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.project_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.dirname(self.project_path))
                        zipf.write(file_path, arcname)
            
            file_size = os.path.getsize(self.backup_zip) / (1024 * 1024)  # MB
            print(f"✅ 工程备份完成 (zip大小: {file_size:.2f} MB)\n")
        except Exception as e:
            print(f"❌ 备份失败: {str(e)}\n")
            raise
    
    def restore_from_backup(self):
        """从zip备份恢复工程目录"""
        if not self.backup_zip or not os.path.exists(self.backup_zip):
            print(f"❌ 未找到备份文件: {self.backup_zip}")
            return False
        
        print(f"🔄 开始从zip备份恢复工程目录...")
        print(f"   备份文件: {self.backup_zip}")
        print(f"   恢复到: {self.project_path}\n")
        
        try:
            # 删除当前工程目录
            if os.path.exists(self.project_path):
                print(f"🗑️  删除当前工程目录...")
                shutil.rmtree(self.project_path)
                print(f"  ✅ 已删除\n")
            
            # 解压备份
            print(f"📂 解压备份文件...")
            with zipfile.ZipFile(self.backup_zip, 'r') as zipf:
                zipf.extractall(os.path.dirname(self.project_path))
            
            print(f"✅ 工程恢复完成\n")
            return True
            
        except Exception as e:
            print(f"❌ 恢复失败: {str(e)}\n")
            return False
    
    def _add_push_dependency(self) -> bool:
        """步骤1: 添加推送SDK依赖"""
        print("步骤 1/3: 添加推送SDK依赖")
        
        # 检查是否使用Version Catalogs
        version_catalog = os.path.join(self.project_path, 'gradle', 'libs.versions.toml')
        
        if os.path.exists(version_catalog):
            return self._add_dependency_version_catalog(version_catalog)
        else:
            return self._add_dependency_traditional()
    
    def _add_dependency_version_catalog(self, version_catalog: str) -> bool:
        """Version Catalogs模式添加依赖"""
        # 检查是否已存在
        with open(version_catalog, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'umeng-push' in content:
            print("  ⚠️  推送SDK依赖已存在,跳过")
            return True
        
        # 解析TOML文件，在现有段内添加
        lines = content.split('\n')
        new_lines = []
        current_section = None
        versions_added = False
        libraries_added = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检测段标题
            if stripped.startswith('[') and not stripped.startswith('[['):
                # 如果前一个段需要添加但还没添加，现在添加
                if current_section == 'versions' and not versions_added:
                    new_lines.append('umeng-push = "+"')
                    versions_added = True
                elif current_section == 'libraries' and not libraries_added:
                    new_lines.append('umeng-push = { module = "com.umeng.umsdk:push", version.ref = "umeng-push" }')
                    libraries_added = True
                
                current_section = stripped.strip('[]').strip()
            
            new_lines.append(line)
            
            # 如果是最后一行，检查是否需要添加
            if i == len(lines) - 1:
                if current_section == 'versions' and not versions_added:
                    new_lines.append('umeng-push = "+"')
                    versions_added = True
                elif current_section == 'libraries' and not libraries_added:
                    new_lines.append('umeng-push = { module = "com.umeng.umsdk:push", version.ref = "umeng-push" }')
                    libraries_added = True
        
        # 如果段不存在，在末尾添加
        if not versions_added:
            new_lines.append('')
            new_lines.append('[versions]')
            new_lines.append('umeng-push = "+"')
        
        if not libraries_added:
            new_lines.append('')
            new_lines.append('[libraries]')
            new_lines.append('umeng-push = { module = "com.umeng.umsdk:push", version.ref = "umeng-push" }')
        
        # 写回文件
        with open(version_catalog, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print("  ✅ 已在libs.versions.toml中添加推送SDK依赖定义")
        
        # 在app/build.gradle.kts中引用
        return self._add_dependency_to_build_gradle('libs.umeng.push')
    
    def _add_dependency_traditional(self) -> bool:
        """传统模式添加依赖"""
        return self._add_dependency_to_build_gradle('com.umeng.umsdk:push:+')
    
    def _add_dependency_to_build_gradle(self, dependency: str) -> bool:
        """在build.gradle中添加依赖"""
        app_gradle_kts = os.path.join(self.project_path, self.app_module, 'build.gradle.kts')
        app_gradle_groovy = os.path.join(self.project_path, self.app_module, 'build.gradle')
        
        gradle_file = None
        if os.path.exists(app_gradle_kts):
            gradle_file = app_gradle_kts
            is_kotlin = True
        elif os.path.exists(app_gradle_groovy):
            gradle_file = app_gradle_groovy
            is_kotlin = False
        else:
            print("  ❌ 未找到app模块的build.gradle文件")
            return False
        
        # 检查是否已存在
        with open(gradle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'com.umeng.umsdk:push' in content or 'umeng-push' in content:
            print("  ⚠️  推送SDK依赖已存在,跳过")
            return True
        
        # 查找dependencies块
        lines = content.split('\n')
        new_lines = []
        in_dependencies = False
        dep_level = 0
        injected = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # 检测进入dependencies块
            if 'dependencies' in line and '{' in line:
                in_dependencies = True
                dep_level = line.count('{') - line.count('}')
                continue
            
            if in_dependencies:
                dep_level += line.count('{') - line.count('}')
                
                # 在dependencies块结束前注入
                if dep_level <= 0:
                    # 添加依赖
                    if 'libs.' in dependency:
                        # Version Catalogs模式
                        indent = '    '
                        dep_line = f'{indent}implementation({dependency})' if is_kotlin else f"{indent}implementation '{dependency}'"
                    else:
                        # 传统模式
                        indent = '    '
                        dep_line = f'{indent}implementation("{dependency}")' if is_kotlin else f"{indent}implementation '{dependency}'"
                    
                    new_lines.insert(-1, dep_line)
                    injected = True
                    in_dependencies = False
        
        if not injected:
            # 如果未找到dependencies块,在文件末尾添加
            print("  ⚠️  未找到dependencies块,在文件末尾添加")
            new_lines.append('')
            new_lines.append('dependencies {')
            if 'libs.' in dependency:
                new_lines.append(f'    implementation({dependency})')
            else:
                new_lines.append(f'    implementation("{dependency}")' if is_kotlin else f"    implementation '{dependency}'")
            new_lines.append('}')
        
        # 写回文件
        with open(gradle_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print(f"  ✅ 已添加推送SDK依赖: {dependency}")
        return True
    
    def _modify_init_code(self) -> bool:
        """步骤2: 修改UMConfigure.init()调用,传入messageSecret"""
        print("\n步骤 2/3: 修改初始化代码")
        
        # 查找Application类
        app_file = self._find_application_file()
        if not app_file:
            print("  ❌ 未找到Application类文件")
            return False
        
        print(f"  📝 修改Application类: {os.path.relpath(app_file, self.project_path)}")
        
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式匹配UMConfigure.init()调用
        # 支持单行和多行格式，匹配: UMConfigure.init(context, appkey, channel, deviceType, null)
        pattern = r'(UMConfigure\.init\s*\([\s\S]*?)(\bnull\b)(\s*(?://[^\n]*)?\s*\))'
        
        if not re.search(pattern, content):
            print("  ❌ 未找到UMConfigure.init()调用或第5个参数不是null")
            print(f"  提示: 请确保第5个参数为null(统计SDK)")
            return False
        
        # 替换null为messageSecret
        message_secret = self.config['message_secret']
        replacement = rf'\1"{message_secret}"\3'
        
        new_content = re.sub(pattern, replacement, content)
        
        # 写回文件
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ 已将UMConfigure.init()第5个参数修改为: \"{message_secret}\"")
        return True
    
    def _add_manifest_metadata(self) -> bool:
        """步骤3: 添加AndroidManifest.xml meta-data配置"""
        print("\n步骤 3/4: 添加AndroidManifest.xml推送配置")
        
        # 查找AndroidManifest.xml
        manifest_path = os.path.join(
            self.project_path,
            self.app_module,
            'src',
            'main',
            'AndroidManifest.xml'
        )
        
        if not os.path.exists(manifest_path):
            print(f"  ❌ 未找到AndroidManifest.xml: {manifest_path}")
            return False
        
        print(f"  📝 修改AndroidManifest.xml: {os.path.relpath(manifest_path, self.project_path)}")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已存在UMENG_MESSAGE_SECRET配置
        if 'UMENG_MESSAGE_SECRET' in content:
            print("  ⚠️  AndroidManifest.xml中已存在推送SDK配置,跳过")
            return True
        
        # 生成meta-data配置
        appkey = self.config['appkey']
        message_secret = self.config['message_secret']
        
        metadata_config = f'''
        <!-- 友盟推送配置 -->
        <meta-data
            android:name="UMENG_APPKEY"
            android:value="{appkey}" />
        <meta-data
            android:name="UMENG_MESSAGE_SECRET"
            android:value="{message_secret}" />
'''
        
        # 在<application>标签后插入meta-data配置
        # 查找<application标签的位置
        import re
        app_pattern = r'(<application[^>]*>)'
        match = re.search(app_pattern, content)
        
        if not match:
            print("  ❌ 未找到<application>标签")
            return False
        
        # 在<application>标签后插入
        insert_pos = match.end()
        new_content = content[:insert_pos] + metadata_config + content[insert_pos:]
        
        # 写回文件
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  ✅ 已添加UMENG_APPKEY和UMENG_MESSAGE_SECRET配置")
        return True
    
    def _add_push_register_code(self) -> bool:
        """步骤3: 添加PushAgent注册代码"""
        print("\n步骤 3/3: 添加推送注册代码")
        
        # 查找Application类
        app_file = self._find_application_file()
        if not app_file:
            print("  ❌ 未找到Application类文件")
            return False
        
        with open(app_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 检测项目语言
        is_kotlin = app_file.endswith('.kt') or app_file.endswith('.kts')
        
        # 生成必要的import语句
        if is_kotlin:
            import_statements = [
                'import com.umeng.message.PushAgent\n',
                'import com.umeng.message.api.UPushRegisterCallback\n',
                'import android.util.Log\n',
            ]
            
            register_code = [
                '\n',
                '        // 注册推送\n',
                '        val mPushAgent = PushAgent.getInstance(context)\n',
                '        mPushAgent.register(object : UPushRegisterCallback {\n',
                '            override fun onSuccess(deviceToken: String) {\n',
                '                Log.i("UmengPush", "deviceToken: " + deviceToken)\n',
                '            }\n',
                '            override fun onFailure(errCode: String, errDesc: String) {\n',
                '                Log.e("UmengPush", "register failed: " + errCode + " " + errDesc)\n',
                '            }\n',
                '        })\n',
            ]
        else:
            import_statements = [
                'import com.umeng.message.PushAgent;\n',
                'import com.umeng.message.api.UPushRegisterCallback;\n',
                'import android.util.Log;\n',
            ]
            
            register_code = [
                '\n',
                '        // 注册推送\n',
                '        PushAgent mPushAgent = PushAgent.getInstance(context);\n',
                '        mPushAgent.register(new UPushRegisterCallback() {\n',
                '            @Override\n',
                '            public void onSuccess(String deviceToken) {\n',
                '                Log.i("UmengPush", "deviceToken: " + deviceToken);\n',
                '            }\n',
                '            @Override\n',
                '            public void onFailure(String s, String s1) {\n',
                '                Log.i("UmengPush", "register failed: " + s + " " + s1);\n',
                '            }\n',
                '        });\n',
            ]
        
        # 先添加import语句（在package声明之后，类声明之前）
        new_lines = []
        imports_added = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # 在最后一个import语句后添加新的import
            if not imports_added and line.startswith('import '):
                # 检查下一行是否还是import
                if i + 1 < len(lines) and not lines[i + 1].startswith('import '):
                    # 这是最后一个import，在后面添加
                    for imp in import_statements:
                        new_lines.append(imp)
                    imports_added = True
        
        # 如果没有import语句，在package声明后添加
        if not imports_added:
            for i, line in enumerate(new_lines):
                if line.startswith('package '):
                    new_lines.insert(i + 1, '\n')
                    for imp in import_statements:
                        new_lines.insert(i + 2, imp)
                    imports_added = True
                    break
        
        # 查找插入位置：在UMConfigure.init()调用结束后立即插入
        # 这样可以确保注册代码和初始化代码在同一个线程中执行
        inserted = False
        in_init_call = False
        paren_count = 0
        final_lines = []
        
        for i, line in enumerate(new_lines):
            final_lines.append(line)
            
            if not inserted and not in_init_call:
                # 检测UMConfigure.init()调用开始
                if 'UMConfigure.init' in line:
                    in_init_call = True
                    # 计算括号数量
                    paren_count += line.count('(') - line.count(')')
                    continue
            
            if in_init_call and not inserted:
                paren_count += line.count('(') - line.count(')')
                
                # 当括号平衡时，说明UMConfigure.init()调用结束
                if paren_count <= 0:
                    # 在这行之后插入推送注册代码
                    final_lines.extend(register_code)
                    inserted = True
                    in_init_call = False
        
        if not inserted:
            print("  ❌ 未找到UMConfigure.init()调用")
            return False
        
        # 写回文件
        with open(app_file, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)
        
        print("  ✅ 已添加PushAgent注册代码和必要的import语句")
        return True
    
    def _find_application_file(self) -> str:
        """查找Application类文件"""
        src_dir = os.path.join(self.project_path, self.app_module, 'src', 'main', 'java')
        kotlin_dir = os.path.join(self.project_path, self.app_module, 'src', 'main', 'kotlin')
        
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
                                return file_path
                        except:
                            continue
        
        return None
