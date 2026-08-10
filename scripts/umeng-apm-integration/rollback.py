#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回滚模块
恢复SDK集成前的所有修改
"""

import os
import sys
import shutil
import zipfile
import argparse
from typing import Tuple


class Rollback:
    """SDK集成回滚器"""
    
    def __init__(self, backup_zip: str, project_path: str):
        self.backup_zip = os.path.abspath(backup_zip)
        self.project_path = os.path.abspath(project_path)
    
    def rollback(self) -> Tuple[bool, str]:
        """
        执行回滚(从zip备份恢复整个工程目录)
        
        Returns:
            (是否成功, 详细信息)
        """
        print("\n🔄 开始回滚SDK集成...\n")
        
        # 验证备份zip文件
        if not os.path.exists(self.backup_zip):
            return False, f"备份zip文件不存在: {self.backup_zip}"
        
        print(f"📦 备份zip文件: {self.backup_zip}")
        print(f"📂 项目路径: {self.project_path}\n")
        
        try:
            # 删除当前工程目录
            print("🗑️  删除当前工程目录...")
            if os.path.exists(self.project_path):
                shutil.rmtree(self.project_path)
                print(f"  ✅ 已删除: {self.project_path}\n")
            
            # 从zip恢复工程目录
            print("📂 从zip备份恢复工程目录...")
            with zipfile.ZipFile(self.backup_zip, 'r') as zipf:
                zipf.extractall(os.path.dirname(self.project_path))
            print(f"  ✅ 已恢复: {self.project_path}\n")
            
            print(f"✅ 回滚完成")
            print(f"   工程已恢复到集成前状态\n")
            
            # 验证恢复结果
            if self._verify_rollback():
                return True, "回滚完成"
            else:
                return False, "回滚后验证失败"
            
        except Exception as e:
            print(f"\n❌ 回滚失败: {str(e)}\n")
            return False, f"回滚失败: {str(e)}"
    

    def _verify_rollback(self) -> bool:
        """验证回滚结果"""
        print("\n验证回滚结果...")
        
        # 检查关键文件是否存在
        check_files = [
            os.path.join(self.project_path, 'build.gradle.kts'),
            os.path.join(self.project_path, 'settings.gradle.kts'),
            os.path.join(self.project_path, 'gradle.properties'),
        ]
        
        all_exist = True
        for file_path in check_files:
            if os.path.exists(file_path):
                rel_path = os.path.relpath(file_path, self.project_path)
                print(f"  ✅ {rel_path}")
            else:
                rel_path = os.path.relpath(file_path, self.project_path)
                print(f"  ❌ 缺失: {rel_path}")
                all_exist = False
        
        if all_exist:
            print("\n✅ 回滚验证通过")
        else:
            print("\n❌ 回滚验证失败")
        
        return all_exist


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='友盟推送SDK集成回滚工具')
    
    parser.add_argument(
        '--backup-zip',
        required=True,
        help='备份zip文件路径'
    )
    
    parser.add_argument(
        '--project-path',
        required=True,
        help='Android项目路径'
    )
    
    args = parser.parse_args()
    
    rollback = Rollback(args.backup_zip, args.project_path)
    success, message = rollback.rollback()
    
    if success:
        print("✅ 回滚成功")
        sys.exit(0)
    else:
        print(f"❌ 回滚失败: {message}")
        sys.exit(1)


if __name__ == '__main__':
    main()

