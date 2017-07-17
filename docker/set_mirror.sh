if [ $USE_MIRROR ]; then
    sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories;
    mkdir -p ~/.pip;
    echo "[global]" > ~/.pip/pip.conf;
    echo "format = columns" >> ~/.pip/pip.conf;
    echo "index-url = https://mirrors.ustc.edu.cn/pypi/web/simple" >> ~/.pip/pip.conf;
fi