# -*- coding: utf-8 -*-
"""
iOS统计SDK集成 - 回滚模块
负责项目备份和回滚恢复
"""

import os
import shutil
import zipfile
import sys
from datetime import datetime


class RollbackManager:
    """回滚管理器"""
    
    def __init__(self, project_path):
        self.project_path = os.path.abspath(project_path)
        self.project_name = os.path.basename(self.project_path)
        self.backup_dir = os.path.join(os.path.dirname(self.project_path), 'backups')
    
    def backup_project(self):
        """备份整个项目目录"""
        print("\n" + "="*60)
        print("💾 开始备份项目...")
        print("="*60 + "\n")
        
        # 创建备份目录
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            print("  📁 创建备份目录: {}".format(self.backup_dir))
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = '{}_backup_{}.zip'.format(self.project_name, timestamp)
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        print("  📦 备份文件: {}".format(backup_filename))
        print("  📂 项目路径: {}".format(self.project_path))
        print("  ⏳ 正在压缩...\n")
        
        try:
            # 使用zipfile压缩整个项目目录
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
    
    def rollback(self, backup_path):
        """从备份恢复项目"""
        print("\n" + "="*60)
        print("🔄 开始回滚项目...")
        print("="*60 + "\n")
        
        if not os.path.exists(backup_path):
            print("  ❌ 备份文件不存在: {}".format(backup_path))
            return False
        
        print("  📄 备份文件: {}".format(backup_path))
        print("  📂 目标路径: {}".format(self.project_path))
        print("  ⚠️  警告: 当前项目的所有修改将被覆盖")
        print("  ⏳ 正在恢复...\n")
        
        try:
            # 先删除当前项目目录
            if os.path.exists(self.project_path):
                print("  🗑️  删除当前项目...")
                shutil.rmtree(self.project_path)
            
            # 解压备份
            print("  📦 解压备份...")
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(os.path.dirname(self.project_path))
            
            print("\n  ✅ 回滚成功")
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
        
        # 按时间排序
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
    
    def _zip_directory(self, directory, zipf):
        """压缩目录"""
        for root, dirs, files in os.walk(directory):
            # 跳过备份目录
            if 'backups' in root:
                continue
            
            for file in files:
                # 跳过备份文件
                if file.endswith('.backup') or file.endswith('.zip'):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(directory))
                zipf.write(file_path, arcname)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='iOS项目回滚工具')
    parser.add_argument('--project-path', required=True, help='项目路径')
    parser.add_argument('--backup-file', help='备份文件路径（用于回滚）')
    parser.add_argument('--list', action='store_true', help='列出所有备份')
    parser.add_argument('--yes', action='store_true', help='跳过确认提示')
    
    args = parser.parse_args()
    
    manager = RollbackManager(args.project_path)
    
    if args.list:
        manager.print_backups()
    elif args.backup_file:
        # 执行回滚
        print("\n⚠️  确认回滚操作")
        print("  项目路径: {}".format(args.project_path))
        print("  备份文件: {}".format(args.backup_file))
        print("\n此操作将覆盖当前项目的所有修改！")
        
        if args.yes:
            choice = 'yes'
        else:
            choice = raw_input("\n是否继续? (yes/no): ").strip().lower() if sys.version_info[0] == 2 else input("\n是否继续? (yes/no): ").strip().lower()
        
        if choice == 'yes':
            if manager.rollback(args.backup_file):
                print("\n✅ 回滚完成")
                sys.exit(0)
            else:
                print("\n❌ 回滚失败")
                sys.exit(1)
        else:
            print("\n❌ 取消回滚")
            sys.exit(0)
    else:
        # 执行备份
        backup_path = manager.backup_project()
        
        if backup_path:
            print("\n✅ 备份完成")
            sys.exit(0)
        else:
            print("\n❌ 备份失败")
            sys.exit(1)


if __name__ == '__main__':
    main()
