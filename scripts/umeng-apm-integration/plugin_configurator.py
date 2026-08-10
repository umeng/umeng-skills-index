#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APM Gradle插件配置模块
处理APM插件的3个注入点：classpath、apply plugin、efs配置块
"""

import os
import re
from typing import Tuple


class GradlePluginConfigurator:
    """友盟APM Gradle插件配置器"""

    def __init__(self, project_path: str, app_module: str):
        self.project_path = os.path.abspath(project_path)
        self.app_module = app_module

    def configure_all(self, package_name: str = "") -> Tuple[bool, str]:
        """
        编排3个Gradle插件配置子步骤

        Args:
            package_name: 应用包名，用于efs whiteList

        Returns:
            (是否成功, 详细信息)
        """
        print("\n🔌 开始配置APM Gradle插件...\n")

        try:
            # 1. 注入classpath依赖
            if not self._inject_classpath():
                return False, "APM插件classpath注入失败"

            # 2. apply plugin
            if not self._apply_plugin():
                return False, "APM插件apply失败"

            # 3. 注入efs配置块
            if not self._inject_efs_config(package_name):
                return False, "efs配置块注入失败"

            print("✅ APM Gradle插件配置完成\n")
            return True, "Gradle插件配置完成"

        except Exception as e:
            print(f"\n❌ Gradle插件配置失败: {str(e)}\n")
            return False, f"Gradle插件配置失败: {str(e)}"

    # ─── 子步骤1: 注入classpath ───────────────────────────────────────

    def _inject_classpath(self) -> bool:
        """在工程根build.gradle的buildscript.dependencies中注入apm-plugin classpath"""
        print("  📋 步骤 1/3: 注入APM插件classpath")

        # 检测Groovy / Kotlin DSL
        root_gradle_kts = os.path.join(self.project_path, 'build.gradle.kts')
        root_gradle_groovy = os.path.join(self.project_path, 'build.gradle')

        if os.path.exists(root_gradle_kts):
            gradle_file = root_gradle_kts
            is_kotlin = True
        elif os.path.exists(root_gradle_groovy):
            gradle_file = root_gradle_groovy
            is_kotlin = False
        else:
            print("    ❌ 未找到工程根build.gradle文件")
            return False

        with open(gradle_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 幂等性检查
        if 'apm-plugin' in content:
            print("    ⚠️  apm-plugin classpath已存在，跳过")
            return True

        # 定位buildscript { dependencies { 块
        lines = content.split('\n')
        new_lines = []
        in_buildscript = False
        in_dependencies = False
        bs_level = 0
        dep_level = 0
        injected = False

        for line in lines:
            new_lines.append(line)
            stripped = line.strip()

            if not in_buildscript and not injected:
                if stripped.startswith('buildscript') and '{' in stripped:
                    in_buildscript = True
                    bs_level = stripped.count('{') - stripped.count('}')
                    continue

            if in_buildscript and not injected:
                bs_level += stripped.count('{') - stripped.count('}')

                if not in_dependencies:
                    if 'dependencies' in stripped and '{' in stripped:
                        in_dependencies = True
                        dep_level = stripped.count('{') - stripped.count('}')
                        continue

                if in_dependencies:
                    dep_level += stripped.count('{') - stripped.count('}')

                    # 在dependencies块关闭前插入
                    if dep_level <= 0:
                        if is_kotlin:
                            classpath_line = '        classpath("com.umeng.umsdk:apm-plugin:2.0.0")'
                        else:
                            classpath_line = '        classpath "com.umeng.umsdk:apm-plugin:2.0.0"'
                        new_lines.insert(-1, classpath_line)
                        injected = True
                        in_dependencies = False
                        in_buildscript = False

                if bs_level <= 0:
                    in_buildscript = False

        if not injected:
            print("    ⚠️  未找到buildscript.dependencies块，在文件顶部添加")
            if is_kotlin:
                block = [
                    'buildscript {',
                    '    dependencies {',
                    '        classpath("com.umeng.umsdk:apm-plugin:2.0.0")',
                    '    }',
                    '}',
                    '',
                ]
            else:
                block = [
                    'buildscript {',
                    '    dependencies {',
                    '        classpath "com.umeng.umsdk:apm-plugin:2.0.0"',
                    '    }',
                    '}',
                    '',
                ]
            new_lines = block + new_lines

        with open(gradle_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        print("    ✅ 已注入apm-plugin classpath")
        return True

    # ─── 子步骤2: apply plugin ────────────────────────────────────────

    def _apply_plugin(self) -> bool:
        """在App模块build.gradle头部添加apply plugin"""
        print("\n  📋 步骤 2/3: Apply APM插件")

        app_gradle_kts = os.path.join(self.project_path, self.app_module, 'build.gradle.kts')
        app_gradle_groovy = os.path.join(self.project_path, self.app_module, 'build.gradle')

        if os.path.exists(app_gradle_kts):
            gradle_file = app_gradle_kts
        elif os.path.exists(app_gradle_groovy):
            gradle_file = app_gradle_groovy
        else:
            print("    ❌ 未找到App模块build.gradle文件")
            return False

        is_kotlin = gradle_file.endswith('.kts')

        with open(gradle_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 幂等性检查
        if 'com.efs.sdk.plugin' in content:
            print("    ⚠️  apply plugin 'com.efs.sdk.plugin' 已存在，跳过")
            return True

        lines = content.split('\n')
        new_lines = []
        inserted = False
        last_apply_idx = -1

        # 构造apply语句
        if is_kotlin:
            apply_stmt = 'apply(plugin = "com.efs.sdk.plugin")'
        else:
            apply_stmt = "apply plugin: 'com.efs.sdk.plugin'"

        # 先找到最后一个apply plugin行的位置
        for i, line in enumerate(lines):
            if line.strip().startswith('apply plugin') or line.strip().startswith('apply(plugin'):
                last_apply_idx = i

        for i, line in enumerate(lines):
            new_lines.append(line)
            if not inserted and i == last_apply_idx:
                new_lines.append(apply_stmt)
                inserted = True

        # 如果没找到apply行，在文件第一行plugins块或文件头部插入
        if not inserted:
            # 查找plugins块结束位置
            plugins_end = -1
            p_level = 0
            in_plugins = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('plugins') and '{' in stripped:
                    in_plugins = True
                    p_level = stripped.count('{') - stripped.count('}')
                    if p_level <= 0:
                        plugins_end = i
                        break
                    continue
                if in_plugins:
                    p_level += stripped.count('{') - stripped.count('}')
                    if p_level <= 0:
                        plugins_end = i
                        break

            if plugins_end >= 0:
                new_lines = lines[:plugins_end + 1] + [apply_stmt] + lines[plugins_end + 1:]
            else:
                new_lines = [apply_stmt, ''] + lines

        with open(gradle_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        print("    ✅ 已添加 apply plugin: 'com.efs.sdk.plugin'")
        return True

    # ─── 子步骤3: 注入efs配置块 ──────────────────────────────────────

    def _inject_efs_config(self, package_name: str) -> bool:
        """在App模块build.gradle中android{}同级添加efs配置块"""
        print("\n  📋 步骤 3/3: 注入efs配置块")

        app_gradle_kts = os.path.join(self.project_path, self.app_module, 'build.gradle.kts')
        app_gradle_groovy = os.path.join(self.project_path, self.app_module, 'build.gradle')

        if os.path.exists(app_gradle_kts):
            gradle_file = app_gradle_kts
        elif os.path.exists(app_gradle_groovy):
            gradle_file = app_gradle_groovy
        else:
            print("    ❌ 未找到App模块build.gradle文件")
            return False

        with open(gradle_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 幂等性检查
        if 'efs {' in content or 'efs{' in content:
            print("    ⚠️  efs配置块已存在，跳过")
            return True

        # 使用括号计数法定位android {}块结束位置
        lines = content.split('\n')
        new_lines = []
        in_android = False
        android_level = 0
        android_end_idx = -1

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not in_android and android_end_idx < 0:
                if stripped.startswith('android') and '{' in stripped:
                    in_android = True
                    android_level = stripped.count('{') - stripped.count('}')
                    if android_level <= 0:
                        android_end_idx = i
                        in_android = False
                    continue

            if in_android:
                android_level += stripped.count('{') - stripped.count('}')
                if android_level <= 0:
                    android_end_idx = i
                    in_android = False

        if android_end_idx < 0:
            print("    ❌ 未找到android {}块")
            return False

        # 构建efs配置块
        whitelist_value = f'"{package_name}"' if package_name else ''
        efs_block = [
            '',
            'efs {',
            '    enable = true',
            f'    whiteList = [{whitelist_value}]',
            '    blackList = []',
            '}',
        ]

        # 在android块结束位置之后插入
        new_lines = lines[:android_end_idx + 1] + efs_block + lines[android_end_idx + 1:]

        with open(gradle_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))

        print(f"    ✅ 已注入efs配置块 (whiteList: [{whitelist_value}])")
        return True
