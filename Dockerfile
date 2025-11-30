# 使用官方轻量级 Python 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# -------------------------------------------------------
# ✨ 关键修改 1：安装系统级依赖 (ping 命令)
# -------------------------------------------------------
# 更新软件源并安装 iputils-ping (提供 ping 命令)
# rm -rf ... 是为了清理缓存减小镜像体积
RUN apt-get update && apt-get install -y \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 库
# (加了清华源 -i ... 是为了让你下载快一点，可选)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目所有代码
COPY . .

# -------------------------------------------------------
# ✨ 关键修改 2：修正端口号 (对应 app.py 的 6030)
# -------------------------------------------------------
EXPOSE 6030

# 启动命令
CMD ["python", "app.py"]# 使用官方轻量级 Python 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# -------------------------------------------------------
# ✨ 关键修改 1：安装系统级依赖 (ping 命令)
# -------------------------------------------------------
# 更新软件源并安装 iputils-ping (提供 ping 命令)
# rm -rf ... 是为了清理缓存减小镜像体积
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 库
# (加了清华源 -i ... 是为了让下载快一点)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目所有代码
COPY . .

#  端口号 (对应 app.py )

EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]