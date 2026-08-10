# -*- coding: utf-8 -*-
"""
Flutter统计SDK集成 - 插件兼容性自动修复模块
修复 umeng_common_sdk 插件的已知打包缺陷：
1. 双实现桩文件冲突（1.3.1：Kotlin/Swift 桩与 Java/OC 完整实现同时存在）
2. compileSdkVersion 33 在 Flutter 3.44+/Gradle 9.1 下编译失败
所有修复操作均为幂等操作，失败不阻塞主流程。
"""

import os
import re


class PluginFixer:
    """修复 umeng_common_sdk 插件的已知打包缺陷"""

    def __init__(self, project_path):
        self.project_path = project_path

    def fix(self):
        """执行所有插件兼容性修复，返回是否全部成功（失败不阻塞主流程）"""
        # 1. 定位插件路径
        plugin_path = self._locate_plugin_path()
        if not plugin_path:
            return False

        all_ok = True

        # 2. 删除双实现桩文件（仅 1.3.1）
        version = self._get_sdk_version()
        if version == '1.3.1':
            if not self._remove_stub_files(plugin_path):
                all_ok = False

        # 3. 修复 compileSdkVersion
        if not self._fix_compile_sdk_version(plugin_path):
            all_ok = False

        return all_ok

    def _get_sdk_version(self):
        """从项目 pubspec.lock 中提取 umeng_common_sdk 的版本号"""
        lock_path = os.path.join(self.project_path, 'pubspec.lock')
        try:
            if not os.path.exists(lock_path):
                print("  ⚠️  未找到 pubspec.lock，跳过插件修复")
                return None
            with open(lock_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # YAML 结构: packages: -> umeng_common_sdk: -> version: "x.y.z"
            match = re.search(
                r'^\s+umeng_common_sdk:\s*\n(?:[ \t]+\S.*\n)*?^\s+version:\s*["\']?([^"\'\n]+)["\']?',
                content, re.MULTILINE
            )
            if match:
                return match.group(1).strip()
        except Exception as e:
            print("  ⚠️  解析 pubspec.lock 失败: {}".format(e))
        return None

    def _locate_plugin_path(self):
        """定位 pub cache 中的 umeng_common_sdk 插件路径"""
        version = self._get_sdk_version()
        if not version:
            print("  ⚠️  pubspec.lock 中未找到 umeng_common_sdk，跳过插件修复")
            return None

        # pub cache 根目录：优先环境变量 PUB_CACHE，否则 ~/.pub-cache
        pub_cache = os.environ.get('PUB_CACHE') or os.path.expanduser('~/.pub-cache')
        plugin_path = os.path.join(pub_cache, 'hosted', 'pub.dev',
                                   'umeng_common_sdk-{}'.format(version))

        if not os.path.exists(plugin_path):
            print("  ⚠️  未找到插件缓存路径: {}".format(plugin_path))
            return None

        return plugin_path

    def _remove_stub_files(self, plugin_path):
        """删除双实现桩文件（仅 1.3.1，幂等）：保留 Java/OC 完整实现"""
        stub_files = [
            os.path.join('android', 'src', 'main', 'kotlin', 'com', 'umeng',
                         'umeng_common_sdk', 'UmengCommonSdkPlugin.kt'),
            os.path.join('ios', 'Classes', 'UmengCommonSdkPlugin.swift')
        ]

        all_ok = True
        for stub_rel in stub_files:
            stub_path = os.path.join(plugin_path, stub_rel)
            try:
                if os.path.exists(stub_path):
                    os.remove(stub_path)
                    print("  ✅ 已删除插件桩文件: {}".format(stub_rel))
                else:
                    print("  ℹ️  桩文件不存在，跳过: {}".format(stub_rel))
            except Exception as e:
                print("  ⚠️  删除桩文件失败（{}）: {}".format(stub_rel, e))
                all_ok = False

        return all_ok

    def _fix_compile_sdk_version(self, plugin_path):
        """修复插件 android/build.gradle 的 compileSdkVersion（幂等）"""
        gradle_path = os.path.join(plugin_path, 'android', 'build.gradle')
        try:
            if not os.path.exists(gradle_path):
                print("  ⚠️  未找到插件 android/build.gradle，跳过 compileSdkVersion 修复")
                return False

            with open(gradle_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 已是 34+ 则跳过
            matches = re.findall(r'compileSdkVersion\s+(\d+)', content)
            if not matches:
                print("  ℹ️  插件 build.gradle 中未找到 compileSdkVersion")
                return True
            if all(int(v) >= 34 for v in matches):
                print("  ℹ️  插件 compileSdkVersion 已是 34+，无需修复")
                return True

            # 替换 33 <= 版本 < 34 的值（即 33）为 34
            new_content, count = re.subn(
                r'(compileSdkVersion\s+)33', r'\g<1>34', content
            )
            if count > 0:
                with open(gradle_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print("  ✅ 已将插件 compileSdkVersion 33 修复为 34")
            return True
        except Exception as e:
            print("  ⚠️  修复 compileSdkVersion 失败: {}".format(e))
            return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python plugin_fixer.py <project_path>")
        sys.exit(1)

    fixer = PluginFixer(sys.argv[1])
    if fixer.fix():
        print("\n✅ 插件兼容性修复完成")
    else:
        print("\n⚠️  插件兼容性修复未全部成功（不影响主流程）")
