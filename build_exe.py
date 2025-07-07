#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件比较器打包脚本
用于将Python应用程序打包成可执行文件
"""

import os
import sys
import subprocess

def build_exe():
    """
    使用PyInstaller打包应用程序
    """
    print("开始打包文件比较器...")
    
    # 根据操作系统确定数据文件分隔符
    data_separator = ';' if sys.platform.startswith('win') else ':'
    
    # PyInstaller命令参数
    cmd = [
        'pyinstaller',
        '--hidden-import=openpyxl',     # 确保包含openpyxl模块
        '--hidden-import=PySimpleGUI',  # 确保包含PySimpleGUI模块
        'main.py'
    ]
    
    # 根据操作系统添加特定参数
    if sys.platform.startswith('win'):
        cmd.extend([
            '--onefile',                # Windows: 打包成单个文件
            '--noconsole',              # Windows: 不显示控制台窗口
            '--name=文件比较器'
        ])
    elif sys.platform == 'darwin':
        cmd.extend([
            '--onedir',                 # macOS: 使用目录模式
            '--windowed',               # macOS: 创建.app包
            '--name=文件比较器'
        ])
    else:
        cmd.extend([
            '--onefile',                # Linux: 打包成单个文件
            '--name=文件比较器'
        ])
    
    # 添加数据文件（如果存在）
    if os.path.exists('README.md'):
        cmd.append(f'--add-data=README.md{data_separator}.')
    
    # 添加图标文件（如果存在）
    if os.path.exists('icon.ico'):
        cmd.append('--icon=icon.ico')
    
    try:
        # 执行打包命令
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("打包成功！")
        print(f"输出目录: {os.path.abspath('dist')}")
        
        # 列出生成的文件
        dist_dir = 'dist'
        if os.path.exists(dist_dir):
            print("\n生成的文件:")
            for file in os.listdir(dist_dir):
                file_path = os.path.join(dist_dir, file)
                size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                print(f"  {file} ({size/1024/1024:.1f} MB)")
                
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    except FileNotFoundError:
        print("错误: 未找到pyinstaller命令")
        print("请先安装PyInstaller: pip install pyinstaller")
        return False
    
    return True

def create_spec_file():
    """
    创建PyInstaller规格文件，用于更精细的控制
    """
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('README.md', '.')],
    hiddenimports=['openpyxl', 'PySimpleGUI'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='文件比较器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
    
    with open('文件比较器.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("已创建规格文件: 文件比较器.spec")
    print("可以使用以下命令进行打包:")
    print("pyinstaller 文件比较器.spec")

if __name__ == '__main__':
    print("文件比较器打包工具")
    print("=" * 50)
    
    choice = input("选择操作:\n1. 直接打包\n2. 创建规格文件\n请输入选择 (1/2): ")
    
    if choice == '1':
        build_exe()
    elif choice == '2':
        create_spec_file()
    else:
        print("无效选择")