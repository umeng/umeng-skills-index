# -*- coding: utf-8 -*-
"""
Flutter APM SDK集成 - SDK集成模块
负责pubspec.yaml修改、Binding替换、NavigatorObserver注册、
Android/iOS可选Native崩溃配置、Dart初始化代码注入
"""

import os
import re
import shutil
import subprocess
import sys

from plugin_fixer import PluginFixer


class SDKIntegrator:
    """Flutter APM SDK集成器"""
    
    # SDK版本
    APM_SDK_VERSION = '^2.2.1'
    COMMON_SDK_VERSION = '^1.2.6'
    
    def __init__(self, project_path, config):
        """
        初始化APM SDK集成器
        
        Args:
            project_path: Flutter项目路径
            config: 配置字典，包含 android_key, ios_key, channel, native_crash, project_type 等
        """
        self.project_path = project_path
        self.config = config
        self.android_key = config.get('android_key', 'YOUR_ANDROID_APPKEY')
        self.ios_key = config.get('ios_key', 'YOUR_IOS_APPKEY')
        self.channel = config.get('channel', 'Umeng')
        self.native_crash = config.get('native_crash', False)
        self.project_type = config.get('project_type', 0)  # 0=App, 1=Module
        self.has_flutter_boost = config.get('has_flutter_boost', False)
        self.project_name = config.get('project_name', 'my_flutter_app')
        self.project_version = config.get('project_version', '1.0.0+1')
        # 集成过程中的待办/警示项（由 main.py step9 报告消费，避免“注释模板却报成功”）
        self.warnings = []
        # iOS 端是否被跳过（无 Podfile 等场景，由报告如实标注）
        self.ios_skipped = False
    
    def integrate(self):
        """执行APM SDK集成"""
        print("\n" + "="*60)
        print("🔧 开始APM SDK集成...")
        print("="*60 + "\n")
        
        # 1. 修改pubspec.yaml
        if not self._update_pubspec():
            return False
        
        # 2. 执行flutter pub get
        if not self._run_flutter_pub_get():
            return False
        
        # 2.5 插件兼容性自动修复（umeng_common_sdk 1.3.1 打包缺陷，失败不阻塞）
        try:
            PluginFixer(self.project_path).fix()
        except Exception as e:
            print("  ⚠️  插件兼容性修复跳过: {}".format(e))
        
        # 3. Android端基础配置（权限+混淆）
        if not self._configure_android():
            return False
        
        # 4. iOS端配置（pod install）
        if not self._configure_ios():
            return False
        
        # 5. 注入Dart APM初始化代码（核心）
        if not self._inject_dart_apm_code():
            return False
        
        # 6. (可选) Native崩溃采集配置
        if self.native_crash:
            if not self._configure_native_crash():
                return False
        
        print("\n✅ APM SDK集成完成\n")
        return True
    
    # ------------------------------------------------------------------
    # pubspec.yaml 修改
    # ------------------------------------------------------------------
    
    def _update_pubspec(self):
        """修改pubspec.yaml添加APM SDK依赖"""
        print("📝 修改 pubspec.yaml...")
        
        pubspec_path = os.path.join(self.project_path, 'pubspec.yaml')
        
        with open(pubspec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = False
        
        # 检查/更新 umeng_apm_sdk
        if 'umeng_apm_sdk' in content:
            # 已有依赖，仅打印版本建议
            ver_match = re.search(r'umeng_apm_sdk:\s*\^?(\d+\.\d+\.\d+)', content)
            if ver_match:
                existing_ver = ver_match.group(1)
                print("  ℹ️  pubspec.yaml 已包含 umeng_apm_sdk: ^{}".format(existing_ver))
                if self._version_lt(existing_ver, '2.2.1'):
                    print("  💡 建议升级到 umeng_apm_sdk: {}".format(self.APM_SDK_VERSION))
            else:
                print("  ⚠️  pubspec.yaml 已包含 umeng_apm_sdk，跳过添加")
        else:
            content = self._add_dep_under_dependencies(content, 
                'umeng_apm_sdk: {}'.format(self.APM_SDK_VERSION))
            modified = True
            print("  ✅ 添加 umeng_apm_sdk: {}".format(self.APM_SDK_VERSION))
        
        # 确保 umeng_common_sdk 版本 >= 1.2.6
        if 'umeng_common_sdk' in content:
            # 检查版本是否过低
            ver_match = re.search(r'umeng_common_sdk:\s*\^?(\d+\.\d+\.\d+)', content)
            if ver_match:
                existing_ver = ver_match.group(1)
                if self._version_lt(existing_ver, '1.2.6'):
                    content = re.sub(
                        r'umeng_common_sdk:\s*\^?\d+\.\d+\.\d+',
                        'umeng_common_sdk: {}'.format(self.COMMON_SDK_VERSION),
                        content
                    )
                    modified = True
                    print("  ✅ 更新 umeng_common_sdk -> {}".format(self.COMMON_SDK_VERSION))
                else:
                    print("  ✅ umeng_common_sdk 版本满足（{}）".format(existing_ver))
            else:
                print("  ℹ️  pubspec.yaml 已包含 umeng_common_sdk，跳过")
        else:
            content = self._add_dep_under_dependencies(content,
                'umeng_common_sdk: {}'.format(self.COMMON_SDK_VERSION))
            modified = True
            print("  ✅ 添加 umeng_common_sdk: {}".format(self.COMMON_SDK_VERSION))
        
        if modified:
            with open(pubspec_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return True
    
    def _add_dep_under_dependencies(self, content, dep_line):
        """在 dependencies: 段落末尾添加一行依赖"""
        deps_match = re.search(r'^dependencies:\s*(?:#.*)?$', content, re.MULTILINE)
        if deps_match:
            insert_pos = deps_match.end()
            next_section_match = re.search(r'\n^\w', content[insert_pos:])
            if next_section_match:
                insert_pos += next_section_match.start()
            content = content[:insert_pos] + '\n  ' + dep_line + '\n' + content[insert_pos:]
        return content
    
    def _version_lt(self, v1, v2):
        """简单版本比较：v1 < v2"""
        def parse(v):
            return [int(x) for x in v.split('.')]
        return parse(v1) < parse(v2)
    
    # ------------------------------------------------------------------
    # flutter pub get
    # ------------------------------------------------------------------
    
    def _run_flutter_pub_get(self):
        """执行flutter pub get"""
        print("\n🔧 执行 flutter pub get...")
        
        try:
            result = subprocess.run(
                ['flutter', 'pub', 'get'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("  ✅ flutter pub get 成功")
                return True
            else:
                print("  ❌ flutter pub get 失败")
                error_output = result.stderr + result.stdout
                
                # http 依赖冲突处理
                if 'http' in error_output.lower() and 'version solving failed' in error_output.lower():
                    print("\n  💡 检测到 http 依赖冲突，尝试添加 dependency_overrides...")
                    self._add_http_override()
                    
                    print("  🔄 重新执行 flutter pub get...")
                    result2 = subprocess.run(
                        ['flutter', 'pub', 'get'],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result2.returncode == 0:
                        print("  ✅ flutter pub get 成功（已解决依赖冲突）")
                        return True
                
                print("\n错误信息:")
                for line in result.stderr.split('\n')[-20:]:
                    if line.strip():
                        print("    {}".format(line))
                return False
                
        except subprocess.TimeoutExpired:
            print("  ❌ flutter pub get 超时（超过2分钟）")
            return False
        except Exception as e:
            print("  ❌ flutter pub get 出错: {}".format(str(e)))
            return False
    
    def _add_http_override(self):
        """添加http依赖覆盖"""
        pubspec_path = os.path.join(self.project_path, 'pubspec.yaml')
        with open(pubspec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有 http override，有则不覆盖
        if 'dependency_overrides:' in content:
            # 检查 dependency_overrides 段中是否已有 http
            override_section = content[content.index('dependency_overrides:'):]
            # 截取到下一个顶级段落（非缩进键）之前
            next_section = re.search(r'\n(?![ \t])[a-zA-Z_]', override_section[1:])
            if next_section:
                override_section = override_section[:next_section.start() + 1]
            if re.search(r'^\s+http\s*:', override_section, re.MULTILINE):
                print("  ℹ️  dependency_overrides 已包含 http override，跳过")
                return
            # 在 dependency_overrides: 段内追加（兼容行内注释）
            override_match = re.search(r'dependency_overrides:[ \t]*(?:#.*)?$', content, re.MULTILINE)
            if override_match:
                insert_pos = override_match.end()
                content = content[:insert_pos] + '\n  http: ^0.13.1' + content[insert_pos:]
        else:
            content += '\ndependency_overrides:\n  http: ^0.13.1\n'
        
        with open(pubspec_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✅ 添加 dependency_overrides: http: ^0.13.1")
    
    # ------------------------------------------------------------------
    # Android 端基础配置
    # ------------------------------------------------------------------
    
    def _configure_android(self):
        """配置Android端（权限+混淆规则）"""
        print("\n🤖 配置 Android 端...")
        
        android_dir = os.path.join(self.project_path, 'android')
        
        # 检测已有原生友盟 SDK 依赖
        build_gradle = os.path.join(android_dir, 'app', 'build.gradle')
        build_gradle_kts = os.path.join(android_dir, 'app', 'build.gradle.kts')
        gradle_file = build_gradle_kts if os.path.exists(build_gradle_kts) else build_gradle
        if os.path.exists(gradle_file):
            with open(gradle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'com.umeng.umsdk' in content:
                print("  ⚠️  检测到已有友盟原生 SDK 依赖（com.umeng.umsdk），Flutter SDK 内置原生 SDK，请删除 build.gradle 中的手动依赖以避免冲突")
        
        if not self._add_android_permissions():
            return False
        
        if not self._add_proguard_rules():
            return False
        
        return True
    
    def _add_android_permissions(self):
        """添加Android权限"""
        print("  📝 添加 AndroidManifest 权限...")
        
        manifest_path = os.path.join(
            self.project_path, 'android', 'app', 'src', 'main', 'AndroidManifest.xml'
        )
        
        if not os.path.exists(manifest_path):
            print("  ❌ 未找到 AndroidManifest.xml")
            return False
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        permissions = [
            'android.permission.ACCESS_NETWORK_STATE',
            'android.permission.ACCESS_WIFI_STATE',
            'android.permission.READ_PHONE_STATE',
            'android.permission.INTERNET'
        ]
        
        modified = False
        for perm in permissions:
            if perm not in content:
                perm_line = '    <uses-permission android:name="{}" />\n'.format(perm)
                app_match = re.search(r'<application', content)
                if app_match:
                    insert_pos = app_match.start()
                    content = content[:insert_pos] + perm_line + content[insert_pos:]
                    modified = True
                    print("    ✅ 添加权限: {}".format(perm))
        
        if modified:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            print("    ℹ️  所有权限已存在，跳过")
        
        return True
    
    def _add_proguard_rules(self):
        """添加混淆规则"""
        print("  📝 添加混淆规则...")
        
        proguard_path = os.path.join(
            self.project_path, 'android', 'app', 'proguard-rules.pro'
        )
        
        rules = """
# 友盟 APM SDK 混淆规则
-keep class com.umeng.** {*;}
-keep class com.uc.** {*;}
-keepclassmembers class * {
    public <init> (org.json.JSONObject);
}
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}
"""
        
        if os.path.exists(proguard_path):
            with open(proguard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'com.umeng.**' in content:
                print("  ℹ️  混淆规则已存在，跳过")
                return True
            
            with open(proguard_path, 'a', encoding='utf-8') as f:
                f.write(rules)
        else:
            with open(proguard_path, 'w', encoding='utf-8') as f:
                f.write(rules)
        
        print("  ✅ 添加混淆规则")
        return True
    
    # ------------------------------------------------------------------
    # iOS 端配置
    # ------------------------------------------------------------------
    
    def _configure_ios(self):
        """配置iOS端（pod install）"""
        print("\n🍎 配置 iOS 端...")
        
        ios_dir = os.path.join(self.project_path, 'ios')
        
        if not os.path.exists(ios_dir):
            print("  ⚠️  未找到 ios/ 目录，跳过 iOS 配置")
            return True
        
        # 检测已有原生友盟 SDK 依赖
        podfile_path = os.path.join(ios_dir, 'Podfile')
        if os.path.exists(podfile_path):
            with open(podfile_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if "pod 'UMCommon'" in content or "pod 'UMAPM'" in content:
                print("  ⚠️  检测到 Podfile 中已有友盟原生 SDK（UMCommon/UMAPM），Flutter SDK 内置原生 SDK，请删除以避免冲突")
        
        # 检查 Podfile 是否存在
        if not os.path.exists(podfile_path):
            self.ios_skipped = True
            print("  ⚠️  未找到 ios/Podfile，跳过 pod install，iOS 原生依赖可能缺失")
            print("     若为 SPM 工程（Flutter 3.44+ 新建工程默认启用）：请参考文档「SPM → CocoaPods 迁移」章节完成迁移后重跑本脚本")
            print("     若为 CocoaPods 工程：请先执行 flutter build ios 生成 Podfile，再手动执行 cd ios && pod install")
            self.warnings.append("iOS 端未配置（未找到 Podfile，pod install 被跳过）：SPM 工程请按文档「SPM → CocoaPods 迁移」章节迁移；CocoaPods 工程请先 flutter build ios 后手动 pod install")
            return True
        
        print("  🔧 执行 pod install...")
        print("     这可能需要几分钟，请耐心等待...\n")
        
        try:
            result = subprocess.run(
                ['pod', 'install'],
                cwd=ios_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("  ✅ pod install 成功")
                print("  ℹ️  iOS 端零原生代码配置（Dart 层自动桥接）")
                return True
            else:
                print("  ❌ pod install 失败")
                print("\n错误信息:")
                for line in result.stderr.split('\n')[-20:]:
                    if line.strip():
                        print("    {}".format(line))
                
                print("\n💡 可能的原因和解决建议:")
                print("  1. 执行 cd ios && pod repo update")
                print("  2. 检查 ios/Podfile 配置")
                print("  3. 确认 Podfile 中 platform :ios 与 IPHONEOS_DEPLOYMENT_TARGET 一致（≥13.0）")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ❌ pod install 超时（超过5分钟）")
            return False
        except FileNotFoundError:
            print("  ❌ pod 命令不存在")
            print("     安装方法: sudo gem install cocoapods")
            return False
        except Exception as e:
            print("  ❌ pod install 出错: {}".format(str(e)))
            return False
    
    # ------------------------------------------------------------------
    # Dart APM 初始化代码注入（核心）
    # ------------------------------------------------------------------
    
    def _inject_dart_apm_code(self):
        """增量注入Dart APM初始化代码（不覆盖整个 main.dart）"""
        print("\n💉 注入 Dart APM 初始化代码...")
        
        main_dart_path = os.path.join(self.project_path, 'lib', 'main.dart')
        
        if not os.path.exists(main_dart_path):
            print("  ❌ 未找到 lib/main.dart")
            return False
        
        with open(main_dart_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 幂等检查：若已包含 APM 初始化则跳过
        if 'UmengApmSdk' in content and 'MyApmWidgetsFlutterBinding' in content:
            print("  ⚠️  main.dart 已包含 APM 初始化代码，跳过注入")
            # 旧版模板残留检测：旧模板将 observer 传入 MyApp，与脚本注入的
            # MaterialApp.navigatorObservers 形成双注册，触发 observer.navigator == null 断言
            if 'MyApp(observer)' in content:
                print("  ⚠️  检测到旧版初始化模板（MyApp(observer)），存在 observer 双注册风险")
                print("     请保持 MyApp 构造不变（不接收 observer），observer 由 MaterialApp.navigatorObservers 承载，详见文档 FAQ")
                self.warnings.append("检测到旧版初始化模板（MyApp(observer)）：请移除 observer 传参，避免与 MaterialApp.navigatorObservers 双注册导致 observer.navigator == null 断言")
                # 联动检查 widget_test.dart：若 MyApp 构造已改为接收 observer，
                # 模板自带测试的 pumpWidget(const MyApp()) 会编译失败（flutter analyze/test 报 error）
                self._check_widget_test_compat()
            return True
        
        # 备份原文件
        backup_path = main_dart_path + '.apm_backup'
        shutil.copy2(main_dart_path, backup_path)
        print("  💾 已备份: {}".format(os.path.basename(backup_path)))
        
        # 检测 main() 函数是否存在
        main_func_match = re.search(r'^(void\s+main\s*\([^)]*\)\s*(async\s*)?\{)', content, re.MULTILINE)
        if not main_func_match:
            # main() 函数找不到，生成参考示例文件，不修改原文件
            print("  ⚠️  无法定位 main() 函数，生成参考示例文件")
            self._generate_apm_guide_file()
            self.warnings.append("无法定位 main() 函数，已生成参考示例 lib/apm_integration_guide.dart，需人工按示例完成 APM 初始化")
            return True
        
        modified = content
        
        # --- 步骤1: 在文件顶部追加必要 import ---
        imports_to_add = []
        if "import 'package:umeng_apm_sdk/umeng_apm_sdk.dart'" not in modified:
            imports_to_add.append("import 'package:umeng_apm_sdk/umeng_apm_sdk.dart';")
        if "import 'package:umeng_common_sdk/umeng_common_sdk.dart'" not in modified:
            imports_to_add.append("import 'package:umeng_common_sdk/umeng_common_sdk.dart';")
        
        if imports_to_add:
            # 找到最后一个 import 语句，在其后追加
            last_import_match = None
            for m in re.finditer(r'^import\s+.+;$', modified, re.MULTILINE):
                last_import_match = m
            
            if last_import_match:
                insert_pos = last_import_match.end()
                import_block = '\n' + '\n'.join(imports_to_add)
                modified = modified[:insert_pos] + import_block + modified[insert_pos:]
            else:
                # 没有 import，在文件开头添加
                import_block = '\n'.join(imports_to_add) + '\n\n'
                modified = import_block + modified
            print("  ✅ 添加 APM SDK import")
        
        # --- 步骤2: 在文件末尾追加 MyApmWidgetsFlutterBinding 类定义 ---
        if 'MyApmWidgetsFlutterBinding' not in modified:
            if self.has_flutter_boost:
                binding_code = (
                    "\n\n/// 自定义 Binding：继承 ApmWidgetsFlutterBinding，混入 BoostFlutterBinding\n"
                    "class MyApmWidgetsFlutterBinding extends ApmWidgetsFlutterBinding\n"
                    "    with BoostFlutterBinding {\n"
                    "  static WidgetsBinding? ensureInitialized() {\n"
                    "    MyApmWidgetsFlutterBinding();\n"
                    "    return WidgetsBinding.instance;\n"
                    "  }\n"
                    "}\n"
                )
            else:
                binding_code = (
                    "\n\n/// 自定义 Binding：继承 ApmWidgetsFlutterBinding\n"
                    "class MyApmWidgetsFlutterBinding extends ApmWidgetsFlutterBinding {\n"
                    "  static WidgetsBinding? ensureInitialized() {\n"
                    "    MyApmWidgetsFlutterBinding();\n"
                    "    return WidgetsBinding.instance;\n"
                    "  }\n"
                    "}\n"
                )
            modified += binding_code
            print("  ✅ 追加 MyApmWidgetsFlutterBinding 类定义")
        
        # --- 步骤3: 在 main() 函数中处理 Binding 调用 ---
        if 'WidgetsFlutterBinding.ensureInitialized()' in modified:
            # 仅替换第一处，避免误改注释或字符串字面量
            modified = modified.replace(
                'WidgetsFlutterBinding.ensureInitialized()',
                'MyApmWidgetsFlutterBinding.ensureInitialized()',
                1
            )
            print("  ✅ 替换 WidgetsFlutterBinding.ensureInitialized() -> MyApmWidgetsFlutterBinding.ensureInitialized()")
        else:
            # 在 main() 函数体开头插入
            main_func_match2 = re.search(r'^(void\s+main\s*\([^)]*\)\s*(async\s*)?\{)', modified, re.MULTILINE)
            if main_func_match2:
                insert_pos = main_func_match2.end()
                binding_call = "\n  MyApmWidgetsFlutterBinding.ensureInitialized();"
                modified = modified[:insert_pos] + binding_call + modified[insert_pos:]
                print("  ✅ 在 main() 开头插入 MyApmWidgetsFlutterBinding.ensureInitialized()")
        
        # --- 步骤4: 在 main() 函数体开头（Binding 调用之前）插入 APM 初始化示例代码块 ---
        main_func_match3 = re.search(r'^(void\s+main\s*\([^)]*\)\s*(async\s*)?\{)', modified, re.MULTILINE)
        if main_func_match3 and '// TODO: 请在用户同意隐私政策后添加 APM 初始化' not in modified:
            insert_pos = main_func_match3.end()
            # 已知 appkey 等参数时填入示例代码
            name = self.project_name or '你的应用名称'
            # 注意：模板不将 observer 传入 MyApp（observer 已由步骤5 注册到
            # MaterialApp.navigatorObservers），避免双注册触发 observer.navigator == null 断言
            init_example = (
                "\n  // TODO: 请在用户同意隐私政策后添加 APM 初始化:\n"
                "  // 注意: 必须在 runApp() 之后调用，之前调用会因 Binding 未就绪而静默失败\n"
                "  // final umengApmSdk = UmengApmSdk(\n"
                "  //   name: '" + name + "',\n"
                "  //   bver: '" + self.project_version + "',\n"
                "  //   initFlutterBinding: MyApmWidgetsFlutterBinding.ensureInitialized,\n"
                "  // );\n"
                "  // umengApmSdk.init(appRunner: (observer) {\n"
                "  //   UmengCommonSdk.initCommon(\n"
                "  //     '" + self.android_key + "',\n"
                "  //     '" + self.ios_key + "',\n"
                "  //     '" + self.channel + "',\n"
                "  //   );\n"
                "  //   return const MyApp();\n"
                "  // });\n"
                "  // 注意: 路由 observer 已由脚本自动注册到 MaterialApp.navigatorObservers，\n"
                "  // 请勿将 observer 传入 MyApp（双注册会触发 observer.navigator == null 断言）"
            )
            modified = modified[:insert_pos] + init_example + modified[insert_pos:]
            print("  ✅ 在 main() 开头插入 APM 初始化示例代码（已注释）")
            self.warnings.append("main() 中的 APM 初始化代码为待激活注释模板，需在用户同意隐私政策后取消注释启用（见文档「激活注释模板」章节）")
        
        # --- 步骤5: 尝试向 MaterialApp 的 navigatorObservers 添加 ApmNavigatorObserver ---
        if 'ApmNavigatorObserver' not in modified:
            # 尝试定位 navigatorObservers
            nav_match = re.search(r'navigatorObservers\s*:\s*\[', modified)
            if nav_match:
                insert_pos = nav_match.end()
                modified = modified[:insert_pos] + '\n        ApmNavigatorObserver.singleInstance,' + modified[insert_pos:]
                print("  ✅ 添加 ApmNavigatorObserver 到 navigatorObservers")
            else:
                # 尝试定位 MaterialApp( 构造
                material_match = re.search(r'MaterialApp\s*\(', modified)
                if material_match:
                    insert_pos = material_match.end()
                    modified = modified[:insert_pos] + '\n      navigatorObservers: [ApmNavigatorObserver.singleInstance],' + modified[insert_pos:]
                    print("  ✅ 添加 navigatorObservers: [ApmNavigatorObserver.singleInstance]")
                else:
                    print("  ⚠️  未定位到 MaterialApp，请手动添加 ApmNavigatorObserver")
        
        # 写入修改后的内容
        with open(main_dart_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        
        print("  ✅ 增量注入 Dart APM 初始化代码完成")
        
        # 注入后语法自检（不阻塞）
        self._verify_dart_syntax()
        
        print("  ⚠️  关键检查项:")
        print("     - MyApmWidgetsFlutterBinding 自定义 Binding 已注入")
        print("     - ApmNavigatorObserver 已注册到 MaterialApp.navigatorObservers")
        print("     - 请在用户同意隐私政策后调用 initCommon()")
        print("     - 必须在 runApp() 之后调用，之前调用会因 Binding 未就绪而静默失败")
        
        return True
    
    def _check_widget_test_compat(self):
        """检查 test/widget_test.dart 与 MyApp 构造改动的兼容性
        
        仅当 MyApp 构造已被改为接收 observer（旧模板/官方文档模式）时调用：
        模板自带的 pumpWidget(const MyApp()) 与新构造不匹配，
        flutter analyze / flutter test 会报编译错误，需提示集成者适配。
        新模板路线（MyApp 构造不变）无需此检查。
        """
        widget_test_path = os.path.join(self.project_path, 'test', 'widget_test.dart')
        try:
            if not os.path.exists(widget_test_path):
                return
            with open(widget_test_path, 'r', encoding='utf-8') as f:
                test_content = f.read()
            if 'const MyApp()' in test_content or 'MyApp()' in test_content:
                print("  ⚠️  test/widget_test.dart 仍使用 const MyApp()，与已修改的 MyApp 构造不匹配，flutter analyze/test 将报错")
                print("     适配方式（二选一）：① 恢复 MyApp 构造为不接收 observer（推荐）；② 同步修改测试为 pumpWidget(MyApp(ApmNavigatorObserver.singleInstance))")
                self.warnings.append("test/widget_test.dart 需同步适配：MyApp 构造已改为接收 observer，模板自带测试的 const MyApp() 会编译失败；推荐恢复 MyApp 构造不变（observer 由 MaterialApp.navigatorObservers 承载）")
        except Exception as e:
            print("  ⚠️  widget_test.dart 兼容性检查跳过: {}".format(e))
    
    def _verify_dart_syntax(self):
        """对注入后的 main.dart 执行语法检查"""
        try:
            result = subprocess.run(
                ['flutter', 'analyze', 'lib/main.dart'],
                cwd=self.project_path, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("  ✅ main.dart 语法检查通过")
            else:
                print("  ⚠️  main.dart 语法检查发现问题（不阻塞，编译阶段会兜底）:")
                for line in result.stdout.split('\n'):
                    if 'error' in line.lower():
                        print("    " + line.strip())
                print("  💡 可用 diff lib/main.dart lib/main.dart.apm_backup 查看注入改动")
        except Exception as e:
            print("  ⚠️  语法检查跳过: {}".format(e))
    
    def _generate_apm_guide_file(self):
        """生成 APM 集成参考示例文件（当无法解析 main.dart 时）"""
        guide_path = os.path.join(self.project_path, 'lib', 'apm_integration_guide.dart')
        
        guide_content = (
            "// APM 集成参考示例\n"
            "// 脚本无法自动定位 main() 函数，请参考以下代码手动集成。\n"
            "//\n"
            "// 1. 添加 import:\n"
            "//    import 'package:umeng_apm_sdk/umeng_apm_sdk.dart';\n"
            "//    import 'package:umeng_common_sdk/umeng_common_sdk.dart';\n"
            "//\n"
            "// 2. 在 main() 中替换 WidgetsFlutterBinding.ensureInitialized() 为:\n"
            "//    MyApmWidgetsFlutterBinding.ensureInitialized();\n"
            "//\n"
            "// 3. 在文件中添加以下 Binding 类:\n"
            "//\n"
            "// class MyApmWidgetsFlutterBinding extends ApmWidgetsFlutterBinding {\n"
            "//   static WidgetsBinding? ensureInitialized() {\n"
            "//     MyApmWidgetsFlutterBinding();\n"
            "//     return WidgetsBinding.instance;\n"
            "//   }\n"
            "// }\n"
            "//\n"
            "// 4. 在 MaterialApp 中添加 navigatorObservers:\n"
            "//    navigatorObservers: [ApmNavigatorObserver.singleInstance],\n"
            "//\n"
            "// 5. 在用户同意隐私政策后调用:\n"
            "//    UmengCommonSdk.initCommon('ANDROID_KEY', 'IOS_KEY', 'CHANNEL');\n"
        )
        
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print("  ℹ️  已生成参考示例: lib/apm_integration_guide.dart")
        print("  ⚠️  请参考该文件手动完成 APM 集成")
    
    # ------------------------------------------------------------------
    # (可选) Native 崩溃采集配置
    # ------------------------------------------------------------------
    
    def _configure_native_crash(self):
        """配置可选的Native崩溃采集（Android MyApplication + iOS AppDelegate）"""
        print("\n🔧 配置 Native 崩溃采集...")
        
        # Android 端
        if not self._create_android_application():
            return False
        
        # iOS 端
        if not self._configure_ios_appdelegate():
            return False
        
        return True
    
    def _create_android_application(self):
        """创建Android MyApplication类（含UMCrash.initConfig + UMConfigure.preInit）"""
        print("  📝 创建 Android MyApplication (Native崩溃采集)...")
        
        android_dir = os.path.join(self.project_path, 'android')
        
        namespace = self.config.get('android_namespace')
        if not namespace:
            build_gradle = os.path.join(android_dir, 'app', 'build.gradle')
            build_gradle_kts = os.path.join(android_dir, 'app', 'build.gradle.kts')
            gradle_file = build_gradle_kts if os.path.exists(build_gradle_kts) else build_gradle
            
            if os.path.exists(gradle_file):
                with open(gradle_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                match = re.search(r'namespace\s*=?\s*["\']([^"\']+)["\']', content)
                if match:
                    namespace = match.group(1)
            
            # fallback to manifest
            if not namespace:
                manifest_path = os.path.join(android_dir, 'app', 'src', 'main', 'AndroidManifest.xml')
                if os.path.exists(manifest_path):
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest_content = f.read()
                    pkg_match = re.search(r'package="([^"]+)"', manifest_content)
                    if pkg_match:
                        namespace = pkg_match.group(1)
        
        if not namespace:
            print("  ❌ 无法确定包名")
            return False
        
        uses_kotlin = os.path.exists(os.path.join(android_dir, 'app', 'src', 'main', 'kotlin'))
        package_path = namespace.replace('.', '/')
        
        if uses_kotlin:
            app_dir = os.path.join(android_dir, 'app', 'src', 'main', 'kotlin', package_path)
            app_file = os.path.join(app_dir, 'MyApplication.kt')
        else:
            app_dir = os.path.join(android_dir, 'app', 'src', 'main', 'java', package_path)
            app_file = os.path.join(app_dir, 'MyApplication.java')
        
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        
        if os.path.exists(app_file):
            # 幂等检查
            with open(app_file, 'r', encoding='utf-8') as f:
                existing = f.read()
            if 'UMCrash.initConfig' in existing:
                print("  ⚠️  MyApplication 已包含 UMCrash.initConfig，跳过")
                return True
        
        if uses_kotlin:
            code = """package {package}

import android.app.Application
import android.os.Bundle
import com.umeng.commonsdk.UMConfigure
import com.umeng.umcrash.UMCrash

class MyApplication : Application() {{
    override fun onCreate() {{
        super.onCreate()

        // 配置 Native 采集开关（必须在 preInit 之前调用）
        val bundle = Bundle().apply {{
            putBoolean(UMCrash.KEY_ENABLE_CRASH_JAVA, true)
            putBoolean(UMCrash.KEY_ENABLE_CRASH_NATIVE, true)
            putBoolean(UMCrash.KEY_ENABLE_CRASH_ALL, true)
            putBoolean(UMCrash.KEY_ENABLE_ANR, false)
            putBoolean(UMCrash.KEY_ENABLE_PA, false)
            putBoolean(UMCrash.KEY_ENABLE_LAUNCH, false)
            putBoolean(UMCrash.KEY_ENABLE_MEM, false)
            putBoolean(UMCrash.KEY_ENABLE_H5PAGE, false)
            putBoolean(UMCrash.KEY_ENABLE_POWER, false)
        }}
        UMCrash.initConfig(bundle)

        // 预初始化
        UMConfigure.preInit(this, "{android_key}", "{channel}",
            UMConfigure.DEVICE_TYPE_PHONE, "")
    }}
}}
""".format(package=namespace, android_key=self.android_key, channel=self.channel)
        else:
            code = """package {package};

import android.app.Application;
import android.os.Bundle;
import com.umeng.commonsdk.UMConfigure;
import com.umeng.umcrash.UMCrash;

public class MyApplication extends Application {{
    @Override
    public void onCreate() {{
        super.onCreate();
        Bundle bundle = new Bundle();
        bundle.putBoolean(UMCrash.KEY_ENABLE_CRASH_JAVA, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_CRASH_NATIVE, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_CRASH_ALL, true);
        bundle.putBoolean(UMCrash.KEY_ENABLE_ANR, false);
        bundle.putBoolean(UMCrash.KEY_ENABLE_PA, false);
        bundle.putBoolean(UMCrash.KEY_ENABLE_LAUNCH, false);
        bundle.putBoolean(UMCrash.KEY_ENABLE_MEM, false);
        bundle.putBoolean(UMCrash.KEY_ENABLE_H5PAGE, false);
        bundle.putBoolean(UMCrash.KEY_ENABLE_POWER, false);
        UMCrash.initConfig(bundle);
        UMConfigure.preInit(this, "{android_key}", "{channel}",
            UMConfigure.DEVICE_TYPE_PHONE, "");
    }}
}}
""".format(package=namespace, android_key=self.android_key, channel=self.channel)
        
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print("  ✅ 创建 MyApplication: {}".format(os.path.basename(app_file)))
        
        # 注册 Application 到 AndroidManifest.xml
        self._register_application()
        
        return True
    
    def _register_application(self):
        """在AndroidManifest.xml中注册Application"""
        print("  📝 注册 Application...")
        
        manifest_path = os.path.join(
            self.project_path, 'android', 'app', 'src', 'main', 'AndroidManifest.xml'
        )
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取整个 <application ...> 开标签
        app_tag_match = re.search(r'<application[^>]*>', content, re.DOTALL)
        if not app_tag_match:
            print("  ❌ 未找到 <application> 标签")
            return
        
        app_tag = app_tag_match.group(0)
        
        if 'android:name=".MyApplication"' in app_tag:
            print("  ℹ️  MyApplication 已注册，跳过")
            return
        
        if '${applicationName}' in app_tag:
            new_tag = re.sub(r'android:name="\$\{applicationName\}"',
                             'android:name=".MyApplication"', app_tag)
            content = content.replace(app_tag, new_tag)
        elif 'android:name=' in app_tag:
            existing = re.search(r'android:name="([^"]*)"', app_tag)
            if existing:
                print("  ⚠️  检测到已有自定义 Application: {}".format(existing.group(1)))
                print("  ⚠️  请手动在该 Application 类中添加友盟初始化代码")
            return
        else:
            new_tag = app_tag.replace('<application', '<application android:name=".MyApplication"', 1)
            content = content.replace(app_tag, new_tag)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ 注册 MyApplication")
    
    def _configure_ios_appdelegate(self):
        """配置iOS AppDelegate（Native崩溃采集）"""
        print("  📝 配置 iOS AppDelegate (Native崩溃采集)...")
        
        ios_dir = os.path.join(self.project_path, 'ios')
        if not os.path.exists(ios_dir):
            print("  ⚠️  未找到 ios/ 目录，跳过")
            return True
        
        # 尝试 Swift
        swift_path = os.path.join(ios_dir, 'Runner', 'AppDelegate.swift')
        objc_path = os.path.join(ios_dir, 'Runner', 'AppDelegate.m')
        
        if os.path.exists(swift_path):
            return self._inject_ios_swift_apm(swift_path)
        elif os.path.exists(objc_path):
            return self._inject_ios_objc_apm(objc_path)
        else:
            print("  ⚠️  未找到 AppDelegate.swift 或 AppDelegate.m，跳过")
            return True
    
    def _inject_ios_swift_apm(self, file_path):
        """Swift AppDelegate注入APM配置（改进版：精确定位注入）"""
        print("    📱 iOS 项目类型: Swift")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 幂等检查
        if 'UMAPMConfig' in content or 'UMCrashConfigure' in content:
            print("    ⚠️  AppDelegate 已包含 APM 配置，跳过")
            return True
        
        # 备份
        backup_path = file_path + '.apm_backup'
        shutil.copy2(file_path, backup_path)
        
        # --- import 注入：在最后一个 import 语句后追加 ---
        imports_to_add = []
        if 'import UMCommon' not in content:
            imports_to_add.append('import UMCommon')
        if 'import UMAPM' not in content:
            imports_to_add.append('import UMAPM')
        
        if imports_to_add:
            # 找到最后一个 import 语句
            last_import_match = None
            for m in re.finditer(r'^import\s+\w+.*$', content, re.MULTILINE):
                last_import_match = m
            
            if last_import_match:
                insert_pos = last_import_match.end()
                import_block = '\n' + '\n'.join(imports_to_add)
                content = content[:insert_pos] + import_block + content[insert_pos:]
            else:
                # 无 import 语句，在文件开头添加
                import_block = '\n'.join(imports_to_add) + '\n\n'
                content = import_block + content
            print("    ✅ 添加 import UMCommon / UMAPM")
        
        # --- 代码注入：定位 didFinishLaunchingWithOptions 方法 ---
        apm_code = (
            "\n        // 友盟APM采集开关配置\n"
            "        let config = UMAPMConfig.defaultConfig()\n"
            "        config?.crashAndBlockMonitorEnable = true\n"
            "        config?.launchMonitorEnable = true\n"
            "        config?.memMonitorEnable = false\n"
            "        config?.oomMonitorEnable = false\n"
            "        config?.networkEnable = true\n"
            "        UMCrashConfigure.setAPMConfig(config)\n\n"
        )
        
        # 用正则定位 didFinishLaunchingWithOptions 方法体的 {
        did_finish_match = re.search(
            r'func\s+application\s*\([^)]*didFinishLaunchingWithOptions[^{]*\{',
            content, re.DOTALL
        )
        
        if did_finish_match:
            insert_pos = did_finish_match.end()
            content = content[:insert_pos] + apm_code + content[insert_pos:]
            print("    ✅ 在 didFinishLaunchingWithOptions 方法中注入 APM 配置")
        else:
            # 找不到方法签名，打印建议代码
            print("    ⚠️  未找到 didFinishLaunchingWithOptions 方法")
            print("    ⚠️  请手动在 AppDelegate 的 application(_:didFinishLaunchingWithOptions:) 中添加以下代码:")
            print("        let config = UMAPMConfig.defaultConfig()")
            print("        config?.crashAndBlockMonitorEnable = true")
            print("        config?.launchMonitorEnable = true")
            print("        config?.memMonitorEnable = false")
            print("        config?.oomMonitorEnable = false")
            print("        config?.networkEnable = true")
            print("        UMCrashConfigure.setAPMConfig(config)")
            # 仍然保存 import 修改
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def _inject_ios_objc_apm(self, file_path):
        """Objective-C AppDelegate注入APM配置（改进版：精确定位注入）"""
        print("    📱 iOS 项目类型: Objective-C")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'UMAPMConfig' in content or 'UMCrashConfigure' in content:
            print("    ⚠️  AppDelegate 已包含 APM 配置，跳过")
            return True
        
        backup_path = file_path + '.apm_backup'
        shutil.copy2(file_path, backup_path)
        
        # --- import 注入：在最后一个 #import 后追加 ---
        imports_to_add = []
        if '#import <UMCommon/UMCommon.h>' not in content:
            imports_to_add.append('#import <UMCommon/UMCommon.h>')
        if '#import <UMAPM/UMCrashConfigure.h>' not in content:
            imports_to_add.append('#import <UMAPM/UMCrashConfigure.h>')
        if '#import <UMAPM/UMAPMConfig.h>' not in content:
            imports_to_add.append('#import <UMAPM/UMAPMConfig.h>')
        
        if imports_to_add:
            # 找到最后一个 #import
            last_import_match = None
            for m in re.finditer(r'^#import\s+.+$', content, re.MULTILINE):
                last_import_match = m
            
            if last_import_match:
                insert_pos = last_import_match.end()
                import_block = '\n' + '\n'.join(imports_to_add)
                content = content[:insert_pos] + import_block + content[insert_pos:]
            else:
                import_block = '\n'.join(imports_to_add) + '\n\n'
                content = import_block + content
            print("    ✅ 添加 UMAPM import")
        
        # --- 代码注入：定位 didFinishLaunchingWithOptions 方法 ---
        apm_code = (
            "\n    // 友盟APM采集开关配置\n"
            "    UMAPMConfig *config = [UMAPMConfig defaultConfig];\n"
            "    config.crashAndBlockMonitorEnable = YES;\n"
            "    config.launchMonitorEnable = YES;\n"
            "    config.memMonitorEnable = NO;\n"
            "    config.oomMonitorEnable = NO;\n"
            "    config.networkEnable = YES;\n"
            "    [UMCrashConfigure setAPMConfig:config];\n\n"
        )
        
        # 定位 didFinishLaunchingWithOptions 方法体的 {
        did_finish_match = re.search(
            r'-\s*\(BOOL\)\s*application\s*:\s*\([^)]*\)\s*\w+\s+didFinishLaunchingWithOptions\s*:[^{]*\{',
            content, re.DOTALL
        )
        
        if did_finish_match:
            insert_pos = did_finish_match.end()
            content = content[:insert_pos] + apm_code + content[insert_pos:]
            print("    ✅ 在 didFinishLaunchingWithOptions 方法中注入 APM 配置")
        else:
            print("    ⚠️  未找到 didFinishLaunchingWithOptions 方法")
            print("    ⚠️  请手动在 AppDelegate 的 application:didFinishLaunchingWithOptions: 中添加以下代码:")
            print("        UMAPMConfig *config = [UMAPMConfig defaultConfig];")
            print("        config.crashAndBlockMonitorEnable = YES;")
            print("        config.launchMonitorEnable = YES;")
            print("        [UMCrashConfigure setAPMConfig:config];")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("    ✅ 注入 APM 配置")
        return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python sdk_integrator.py <project_path> [options]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    config = {
        'android_key': 'YOUR_ANDROID_APPKEY',
        'ios_key': 'YOUR_IOS_APPKEY',
        'channel': 'Umeng',
        'native_crash': False,
        'project_type': 0,
        'has_flutter_boost': False,
        'project_name': 'my_flutter_app',
        'project_version': '1.0.0+1',
    }
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--android-key' and i + 1 < len(sys.argv):
            config['android_key'] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--ios-key' and i + 1 < len(sys.argv):
            config['ios_key'] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--channel' and i + 1 < len(sys.argv):
            config['channel'] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--native-crash':
            config['native_crash'] = True
            i += 1
        else:
            i += 1
    
    integrator = SDKIntegrator(project_path, config)
    if integrator.integrate():
        print("\n✅ APM SDK集成成功")
    else:
        print("\n❌ APM SDK集成失败")
        sys.exit(1)
