#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APM SDK集成模块
在统计SDK基础上增量集成APM性能监控SDK
"""

import os
import re
import shutil
import zipfile
from datetime import datetime
from typing import Tuple, List, Optional


class APMSDKIntegrator:
    """友盟APM SDK集成器"""

    def __init__(self, project_path: str, app_module: str, config: dict):
        self.project_path = os.path.abspath(project_path)
        self.app_module = app_module
        self.config = config  # {'appkey': str, 'channel': str, 'using_placeholder': bool}
        self.backup_zip = None  # 备份zip文件路径

    def integrate(self) -> Tuple[bool, str]:
        """
        执行APM SDK增量集成（4个子步骤）

        Returns:
            (是否成功, 详细信息)
        """
        print("\n📦 开始增量集成友盟APM SDK...\n")

        # 若备份已由外部（main.py step4）创建，则跳过
        if not self.backup_zip:
            self._create_backup_zip()

        try:
            # 1. 添加APM SDK依赖
            if not self._add_apm_dependency():
                return False, "APM SDK依赖添加失败"

            # 2. 添加权限配置
            if not self._add_permissions():
                return False, "权限配置添加失败"

            # 3. 添加混淆规则
            if not self._add_proguard_rules():
                return False, "混淆规则添加失败"

            # 4. 添加APM初始化代码
            if not self._add_apm_init_code():
                return False, "APM初始化代码添加失败"

            print("✅ APM SDK增量集成完成\n")
            return True, "APM SDK集成完成"

        except Exception as e:
            print(f"\n❌ APM SDK集成失败: {str(e)}\n")
            return False, f"APM SDK集成失败: {str(e)}"

    # ─── 备份与恢复 ──────────────────────────────────────────────────

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

    # ─── 步骤1: 添加APM SDK依赖 ──────────────────────────────────────

    def _add_apm_dependency(self) -> bool:
        """步骤1: 添加APM SDK依赖"""
        print("步骤 1/4: 添加APM SDK依赖")

        # 检查是否使用Version Catalogs
        version_catalog = os.path.join(self.project_path, 'gradle', 'libs.versions.toml')

        if os.path.exists(version_catalog):
            return self._add_dependency_version_catalog(version_catalog)
        else:
            return self._add_dependency_traditional()

    def _add_dependency_version_catalog(self, version_catalog: str) -> bool:
        """Version Catalogs模式添加依赖"""
        with open(version_catalog, 'r', encoding='utf-8') as f:
            content = f.read()

        # 幂等性检查
        if 'umeng-apm' in content:
            print("  ⚠️  APM SDK依赖已存在，跳过")
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
                    new_lines.append('umeng-apm = "+"')
                    versions_added = True
                elif current_section == 'libraries' and not libraries_added:
                    new_lines.append('umeng-apm = { module = "com.umeng.umsdk:apm", version.ref = "umeng-apm" }')
                    libraries_added = True

                current_section = stripped.strip('[]').strip()

            new_lines.append(line)

            # 如果是最后一行，检查是否需要添加
            if i == len(lines) - 1:
                if current_section == 'versions' and not versions_added:
                    new_lines.append('umeng-apm = "+"')
                    versions_added = True
                elif current_section == 'libraries' and not libraries_added:
                    new_lines.append('umeng-apm = { module = "com.umeng.umsdk:apm", version.ref = "umeng-apm" }')
                    libraries_added = True

        # 如果段不存在，在末尾添加
        if not versions_added:
            new_lines.append('')
            new_lines.append('[versions]')
            new_lines.append('umeng-apm = "+"')

        if not libraries_added:
            new_lines.append('')
            new_lines.append('[libraries]')
            new_lines.append('umeng-apm = { module = "com.umeng.umsdk:apm", version.ref = "umeng-apm" }')

        with open(version_catalog, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        print("  ✅ 已在libs.versions.toml中添加APM SDK依赖定义")

        # 在app/build.gradle中引用
        return self._add_dependency_to_build_gradle('libs.umeng.apm')

    def _add_dependency_traditional(self) -> bool:
        """传统模式添加依赖"""
        return self._add_dependency_to_build_gradle('com.umeng.umsdk:apm:+')

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

        with open(gradle_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 幂等性检查
        if 'com.umeng.umsdk:apm' in content or 'umeng-apm' in content:
            print("  ⚠️  APM SDK依赖已存在，跳过")
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
                    if 'libs.' in dependency:
                        indent = '    '
                        dep_line = f'{indent}implementation({dependency})' if is_kotlin else f"{indent}implementation '{dependency}'"
                    else:
                        indent = '    '
                        dep_line = f'{indent}implementation("{dependency}")' if is_kotlin else f"{indent}implementation '{dependency}'"

                    new_lines.insert(-1, dep_line)
                    injected = True
                    in_dependencies = False

        if not injected:
            print("  ⚠️  未找到dependencies块，在文件末尾添加")
            new_lines.append('')
            new_lines.append('dependencies {')
            if 'libs.' in dependency:
                new_lines.append(f'    implementation({dependency})')
            else:
                new_lines.append(f'    implementation("{dependency}")' if is_kotlin else f"    implementation '{dependency}'")
            new_lines.append('}')

        with open(gradle_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        print(f"  ✅ 已添加APM SDK依赖: {dependency}")
        return True

    # ─── 步骤2: 添加权限 ─────────────────────────────────────────────

    def _add_permissions(self) -> bool:
        """步骤2: 添加权限配置到AndroidManifest.xml"""
        print("\n步骤 2/4: 配置权限")

        manifest_path = os.path.join(
            self.project_path,
            self.app_module,
            'src', 'main',
            'AndroidManifest.xml'
        )

        if not os.path.exists(manifest_path):
            print(f"  ❌ 未找到AndroidManifest.xml\n")
            return False

        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 需要添加的3个权限
        required_permissions = [
            ('android.permission.ACCESS_NETWORK_STATE', '<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />'),
            ('android.permission.ACCESS_WIFI_STATE', '<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />'),
            ('android.permission.INTERNET', '<uses-permission android:name="android.permission.INTERNET" />'),
        ]

        # 过滤出尚未添加的权限
        missing_permissions = []
        for perm_name, perm_line in required_permissions:
            if perm_name not in content:
                missing_permissions.append(perm_line)

        if not missing_permissions:
            print("  ⚠️  所有权限已存在，跳过")
            # 仍需配置 extractNativeLibs 属性
            if not self._add_extract_native_libs():
                print("  ⚠️  extractNativeLibs 配置失败，但不阻塞集成")
            return True

        # 在<application>标签前插入缺失的权限
        lines = content.split('\n')
        new_lines = []
        inserted = False

        for i, line in enumerate(lines):
            if '<application' in line and not inserted:
                new_lines.append('')
                for perm in missing_permissions:
                    new_lines.append(f'    {perm}')
                    print(f"  ✅ 添加权限: {perm}")
                new_lines.append('')
                inserted = True
            new_lines.append(line)

        if not inserted:
            print("  ❌ 未找到<application>标签\n")
            return False

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        print()

        # 配置 extractNativeLibs 属性
        if not self._add_extract_native_libs():
            print("  ⚠️  extractNativeLibs 配置失败，但不阻塞集成")

        return True

    # ─── 步骤2.5: 检测AGP版本 ────────────────────────────────────────

    def _detect_agp_version(self) -> Optional[int]:
        """检测项目的 Android Gradle Plugin 主版本号
            
        Returns:
            AGP 主版本号（如 7, 8），检测失败返回 None
        """
        # 1. 尝试从根 build.gradle 中检测
        for ext in ['build.gradle', 'build.gradle.kts']:
            root_gradle = os.path.join(self.project_path, ext)
            if os.path.exists(root_gradle):
                with open(root_gradle, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                # 过滤注释行（// 开头、/* 开头、* 开头）
                effective_lines = []
                for line in lines:
                    s = line.strip()
                    if s.startswith('//') or s.startswith('/*') or s.startswith('*'):
                        continue
                    effective_lines.append(line)
                content = ''.join(effective_lines)
                # 匹配 com.android.tools.build:gradle:X.Y.Z
                match = re.search(r'com\.android\.tools\.build:gradle:(\d+)', content)
                if match:
                    return int(match.group(1))
                # 匹配 id("com.android.application") version "X.Y.Z" 或类似
                match = re.search(r'com\.android\.\w+["\']?\s*version\s*["\'](\d+)', content)
                if match:
                    return int(match.group(1))
            
        # 2. 尝试从 Version Catalogs (libs.versions.toml) 中检测
        toml_path = os.path.join(self.project_path, 'gradle', 'libs.versions.toml')
        if os.path.exists(toml_path):
            with open(toml_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # 过滤注释行（# 开头）
            effective_lines = []
            for line in lines:
                s = line.strip()
                if s.startswith('#'):
                    continue
                effective_lines.append(line)
            content = ''.join(effective_lines)
            # 匹配 agp = "X.Y.Z" 或 androidGradlePlugin = "X.Y.Z"
            match = re.search(r'(?:agp|android[Gg]radle[Pp]lugin)\s*=\s*["\'](\d+)', content)
            if match:
                return int(match.group(1))
            
        return None

    # ─── 步骤2.5: 配置native库提取（AGP版本感知） ─────────────────────

    def _add_extract_native_libs(self) -> bool:
        """配置native库提取：AGP 8.x+用build.gradle，AGP 7.x及以下用AndroidManifest.xml"""
        print("\n  📋 配置 native 库提取")

        agp_version = self._detect_agp_version()

        if agp_version is None:
            print("    ⚠️ 未能检测到 AGP 版本，使用保守策略（AndroidManifest.xml 方式）")
            return self._inject_extract_native_libs_manifest()

        if agp_version < 8:
            # AGP 7.x 及以下：AndroidManifest.xml 方式
            return self._inject_extract_native_libs_manifest()
        else:
            # AGP 8.x+：build.gradle 方式（推荐）
            return self._inject_legacy_packaging_gradle()

    def _inject_extract_native_libs_manifest(self) -> bool:
        """AGP 7.x：在AndroidManifest.xml的<application>标签中注入extractNativeLibs属性"""
        print("    → AGP < 8.0，使用 AndroidManifest.xml 方式")
        
        manifest_path = os.path.join(
            self.project_path, self.app_module,
            'src', 'main', 'AndroidManifest.xml'
        )

        if not os.path.exists(manifest_path):
            print("    ❌ 未找到AndroidManifest.xml")
            return False

        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 幂等性检查
        if 'extractNativeLibs' in content:
            print("    ⚠️  extractNativeLibs 已配置，跳过")
            return True

        # 找到 <application 标签行，注入属性
        lines = content.split('\n')
        injected = False
        for i, line in enumerate(lines):
            if '<application' in line and 'extractNativeLibs' not in line:
                lines[i] = line.replace('<application', '<application\n        android:extractNativeLibs="true"', 1)
                injected = True
                break

        if not injected:
            print("    ❌ 未找到 <application 标签")
            return False

        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print("    ✅ 已添加 android:extractNativeLibs=\"true\"")
        return True

    def _inject_legacy_packaging_gradle(self) -> bool:
        """AGP 8.x+：在app/build.gradle的android{}块内注入packaging配置"""
        print("    → AGP >= 8.0（或未知），使用 build.gradle 方式")
        
        # 查找 app 模块的 build.gradle
        app_gradle_kts = os.path.join(self.project_path, self.app_module, 'build.gradle.kts')
        app_gradle_groovy = os.path.join(self.project_path, self.app_module, 'build.gradle')
        
        if os.path.exists(app_gradle_kts):
            gradle_file = app_gradle_kts
        elif os.path.exists(app_gradle_groovy):
            gradle_file = app_gradle_groovy
        else:
            print("    ❌ 未找到 app 模块 build.gradle")
            return False

        with open(gradle_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 幂等性检查
        if 'useLegacyPackaging' in content:
            print("    ⚠️  useLegacyPackaging 已配置，跳过")
            return True

        # 使用括号计数法定位 android {} 块的结束位置
        lines = content.split('\n')
        android_start = -1
        brace_count = 0
        android_end = -1

        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            if android_start == -1:
                # 匹配 android { 或 android{
                if re.match(r'^android\s*\{', stripped):
                    android_start = i
                    brace_count = stripped.count('{') - stripped.count('}')
                # 匹配分行写法: android 单独一行，下一行是 {
                elif stripped == 'android' and i + 1 < len(lines) and '{' in lines[i + 1]:
                    android_start = i
                    i += 1
                    brace_count = lines[i].strip().count('{') - lines[i].strip().count('}')
            else:
                brace_count += stripped.count('{') - stripped.count('}')

            if android_start != -1 and brace_count <= 0:
                android_end = i
                break
            i += 1

        if android_end == -1:
            print("    ❌ 未找到 android {} 块")
            return False

        # 在 android {} 块的闭合 } 所在行之前插入 packaging 配置
        packaging_block = [
            '',
            '    packaging {',
            '        jniLibs {',
            '            useLegacyPackaging = true',
            '        }',
            '    }',
        ]

        new_lines = lines[:android_end] + packaging_block + lines[android_end:]

        with open(gradle_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        print("    ✅ 已添加 packaging.jniLibs.useLegacyPackaging = true")
        return True

    # ─── 步骤3: 添加混淆规则 ─────────────────────────────────────────

    def _add_proguard_rules(self) -> bool:
        """步骤3: 添加混淆规则到proguard-rules.pro"""
        print("步骤 3/4: 配置混淆规则")

        proguard_path = os.path.join(
            self.project_path,
            self.app_module,
            'proguard-rules.pro'
        )

        # 如果文件不存在，创建它
        if not os.path.exists(proguard_path):
            with open(proguard_path, 'w', encoding='utf-8') as f:
                f.write('# Add project specific ProGuard rules here.\n')
            print("  📝 创建proguard-rules.pro")

        with open(proguard_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 需要添加的混淆规则及其检测标记
        rules_to_add = []

        rule_checks = [
            ('com.umeng.**', '-keep class com.umeng.** { *; }'),
            ('com.uc.**', '-keep class com.uc.** { *; }'),
            ('com.efs.**', '-keep class com.efs.** { *; }'),
            ('public <init>(org.json.JSONObject)', '-keepclassmembers class * {\n    public <init>(org.json.JSONObject);\n}'),
            ('public static **[] values()', '-keepclassmembers enum * {\n    public static **[] values();\n    public static ** valueOf(java.lang.String);\n}'),
        ]

        for check_str, rule in rule_checks:
            if check_str not in content:
                rules_to_add.append(rule)

        if not rules_to_add:
            print("  ⚠️  混淆规则已存在，跳过")
            return True

        # 构建追加内容
        proguard_block = '\n# ========== 友盟APM SDK混淆规则 ==========\n'
        proguard_block += '\n'.join(rules_to_add)
        proguard_block += '\n'

        with open(proguard_path, 'a', encoding='utf-8') as f:
            f.write(proguard_block)

        print("  ✅ 已添加友盟APM SDK混淆规则\n")
        return True

    # ─── 步骤4: 添加APM初始化代码 ────────────────────────────────────

    def _add_apm_init_code(self) -> bool:
        """步骤4: 在Application类中注入UMCrash.initConfig()代码（必须在UMConfigure.init之前）"""
        print("步骤 4/4: 添加APM初始化代码")

        # 查找Application类文件
        app_file = self._find_application_file()
        if not app_file:
            print("  ❌ 未找到Application类文件")
            return False

        print(f"  📝 修改Application类: {os.path.relpath(app_file, self.project_path)}")

        with open(app_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 检测语言
        is_kotlin = app_file.endswith('.kt') or app_file.endswith('.kts')

        # 幂等性检查
        content_str = ''.join(lines)
        if 'UMCrash.initConfig' in content_str:
            print("  ⚠️  UMCrash.initConfig已存在，跳过")
            return True

        # 前置依赖检查：UMConfigure.init 是否已集成
        if 'UMConfigure.init' not in content_str:
            print("  ⚠️  未检测到 UMConfigure.init 调用，建议先通过 android-analytics-integration 集成统计 SDK")

        # 生成import语句
        if is_kotlin:
            import_statements = [
                'import android.os.Bundle\n',
                'import com.umeng.umcrash.UMCrash\n',
            ]
        else:
            import_statements = [
                'import android.os.Bundle;\n',
                'import com.umeng.umcrash.UMCrash;\n',
            ]

        # 生成初始化代码
        if is_kotlin:
            init_code = [
                '\n',
                '        // APM性能监控配置（必须在UMConfigure.init之前调用）\n',
                '        val bundle = Bundle().apply {\n',
                '            putBoolean(UMCrash.KEY_ENABLE_CRASH_JAVA, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_CRASH_NATIVE, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_ANR, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_PA, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_LAUNCH, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_MEM, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_NET, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_PAGE, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_POWER, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_CODE_LOG, true)\n',
                '            putBoolean(UMCrash.KEY_ENABLE_MEMLEAK, true)\n',
                '            putLong(UMCrash.KEY_PA_TIMEOUT_TIME, 2000L)\n',
                '        }\n',
                '        UMCrash.initConfig(bundle)\n',
                '\n',
            ]
        else:
            init_code = [
                '\n',
                '        // APM性能监控配置（必须在UMConfigure.init之前调用）\n',
                '        Bundle bundle = new Bundle();\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_CRASH_JAVA, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_CRASH_NATIVE, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_ANR, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_PA, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_LAUNCH, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_MEM, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_NET, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_PAGE, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_POWER, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_CODE_LOG, true);\n',
                '        bundle.putBoolean(UMCrash.KEY_ENABLE_MEMLEAK, true);\n',
                '        bundle.putLong(UMCrash.KEY_PA_TIMEOUT_TIME, 2000L);\n',
                '        UMCrash.initConfig(bundle);\n',
                '\n',
            ]

        # 添加import语句（在最后一个import之后）
        new_lines = []
        imports_added = False

        for i, line in enumerate(lines):
            new_lines.append(line)

            # 在最后一个import语句后添加新的import
            if not imports_added and line.startswith('import '):
                # 检查下一行是否还是import
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('import '):
                    for imp in import_statements:
                        # 去重：只添加尚不存在的import
                        if imp.strip() not in content_str:
                            new_lines.append(imp)
                        else:
                            print("  ✅ import 语句已存在，跳过（重复检测）")
                    imports_added = True

        # 如果没有import语句，在package声明后添加
        if not imports_added:
            temp_lines = []
            for i, line in enumerate(new_lines):
                temp_lines.append(line)
                if line.startswith('package '):
                    temp_lines.append('\n')
                    for imp in import_statements:
                        if imp.strip() not in content_str:
                            temp_lines.append(imp)
                        else:
                            print("  ✅ import 语句已存在，跳过（重复检测）")
                    imports_added = True
            new_lines = temp_lines

        # 定位UMConfigure.init()调用位置，在其之前插入APM初始化代码
        final_lines = []
        inserted = False

        for i, line in enumerate(new_lines):
            if not inserted and 'UMConfigure.init' in line:
                # 在UMConfigure.init()调用之前插入APM初始化代码
                final_lines.extend(init_code)
                inserted = True

            final_lines.append(line)

        if not inserted:
            print("  ❌ 未找到UMConfigure.init()调用，无法确定插入位置")
            return False

        # 写回文件
        with open(app_file, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)

        print("  ✅ 已添加UMCrash.initConfig()代码（位于UMConfigure.init之前）")
        return True

    # ─── 工具方法 ─────────────────────────────────────────────────────

    def _find_application_file(self) -> Optional[str]:
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

                            if 'Application' in content and (
                                'extends Application' in content or
                                ': Application()' in content or
                                ': Application(' in content
                            ):
                                return file_path
                        except Exception:
                            continue

        return None

    def _extract_package_name(self) -> str:
        """从AndroidManifest.xml或build.gradle提取应用包名（供efs whiteList使用）"""
        # 优先从AndroidManifest.xml提取
        manifest_path = os.path.join(
            self.project_path,
            self.app_module,
            'src', 'main',
            'AndroidManifest.xml'
        )

        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.search(r'package\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)

        # 回退：从build.gradle提取namespace或applicationId
        for ext in ['build.gradle.kts', 'build.gradle']:
            gradle_file = os.path.join(self.project_path, self.app_module, ext)
            if os.path.exists(gradle_file):
                with open(gradle_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 尝试匹配namespace
                match = re.search(r'namespace\s*[=\s]*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)

                # 尝试匹配applicationId
                match = re.search(r'applicationId\s*[=\s]*["\']([^"\']+)["\']', content)
                if match:
                    return match.group(1)

        print("  ⚠️  未能自动提取包名，请手动指定")
        return ""
