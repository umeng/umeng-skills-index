# -*- coding: utf-8 -*-
"""
Flutter APM SDK集成 - 插件兼容性自动修复模块

背景：umeng_common_sdk 1.3.1 存在打包缺陷（同时残留 Android/iOS 双实现桩文件、
compileSdkVersion 过低），在 Flutter 3.44+/Gradle 9.1 环境下导致双端编译必失败：
  - Android: Redeclaration: class UmengCommonSdkPlugin
  - iOS:     Duplicate interface definition for class 'UmengCommonSdkPlugin'
  - Android: requires compile against version 34

本模块在 flutter pub get 成功后自动修复 pub cache 中的插件源码，
所有操作幂等、容错（异常仅打印警告，不阻塞集成流程）。
"""

import os
import re


class PluginFixer:
    """友盟 Flutter 插件兼容性修复器

    当前修复目标：
    - umeng_common_sdk 1.3.1：双实现桩文件 + compileSdkVersion 33
    - umeng_apm_sdk（如 2.3.7）：compileSdkVersion 33 在 AGP 9.x 下编译失败
    类结构预留扩展：后续可通过 _fix_plugin() 追加处理其他插件。
    """

    # 需要删除的双实现桩文件（相对插件根目录），仅针对 umeng_common_sdk 1.3.1
    STUB_FILES = [
        os.path.join('android', 'src', 'main', 'kotlin', 'com', 'umeng',
                     'umeng_common_sdk', 'UmengCommonSdkPlugin.kt'),
        os.path.join('ios', 'Classes', 'UmengCommonSdkPlugin.swift'),
    ]

    def __init__(self, project_path):
        """
        Args:
            project_path: Flutter项目路径（用于解析 pubspec.lock）
        """
        self.project_path = project_path

    def fix(self):
        """执行插件兼容性修复（入口方法）

        Returns:
            bool: 修复是否成功（失败不阻塞集成流程）
        """
        print("\n🔧 检查友盟插件兼容性修复（plugin_fixer）...")

        try:
            ok = self._fix_plugin('umeng_common_sdk')
            # umeng_apm_sdk 同样存在 compileSdkVersion 33 缺陷（如 2.3.7），
            # 桩文件删除仅对 umeng_common_sdk 1.3.1 生效，此处只会走 compileSdkVersion 修复
            ok = self._fix_plugin('umeng_apm_sdk') and ok
            return ok
        except Exception as e:
            print("  ⚠️  插件兼容性修复异常（已跳过，不阻塞集成）: {}".format(e))
            return False

    # ------------------------------------------------------------------
    # 单插件修复流程
    # ------------------------------------------------------------------

    def _fix_plugin(self, plugin_name):
        """修复指定插件的已知缺陷

        Args:
            plugin_name: 插件包名（如 umeng_common_sdk）

        Returns:
            bool: 是否成功
        """
        # 1. 解析 pubspec.lock 获取插件版本
        version = self._resolve_plugin_version(plugin_name)
        if not version:
            print("  ℹ️  pubspec.lock 中未找到 {}，跳过修复".format(plugin_name))
            return True

        # 2. 定位 pub cache 中的插件目录
        plugin_dir = self._locate_plugin_dir(plugin_name, version)
        if not plugin_dir:
            return True

        print("  📦 检测到 {} {}".format(plugin_name, version))

        # 3. 针对 umeng_common_sdk 1.3.1：删除双实现桩文件
        if plugin_name == 'umeng_common_sdk' and version == '1.3.1':
            self._remove_stub_files(plugin_dir)
        else:
            print("  ℹ️  {} {} 无需删除桩文件".format(plugin_name, version))

        # 4. 修复 compileSdkVersion（幂等）
        self._fix_compile_sdk_version(plugin_dir)

        return True

    def _resolve_plugin_version(self, plugin_name):
        """从项目 pubspec.lock 解析插件版本号

        Returns:
            str | None: 版本号（如 "1.3.1"），未找到返回 None
        """
        pubspec_lock = os.path.join(self.project_path, 'pubspec.lock')
        try:
            if not os.path.exists(pubspec_lock):
                print("  ⚠️  未找到 pubspec.lock，跳过插件兼容性修复")
                return None

            with open(pubspec_lock, 'r', encoding='utf-8') as f:
                content = f.read()

            # 匹配 pubspec.lock 中的包条目块：
            #   umeng_common_sdk:
            #     dependency: ...
            #     description: ...
            #     source: hosted
            #     version: "1.3.1"
            pattern = r'(?:^|\n)\s*' + re.escape(plugin_name) + \
                      r':\s*\n(?:[ \t]+\S.*\n)*?[ \t]+version:\s*"([^"]+)"'
            match = re.search(pattern, content)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            print("  ⚠️  解析 pubspec.lock 失败: {}".format(e))
            return None

    def _locate_plugin_dir(self, plugin_name, version):
        """定位 pub cache 中的插件目录

        pub cache 根目录优先取环境变量 PUB_CACHE，否则使用 ~/.pub-cache

        Returns:
            str | None: 插件目录路径，不存在时打印提示并返回 None
        """
        try:
            pub_cache = os.environ.get('PUB_CACHE', '').strip()
            if not pub_cache:
                pub_cache = os.path.join(os.path.expanduser('~'), '.pub-cache')

            plugin_dir = os.path.join(
                pub_cache, 'hosted', 'pub.dev',
                '{}-{}'.format(plugin_name, version)
            )

            if not os.path.isdir(plugin_dir):
                print("  ⚠️  未找到插件目录: {}".format(plugin_dir))
                print("  💡 请确认已执行 flutter pub get，或检查 PUB_CACHE 环境变量指向的缓存目录")
                return None
            return plugin_dir
        except Exception as e:
            print("  ⚠️  定位插件目录失败: {}".format(e))
            return None

    def _remove_stub_files(self, plugin_dir):
        """删除插件中的双实现桩文件（幂等）

        1.3.1 版本打包缺陷：同时包含平台实现桩文件与预编译产物，
        新版 Gradle/Xcode 下触发类重复定义编译错误。
        """
        removed = 0
        for rel_path in self.STUB_FILES:
            stub_path = os.path.join(plugin_dir, *rel_path.split(os.sep))
            try:
                if os.path.exists(stub_path):
                    os.remove(stub_path)
                    removed += 1
                    print("  ✅ 已删除桩文件: {}".format(rel_path))
                # 不存在视为已修复（幂等）
            except Exception as e:
                print("  ⚠️  删除桩文件失败（{}）: {}".format(rel_path, e))

        if removed == 0:
            print("  ℹ️  双实现桩文件已不存在，跳过")

    def _fix_compile_sdk_version(self, plugin_dir):
        """修复插件 android/build.gradle 中的 compileSdkVersion（幂等）

        compileSdkVersion 33 -> 34；已是 34+ 则跳过。
        """
        gradle_path = os.path.join(plugin_dir, 'android', 'build.gradle')
        try:
            if not os.path.exists(gradle_path):
                print("  ⚠️  插件缺少 android/build.gradle，跳过 compileSdkVersion 修复")
                return

            with open(gradle_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.search(r'compileSdkVersion\s+(\d+)', content)
            if not match:
                print("  ⚠️  插件 build.gradle 中未找到 compileSdkVersion，跳过")
                return

            current = int(match.group(1))
            if current >= 34:
                print("  ✅ compileSdkVersion 已为 {}，无需修复".format(current))
                return

            new_content = content.replace(
                match.group(0), 'compileSdkVersion 34', 1)
            with open(gradle_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("  ✅ compileSdkVersion {} -> 34".format(current))
        except Exception as e:
            print("  ⚠️  compileSdkVersion 修复失败: {}".format(e))


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python plugin_fixer.py <flutter_project_path>")
        sys.exit(1)

    fixer = PluginFixer(sys.argv[1])
    if fixer.fix():
        print("\n✅ 插件兼容性修复完成")
    else:
        print("\n⚠️  插件兼容性修复未完全成功（不影响集成流程）")
