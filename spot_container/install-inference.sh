# Install TensorRT (required for neo-ai-dlr)
export LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:/usr/local/cuda-10.2/lib64:/usr/local/cuda/lib64:/TensorRT-7.2.1.6/lib
export PATH=/usr/local/cuda-10.2/bin:/usr/local/nvidia/bin:/usr/local/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export CUDA_HOME=/usr/local/cuda-10.2

cd /TensorRT-7.2.1.6/python/ && pip3 install tensorrt-7.2.1.6-cp37-none-linux_x86_64.whl
cd /

# Install newer CMake version (required for neo-ai-dlr)
apt remove -y --purge --auto-remove cmake
version=3.19
build=1
mkdir ~/temp
cd ~/temp
wget https://cmake.org/files/v$version/cmake-$version.$build-Linux-x86_64.sh
mkdir /opt/cmake
yes | sh cmake-$version.$build-Linux-x86_64.sh --skip-license --prefix=/opt/cmake
ln -s /opt/cmake/bin/cmake /usr/bin/cmake
cd /

# Install DLR
git clone --recursive https://github.com/neo-ai/neo-ai-dlr
cd neo-ai-dlr
mkdir build
cd build
cmake .. -DUSE_CUDA=ON -DUSE_CUDNN=ON -DUSE_TENSORRT=/TensorRT-7.2.1.6/
make -j4
cd ../python
python3 setup.py install


