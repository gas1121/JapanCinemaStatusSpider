if [ $USE_MIRROR ]; then
    sed -i 's/httpredir.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list;
    sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list;
    mkdir -p ~/.pip;
    echo "[global]" > ~/.pip/pip.conf;
    echo "format = columns" >> ~/.pip/pip.conf;
    echo "index-url = https://mirrors.ustc.edu.cn/pypi/web/simple" >> ~/.pip/pip.conf;
fi