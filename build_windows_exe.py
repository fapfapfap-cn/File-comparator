#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在macOS上构建Windows可执行文件的脚本
使用Docker容器模拟Windows环境进行交叉编译
"""

import os
import sys
import subprocess
import shutil

def check_docker():
    """检查Docker是否已安装并运行"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker已安装: {result.stdout.strip()}")
        
        # 检查Docker是否运行
        result = subprocess.run(['docker', 'info'], 
                              capture_output=True, text=True, check=True)
        print("✅ Docker服务正在运行")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker未安装或未运行")
        print("请先安装Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False

def create_dockerfile():
    """创建用于Windows交叉编译的Dockerfile"""
    dockerfile_content = '''# 使用Wine来模拟Windows环境
FROM ubuntu:20.04

# 设置非交互模式
ENV DEBIAN_FRONTEND=noninteractive

# 安装必要的包
RUN apt-get update && apt-get install -y \
    wget \
    software-properties-common \
    gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# 添加Wine仓库
RUN wget -nc https://dl.winehq.org/wine-builds/winehq.key && \
    apt-key add winehq.key && \
    add-apt-repository 'deb https://dl.winehq.org/wine-builds/ubuntu/ focal main'

# 安装Wine和Python
RUN apt-get update && apt-get install -y \
    winehq-stable \
    python3 \
    python3-pip \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# 设置Wine环境
ENV WINEPREFIX=/root/.wine
ENV WINEARCH=win64
ENV DISPLAY=:99

# 初始化Wine
RUN Xvfb :99 -screen 0 1024x768x16 & \
    sleep 5 && \
    winecfg

# 下载并安装Windows版Python
RUN wget https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe && \
    Xvfb :99 -screen 0 1024x768x16 & \
    sleep 5 && \
    wine python-3.11.0-amd64.exe /quiet InstallAllUsers=1 PrependPath=1

# 设置工作目录
WORKDIR /app

# 复制应用文件
COPY . /app/

# 安装Python依赖
RUN Xvfb :99 -screen 0 1024x768x16 & \
    sleep 5 && \
    wine python -m pip install --upgrade pip && \
    wine python -m pip install pyinstaller PySimpleGUI openpyxl

# 构建脚本
CMD ["bash", "-c", "Xvfb :99 -screen 0 1024x768x16 & sleep 5 && wine python -m PyInstaller --onefile --noconsole --name=文件比较器 --hidden-import=openpyxl --hidden-import=PySimpleGUI main.py"]
'''
    
    with open('Dockerfile.windows', 'w', encoding='utf-8') as f:
        f.write(dockerfile_content)
    
    print("✅ 已创建 Dockerfile.windows")

def build_docker_image():
    """构建Docker镜像"""
    print("🔨 开始构建Docker镜像...")
    print("⚠️  首次构建可能需要10-20分钟，请耐心等待")
    
    try:
        cmd = ['docker', 'build', '-f', 'Dockerfile.windows', '-t', 'python-wine-builder', '.']
        result = subprocess.run(cmd, check=True)
        print("✅ Docker镜像构建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker镜像构建失败: {e}")
        return False

def build_windows_exe():
    """在Docker容器中构建Windows可执行文件"""
    print("🔨 开始在Docker容器中构建Windows可执行文件...")
    
    try:
        # 创建输出目录
        os.makedirs('dist_windows', exist_ok=True)
        
        # 运行Docker容器进行构建
        cmd = [
            'docker', 'run', '--rm',
            '-v', f'{os.getcwd()}:/app',
            '-v', f'{os.getcwd()}/dist_windows:/app/dist',
            'python-wine-builder'
        ]
        
        result = subprocess.run(cmd, check=True)
        print("✅ Windows可执行文件构建成功")
        
        # 检查生成的文件
        dist_dir = 'dist_windows'
        if os.path.exists(dist_dir):
            print(f"\n📁 生成的Windows文件位于: {os.path.abspath(dist_dir)}")
            for file in os.listdir(dist_dir):
                file_path = os.path.join(dist_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"  📄 {file} ({size/1024/1024:.1f} MB)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Windows可执行文件构建失败: {e}")
        return False

def create_simple_solution():
    """创建简化的解决方案说明"""
    solution_content = '''# 在macOS上生成Windows可执行文件的解决方案

## 方案一：使用Docker（推荐）

### 前提条件
1. 安装Docker Desktop for Mac
2. 确保Docker服务正在运行

### 使用步骤
```bash
# 运行Windows构建脚本
python build_windows_exe.py
```

脚本会自动：
1. 检查Docker环境
2. 创建包含Wine和Windows Python的Docker镜像
3. 在容器中构建Windows .exe文件
4. 将结果输出到 `dist_windows/` 目录

## 方案二：使用GitHub Actions（云端构建）

创建 `.github/workflows/build.yml`：

```yaml
name: Build Executables

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller PySimpleGUI openpyxl
    - name: Build Windows executable
      run: |
        pyinstaller --onefile --noconsole --name=文件比较器 --hidden-import=openpyxl --hidden-import=PySimpleGUI main.py
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: windows-executable
        path: dist/

  build-macos:
    runs-on: macos-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller PySimpleGUI openpyxl
    - name: Build macOS executable
      run: |
        pyinstaller --onedir --windowed --name=文件比较器 --hidden-import=openpyxl --hidden-import=PySimpleGUI main.py
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: macos-executable
        path: dist/
```

## 方案三：使用虚拟机

1. 安装Parallels Desktop或VMware Fusion
2. 创建Windows虚拟机
3. 在虚拟机中安装Python和依赖
4. 运行PyInstaller构建

## 方案四：使用云服务

### 使用Replit
1. 在Replit上创建Python项目
2. 上传代码文件
3. 安装依赖并运行PyInstaller

### 使用CodeSandbox
1. 创建Python环境
2. 上传项目文件
3. 在线构建可执行文件

## 注意事项

1. **Docker方案**：首次构建时间较长，但后续构建较快
2. **GitHub Actions**：免费且自动化，但需要推送到GitHub
3. **虚拟机方案**：最可靠，但需要Windows许可证
4. **云服务方案**：简单快捷，但可能有文件大小限制

## 推荐流程

对于个人开发者，推荐使用GitHub Actions方案：
1. 将代码推送到GitHub仓库
2. 配置GitHub Actions工作流
3. 每次推送代码时自动构建多平台可执行文件
4. 从Actions页面下载构建结果
'''
    
    with open('Windows构建方案.md', 'w', encoding='utf-8') as f:
        f.write(solution_content)
    
    print("✅ 已创建 Windows构建方案.md")

def main():
    print("🚀 macOS上构建Windows可执行文件")
    print("=" * 50)
    
    print("\n选择构建方案:")
    print("1. 使用Docker构建（需要Docker Desktop）")
    print("2. 创建构建方案说明文档")
    print("3. 退出")
    
    choice = input("\n请输入选择 (1/2/3): ")
    
    if choice == '1':
        if not check_docker():
            return
        
        create_dockerfile()
        
        print("\n⚠️  注意：首次构建Docker镜像可能需要10-20分钟")
        confirm = input("是否继续？(y/N): ")
        
        if confirm.lower() in ['y', 'yes']:
            if build_docker_image():
                build_windows_exe()
        else:
            print("已取消构建")
            
    elif choice == '2':
        create_simple_solution()
        print("\n📖 已创建详细的构建方案说明文档")
        
    elif choice == '3':
        print("👋 再见！")
        
    else:
        print("❌ 无效选择")

if __name__ == '__main__':
    main()