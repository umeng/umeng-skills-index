# -*- coding: utf-8 -*-
"""
Flutter统计SDK集成 - SDK集成模块
负责pubspec.yaml修改、Android原生配置、iOS pod install、Dart代码注入
"""

import os
import re
import shutil
import subprocess
import sys

from plugin_fixer import PluginFixer


class SDKIntegrator:
    """Flutter统计SDK集成器"""
    
    def __init__(self, project_path, config):
        self.project_path = project_path
        self.config = config
        self.android_key = config.get('android_key', 'YOUR_ANDROID_APPKEY')
        self.ios_key = config.get('ios_key', 'YOUR_IOS_APPKEY')
        self.channel = config.get('channel', 'Umeng')
        
        # SDK版本
        self.sdk_version = '^1.2.3'
    
    def integrate(self):
        """执行SDK集成"""
        print("\n" + "="*60)
        print("🔧 开始SDK集成...")
        print("="*60 + "\n")
        
        # 步骤1: 修改pubspec.yaml
        if not self._update_pubspec():
            return False
        
        # 步骤2: 执行flutter pub get
        if not self._run_flutter_pub_get():
            return False
        
        # 步骤 2.5: 插件兼容性自动修复
        print("\n  🔧 检查插件兼容性...")
        if not PluginFixer(self.project_path).fix():
            print("  ⚠️  插件兼容性修复未全部成功（不阻塞集成流程）")
        
        # 步骤3: Android端配置
        if not self._configure_android():
            return False
        
        # 步骤4: iOS端配置
        if not self._configure_ios():
            return False
        
        # 步骤5: 注入Dart初始化代码
        if not self._inject_dart_code():
            return False
        
        print("\n✅ SDK集成完成\n")
        return True
    
    def _update_pubspec(self):
        """修改pubspec.yaml添加友盟SDK依赖"""
        print("📝 修改 pubspec.yaml...")
        
        pubspec_path = os.path.join(self.project_path, 'pubspec.yaml')
        
        with open(pubspec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经包含umeng_common_sdk
        if 'umeng_common_sdk' in content:
            # 提取已有版本号
            existing_match = re.search(r'umeng_common_sdk:\s*(\S+)', content)
            if existing_match:
                existing_ver = existing_match.group(1)
                print("  ⚠️  pubspec.yaml 已包含 umeng_common_sdk: {}".format(existing_ver))
                if existing_ver != self.sdk_version:
                    print("  ℹ️  建议升级到 {}（当前不自动覆盖）".format(self.sdk_version))
            else:
                print("  ⚠️  pubspec.yaml 已包含 umeng_common_sdk，跳过添加")
            return True
        
        # 在dependencies下添加umeng_common_sdk
        # 查找dependencies:段落（支持行内注释）
        deps_match = re.search(r'^dependencies:\s*(?:#.*)?$', content, re.MULTILINE)
        
        if deps_match:
            # 在dependencies:后添加
            insert_pos = deps_match.end()
            
            # 查找第一个非缩进的行（下一个段落的开始）
            next_section_match = re.search(r'\n^\w', content[insert_pos:])
            if next_section_match:
                insert_pos += next_section_match.start()
            
            # 添加SDK依赖
            sdk_dep = '\n  umeng_common_sdk: {}\n'.format(self.sdk_version)
            content = content[:insert_pos] + sdk_dep + content[insert_pos:]
            
            with open(pubspec_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("  ✅ 添加 umeng_common_sdk: {}".format(self.sdk_version))
        else:
            print("  ❌ 未找到 dependencies 段落")
            return False
        
        return True
    
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
                
                # 检查是否包含umeng_common_sdk
                if 'umeng_common_sdk' in result.stdout:
                    print("  ✅ umeng_common_sdk 已安装")
                
                return True
            else:
                print("  ❌ flutter pub get 失败")
                
                # 检查是否是http依赖冲突
                error_output = result.stderr + result.stdout
                if 'http' in error_output.lower() and 'version solving failed' in error_output.lower():
                    print("\n  💡 检测到 http 依赖冲突，尝试添加 dependency_overrides...")
                    self._add_http_override()
                    
                    # 重新执行flutter pub get
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
        """添加http依赖覆盖（仅在尚无 http override 时添加）"""
        pubspec_path = os.path.join(self.project_path, 'pubspec.yaml')
        
        with open(pubspec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有 dependency_overrides 中的 http 条目
        if 'dependency_overrides:' in content:
            # 提取 dependency_overrides 段落内容
            override_section_match = re.search(
                r'dependency_overrides:\s*\n((?:[ \t]+\S.*\n)*)', content
            )
            if override_section_match:
                override_content = override_section_match.group(1)
                if 'http:' in override_content or 'http :' in override_content:
                    print("  ℹ️  dependency_overrides 中已有 http override，跳过")
                    return
            
            # 已有 dependency_overrides 但没有 http，添加 http 条目
            override_match = re.search(r'dependency_overrides:\s*$', content, re.MULTILINE)
            if override_match:
                insert_pos = override_match.end()
                content = content[:insert_pos] + '\n  http: ^0.13.1' + content[insert_pos:]
        else:
            # 添加新的dependency_overrides段落
            content += '\ndependency_overrides:\n  http: ^0.13.1\n'
        
        with open(pubspec_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ 添加 dependency_overrides: http: ^0.13.1")
        print("  ℹ️  如不再需要可在集成完成后手动移除 dependency_overrides 中的 http 条目")
    
    def _configure_android(self):
        """配置Android端"""
        print("\n🤖 配置 Android 端...")
        
        # 1. 添加权限到AndroidManifest.xml
        if not self._add_android_permissions():
            return False
        
        # 2. 创建MyApplication类
        if not self._create_application_class():
            return False
        
        # 3. 注册Application
        if not self._register_application():
            return False
        
        # 4. 添加混淆规则
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
        
        # 需要添加的权限
        permissions = [
            'android.permission.ACCESS_NETWORK_STATE',
            'android.permission.ACCESS_WIFI_STATE',
            'android.permission.READ_PHONE_STATE',
            'android.permission.INTERNET'
        ]
        
        modified = False
        for perm in permissions:
            if perm not in content:
                # 在<application>标签前添加权限
                perm_line = '    <uses-permission android:name="{}" />\n'.format(perm)
                
                # 查找<application>标签
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
    
    def _create_application_class(self):
        """创建MyApplication类"""
        print("  📝 创建 MyApplication 类...")
        
        android_dir = os.path.join(self.project_path, 'android')
        
        # 确定包路径
        namespace = self.config.get('android_namespace')
        if not namespace:
            # 尝试从build.gradle或build.gradle.kts读取
            build_gradle = os.path.join(android_dir, 'app', 'build.gradle')
            build_gradle_kts = os.path.join(android_dir, 'app', 'build.gradle.kts')
            gradle_file = build_gradle_kts if os.path.exists(build_gradle_kts) else build_gradle
            if os.path.exists(gradle_file):
                with open(gradle_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                match = re.search(r'namespace\s*=?\s*["\']([^"\']+)["\']', content)
                if match:
                    namespace = match.group(1)
        
        if not namespace:
            print("  ❌ 无法确定包名")
            return False
        
        # 确定使用Kotlin还是Java
        kotlin_dir = os.path.join(android_dir, 'app', 'src', 'main', 'kotlin')
        java_dir = os.path.join(android_dir, 'app', 'src', 'main', 'java')
        
        uses_kotlin = os.path.exists(kotlin_dir)
        
        # 构建目录路径
        package_path = namespace.replace('.', '/')
        
        if uses_kotlin:
            app_dir = os.path.join(kotlin_dir, package_path)
            app_file = os.path.join(app_dir, 'MyApplication.kt')
        else:
            app_dir = os.path.join(java_dir, package_path)
            app_file = os.path.join(app_dir, 'MyApplication.java')
        
        # 创建目录
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        
        # 检查文件是否已存在
        if os.path.exists(app_file):
            print("  ⚠️  MyApplication 已存在，跳过创建")
            return True
        
        # 生成代码
        if uses_kotlin:
            code = """package {package}

import android.app.Application
import com.umeng.commonsdk.UMConfigure

class MyApplication : Application() {{
    override fun onCreate() {{
        super.onCreate()
        // 预初始化：不采集设备信息，不上报数据，耗时极少
        // 将 {android_key} 替换为实际 AppKey
        UMConfigure.preInit(this, "{android_key}", "{channel}")
    }}
}}
""".format(package=namespace, android_key=self.android_key, channel=self.channel)
        else:
            code = """package {package};

import android.app.Application;
import com.umeng.commonsdk.UMConfigure;

public class MyApplication extends Application {{
    @Override
    public void onCreate() {{
        super.onCreate();
        // 预初始化：不采集设备信息，不上报数据，耗时极少
        // 将 {android_key} 替换为实际 AppKey
        UMConfigure.preInit(this, "{android_key}", "{channel}");
    }}
}}
""".format(package=namespace, android_key=self.android_key, channel=self.channel)
        
        with open(app_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print("  ✅ 创建 MyApplication: {}".format(os.path.basename(app_file)))
        
        return True
    
    def _register_application(self):
        """在AndroidManifest.xml中注册Application"""
        print("  📝 注册 Application...")
        
        manifest_path = os.path.join(
            self.project_path, 'android', 'app', 'src', 'main', 'AndroidManifest.xml'
        )
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 读取 <application ...> 标签
        app_tag_match = re.search(r'<application[^>]*>', content, re.DOTALL)
        if not app_tag_match:
            print("  ❌ 未找到 <application> 标签")
            return False
        
        app_tag = app_tag_match.group(0)
        
        # 检查是否已注册为 MyApplication
        if 'android:name=".MyApplication"' in app_tag:
            print("  ℹ️  MyApplication 已注册，跳过")
            return True
        
        # 检查是否有 ${applicationName}（Flutter 默认模板）
        if '${applicationName}' in app_tag:
            # 替换默认占位符
            new_tag = re.sub(r'android:name="\$\{applicationName\}"',
                             'android:name=".MyApplication"', app_tag)
            content = content.replace(app_tag, new_tag)
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("  ✅ 替换 ${applicationName} 为 .MyApplication")
        elif 'android:name=' in app_tag:
            # 已有其他自定义 Application
            existing = re.search(r'android:name="([^"]*)"', app_tag)
            if existing:
                print("  ⚠️  检测到已有自定义 Application: {}".format(existing.group(1)))
                print("  ⚠️  请手动在该 Application 类中添加友盟初始化代码")
                print("  ⚠️  跳过自动注册，集成仍可继续")
            return True
        else:
            # 无 android:name，安全插入
            new_tag = app_tag.replace('<application', '<application android:name=".MyApplication"', 1)
            content = content.replace(app_tag, new_tag)
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("  ✅ 注册 MyApplication")
        
        return True
    
    def _add_proguard_rules(self):
        """添加混淆规则"""
        print("  📝 添加混淆规则...")
        
        proguard_path = os.path.join(
            self.project_path, 'android', 'app', 'proguard-rules.pro'
        )
        
        rules = """
# 友盟 SDK 混淆规则
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
            
            # 检查是否已包含友盟规则
            if 'com.umeng.**' in content:
                print("  ℹ️  混淆规则已存在，跳过")
                return True
            
            # 追加规则
            with open(proguard_path, 'a', encoding='utf-8') as f:
                f.write(rules)
        else:
            # 创建新文件
            with open(proguard_path, 'w', encoding='utf-8') as f:
                f.write(rules)
        
        print("  ✅ 添加混淆规则")
        
        return True
    
    def _configure_ios(self):
        """配置iOS端"""
        print("\n🍎 配置 iOS 端...")
        
        ios_dir = os.path.join(self.project_path, 'ios')
        
        if not os.path.exists(ios_dir):
            print("  ⚠️  未找到 ios/ 目录，跳过 iOS 配置")
            return True
        
        # 执行pod install
        print("  🔧 执行 pod install...")
        print("     这可能需要几分钟，请耐心等待...\n")
        
        podfile_path = os.path.join(ios_dir, 'Podfile')
        if not os.path.exists(podfile_path):
            print("  ⚠️  未找到 ios/Podfile，跳过 pod install，iOS 原生依赖可能缺失")
            print("     若为 SPM 工程（Flutter 3.44+ 新建工程默认启用）：请参考文档「SPM → CocoaPods 迁移」章节完成迁移后重跑本脚本")
            print("     若为 CocoaPods 工程：请先执行 flutter build ios 生成 Podfile，再手动执行 cd ios && pod install")
            return True
        
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
                print("  ℹ️  iOS 端零原生代码配置，Dart 层会自动桥接")
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
    
    def _inject_dart_code(self):
        """注入Dart初始化代码（注入式修改，保留用户原有业务代码）"""
        print("\n💉 注入 Dart 初始化代码...")
        
        main_dart_path = os.path.join(self.project_path, 'lib', 'main.dart')
        
        if not os.path.exists(main_dart_path):
            print("  ❌ 未找到 lib/main.dart")
            return False
        
        # 读取现有 main.dart 内容
        with open(main_dart_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # 幂等检查：若已包含友盟 SDK 初始化代码则跳过
        if 'UmengCommonSdk.initCommon' in existing_content:
            print("  ⚠️  已检测到友盟 SDK 初始化代码，跳过注入")
            return True
        
        # 备份原文件
        backup_path = main_dart_path + '.backup'
        shutil.copy2(main_dart_path, backup_path)
        print("  💾 已备份: {}".format(os.path.basename(backup_path)))
        
        modified_content = existing_content
        
        # 1. 添加 import（如不存在）
        umeng_import = "import 'package:umeng_common_sdk/umeng_common_sdk.dart';"
        if umeng_import not in modified_content:
            # 在文件顶部最后一个 import 之后添加
            last_import_match = None
            for m in re.finditer(r'^import\s+.+$', modified_content, re.MULTILINE):
                last_import_match = m
            
            if last_import_match:
                insert_pos = last_import_match.end()
                modified_content = modified_content[:insert_pos] + '\n' + umeng_import + modified_content[insert_pos:]
            else:
                # 没有 import 语句，添加到文件开头
                modified_content = umeng_import + '\n\n' + modified_content
            print("  ✅ 添加 umeng_common_sdk import")
        
        # 2. 创建 _initUmengSdk() 函数定义并注入到 main() 中 runApp() 之前
        init_function = (
            "\n"
            "/// 友盟 SDK 初始化函数\n"
            "/// 必须在用户同意隐私政策后才能调用\n"
            "void _initUmengSdk() {{\n"
            "  UmengCommonSdk.initCommon(\n"
            "    '{android_key}',  // Android 平台 AppKey\n"
            "    '{ios_key}',      // iOS 平台 AppKey\n"
            "    '{channel}',      // 渠道标识\n"
            "  );\n"
            "  UmengCommonSdk.setPageCollectionModeAuto();\n"
            "}}\n"
        ).format(
            android_key=self.android_key,
            ios_key=self.ios_key,
            channel=self.channel
        )
        
        # 在 runApp() 调用之前注入注释提示（不自动调用，遵守隐私合规）
        runapp_match = re.search(r'^(\s*)runApp\s*\(', modified_content, re.MULTILINE)
        if runapp_match:
            indent = runapp_match.group(1)
            # 注入注释提示（不自动调用，需用户同意隐私政策后手动调用）
            inject_comment = (
                "{indent}// TODO: 请在用户同意隐私政策后调用 _initUmengSdk()\n"
                "{indent}// 注意: 必须在 runApp() 之后调用（如首页 initState 或隐私同意回调），\n"
                "{indent}// 在 runApp() 之前调用会因 Binding 未就绪而静默失败\n"
                "\n"
            ).format(indent=indent)
            insert_pos = runapp_match.start()
            modified_content = modified_content[:insert_pos] + inject_comment + modified_content[insert_pos:]
            print("  ✅ 在 runApp() 之前添加隐私合规提示注释")
        else:
            print("  ⚠️  未找到 runApp() 调用，请在 main() 中手动添加 _initUmengSdk() 调用")
        
        # 在文件末尾添加 _initUmengSdk() 函数定义
        modified_content = modified_content.rstrip() + '\n' + init_function
        print("  ✅ 添加 _initUmengSdk() 函数定义")
        
        # 写入修改后的内容
        with open(main_dart_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print("  ✅ 注入 Dart 初始化代码（保留原有业务代码）")
        print("  ℹ️  已在 main.dart 中添加友盟 SDK 初始化，原有 Widget 树保持不变")
        print("  ⚠️  请在用户同意隐私政策后手动调用 _initUmengSdk()")
        
        # 注入后语法自检
        self._verify_dart_syntax()
        
        return True
    
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
                # 打印 analyze 输出的错误行（前 10 行）
                shown = 0
                for line in result.stdout.split('\n'):
                    if 'error' in line.lower() and shown < 10:
                        print("    " + line.strip())
                        shown += 1
                print("  💡 可用 diff lib/main.dart lib/main.dart.backup 查看注入改动")
        except Exception as e:
            print("  ⚠️  语法检查跳过: {}".format(e))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python sdk_integrator.py <project_path> [--android-key KEY] [--ios-key KEY] [--channel CHANNEL]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    config = {
        'android_key': 'YOUR_ANDROID_APPKEY',
        'ios_key': 'YOUR_IOS_APPKEY',
        'channel': 'Umeng'
    }
    
    # 解析参数
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
        else:
            i += 1
    
    integrator = SDKIntegrator(project_path, config)
    if integrator.integrate():
        print("\n✅ SDK集成成功")
    else:
        print("\n❌ SDK集成失败")
        sys.exit(1)
