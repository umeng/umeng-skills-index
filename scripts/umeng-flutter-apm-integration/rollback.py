# -*- coding: utf-8 -*-
"""
Flutter APM SDK集成 - 回滚模块
负责项目备份和回滚恢复
"""

import os
import shutil
import zipfile
import sys
from datetime import datetime


class RollbackManager:
    """回滚管理器"""
    
    # 排除的目录（不纳入备份，减少体积）
    EXCLUDE_DIRS = {
        'build', '.dart_tool', '.gradle', 'Pods',
        'backups', '.git', '.idea', '.vscode',
    }
    EXCLUDE_PATH_FRAGMENTS = {
        'android/.gradle', 'android/app/build',
        'ios/Pods', '.dart_tool', 'build/',
    }
    
    # 关键文件列表（仅回滚这些文件可避免全量覆盖）
    CRITICAL_FILES = [
        'pubspec.yaml',
        'pubspec.lock',
        os.path.join('android', 'app', 'build.gradle'),
        os.path.join('android', 'app', 'build.gradle.kts'),
        os.path.join('android', 'app', 'src', 'main', 'AndroidManifest.xml'),
        os.path.join('lib', 'main.dart'),
        os.path.join('ios', 'Runner', 'AppDelegate.swift'),
        os.path.join('ios', 'Runner', 'AppDelegate.m'),
        os.path.join('ios', 'Podfile'),
    ]
    
    def __init__(self, project_path):
        self.project_path = os.path.abspath(project_path)
        self.project_name = os.path.basename(self.project_path)
        self.backup_dir = os.path.join(os.path.dirname(self.project_path), 'backups')
    
    def backup_project(self):
        """备份整个项目目录"""
        print("\n" + "="*60)
        print("💾 开始备份项目...")
        print("="*60 + "\n")
        
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            print("  📁 创建备份目录: {}".format(self.backup_dir))
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = '{}_apm_backup_{}.zip'.format(self.project_name, timestamp)
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        print("  📦 备份文件: {}".format(backup_filename))
        print("  📂 项目路径: {}".format(self.project_path))
        print("  ⏳ 正在压缩...\n")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                self._zip_directory(self.project_path, zipf)
            
            file_size = os.path.getsize(backup_path)
            file_size_mb = file_size / (1024 * 1024)
            
            print("\n  ✅ 备份成功")
            print("  📊 备份大小: {:.2f} MB".format(file_size_mb))
            print("  📄 备份路径: {}".format(backup_path))
            
            return backup_path
            
        except Exception as e:
            print("\n  ❌ 备份失败: {}".format(str(e)))
            return None
    
    def rollback(self, backup_path, full=False):
        """执行回滚
        Args:
            backup_path: 备份文件路径
            full: True=全量回滚，False=仅回滚关键文件（默认）
        """
        if full:
            return self._full_rollback(backup_path)
        else:
            return self.rollback_files_only(backup_path)
    
    def rollback_files_only(self, backup_path):
        """仅从备份中恢复关键文件"""
        print("\n" + "="*60)
        print("🔄 开始关键文件回滚...")
        print("="*60 + "\n")
        
        if not os.path.exists(backup_path):
            print("  ❌ 备份文件不存在: {}".format(backup_path))
            return False
        
        print("  📄 备份文件: {}".format(backup_path))
        print("  📂 目标路径: {}".format(self.project_path))
        print("  📋 仅恢复关键文件:")
        for f in self.CRITICAL_FILES:
            print("     - {}".format(f))
        print("  ⏳ 正在恢复...\n")
        
        try:
            restored_count = 0
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                namelist = zipf.namelist()
                
                for critical_file in self.CRITICAL_FILES:
                    # 备份中的路径包含项目名前缀
                    arcname = os.path.join(self.project_name, critical_file)
                    # 兼容正反斜杠
                    arcname_normalized = arcname.replace('\\', '/')
                    
                    matched = None
                    for name in namelist:
                        if name.replace('\\', '/') == arcname_normalized:
                            matched = name
                            break
                    
                    if matched:
                        target_path = os.path.join(self.project_path, critical_file)
                        target_dir = os.path.dirname(target_path)
                        
                        if not os.path.exists(target_dir):
                            os.makedirs(target_dir)
                        
                        with zipf.open(matched) as src, open(target_path, 'wb') as dst:
                            dst.write(src.read())
                        
                        restored_count += 1
                        print("  ✅ 已恢复: {}".format(critical_file))
            
            print("\n  📊 共恢复 {} 个文件".format(restored_count))
            print("  ✅ 关键文件回滚成功")
            return True
            
        except Exception as e:
            print("\n  ❌ 关键文件回滚失败: {}".format(str(e)))
            return False
    
    def _full_rollback(self, backup_path):
        """从备份全量恢复项目"""
        print("\n" + "="*60)
        print("🔄 开始全量回滚项目...")
        print("="*60 + "\n")
        
        if not os.path.exists(backup_path):
            print("  ❌ 备份文件不存在: {}".format(backup_path))
            return False
        
        print("  📄 备份文件: {}".format(backup_path))
        print("  📂 目标路径: {}".format(self.project_path))
        print("  ⚠️  警告: 当前项目的所有修改将被覆盖")
        print("  ⏳ 正在恢复...\n")
        
        try:
            if os.path.exists(self.project_path):
                print("  🗑️  删除当前项目...")
                shutil.rmtree(self.project_path)
            
            print("  📦 解压备份...")
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(os.path.dirname(self.project_path))
            
            print("\n  ✅ 全量回滚成功")
            print("  📂 项目已恢复到: {}".format(self.project_path))
            
            return True
            
        except Exception as e:
            print("\n  ❌ 回滚失败: {}".format(str(e)))
            return False
    
    def list_backups(self):
        """列出所有备份"""
        if not os.path.exists(self.backup_dir):
            print("  📁 备份目录不存在")
            return []
        
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.endswith('.zip') and self.project_name in file:
                backup_path = os.path.join(self.backup_dir, file)
                file_size = os.path.getsize(backup_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(backup_path))
                
                backups.append({
                    'path': backup_path,
                    'filename': file,
                    'size': file_size,
                    'time': file_time
                })
        
        backups.sort(key=lambda x: x['time'], reverse=True)
        
        return backups
    
    def print_backups(self):
        """打印备份列表"""
        print("\n" + "="*60)
        print("📋 项目备份列表")
        print("="*60 + "\n")
        
        backups = self.list_backups()
        
        if not backups:
            print("  📁 暂无备份")
            return
        
        for i, backup in enumerate(backups, 1):
            size_mb = backup['size'] / (1024 * 1024)
            time_str = backup['time'].strftime('%Y-%m-%d %H:%M:%S')
            
            print("  {}. {}".format(i, backup['filename']))
            print("     时间: {}".format(time_str))
            print("     大小: {:.2f} MB".format(size_mb))
            print("     路径: {}".format(backup['path']))
            print()
        
        print("="*60)
    
    def _should_exclude(self, file_path, rel_path):
        """判断是否应排除该路径"""
        # 检查目录名
        basename = os.path.basename(file_path)
        if basename in self.EXCLUDE_DIRS:
            return True
        
        # 检查路径片段
        rel_normalized = rel_path.replace('\\', '/')
        for frag in self.EXCLUDE_PATH_FRAGMENTS:
            if frag in rel_normalized:
                return True
        
        # 跳过备份文件
        if basename.endswith('.backup') or basename.endswith('.zip'):
            return True
        
        return False
    
    def _zip_directory(self, directory, zipf):
        """压缩目录（排除构建产物和缓存）"""
        for root, dirs, files in os.walk(directory):
            # 过滤目录（原地修改 dirs 以阻止 os.walk 进入）
            dirs[:] = [d for d in dirs if not self._should_exclude(
                os.path.join(root, d),
                os.path.relpath(os.path.join(root, d), directory)
            )]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory)
                
                if self._should_exclude(file_path, rel_path):
                    continue
                
                arcname = os.path.relpath(file_path, os.path.dirname(directory))
                zipf.write(file_path, arcname)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flutter APM项目回滚工具')
    parser.add_argument('--project-path', required=True, help='项目路径')
    parser.add_argument('--backup-file', help='备份文件路径（用于回滚）')
    parser.add_argument('--list', action='store_true', help='列出所有备份')
    parser.add_argument('--full', action='store_true', help='全量回滚（默认仅回滚关键文件）')
    parser.add_argument('--yes', action='store_true', help='跳过确认提示')
    
    args = parser.parse_args()
    
    manager = RollbackManager(args.project_path)
    
    if args.list:
        manager.print_backups()
    elif args.backup_file:
        print("\n⚠️  确认回滚操作")
        print("  项目路径: {}".format(args.project_path))
        print("  备份文件: {}".format(args.backup_file))
        print("\n此操作将覆盖当前项目的所有修改！")
        
        if args.yes:
            choice = 'yes'
        else:
            choice = input("\n是否继续? (yes/no): ").strip().lower()
        
        if choice == 'yes':
            if manager.rollback(args.backup_file, full=args.full):
                print("\n✅ 回滚完成")
                sys.exit(0)
            else:
                print("\n❌ 回滚失败")
                sys.exit(1)
        else:
            print("\n❌ 取消回滚")
            sys.exit(0)
    else:
        backup_path = manager.backup_project()
        
        if backup_path:
            print("\n✅ 备份完成")
            sys.exit(0)
        else:
            print("\n❌ 备份失败")
            sys.exit(1)


if __name__ == '__main__':
    main()
