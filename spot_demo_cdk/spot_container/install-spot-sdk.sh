if [ $# -ne 1 ]; then
  echo 1>&2 "Usage: $0 SPOT_SDK_VERSION"
  exit 3
fi

SPOT_SDK_VERSION=$1

# Install Spot SDK
git clone --branch v${SPOT_SDK_VERSION} https://github.com/boston-dynamics/spot-sdk.git
cd /spot-sdk/prebuilt

pip3 install --upgrade pip

pip3 install bosdyn_api-${SPOT_SDK_VERSION}-py2.py3-none-any.whl
pip3 install bosdyn_core-${SPOT_SDK_VERSION}-py2.py3-none-any.whl
pip3 install bosdyn_client-${SPOT_SDK_VERSION}-py2.py3-none-any.whl
pip3 install bosdyn_choreography_protos-${SPOT_SDK_VERSION}-py3-none-any.whl
pip3 install bosdyn_choreography_client-${SPOT_SDK_VERSION}-py2.py3-none-any.whl
pip3 install bosdyn_mission-${SPOT_SDK_VERSION}-py2.py3-none-any.whl

# Install OpenCV
pip3 install scikit-build

apt-get install -y cmake gcc g++ \
  && pip3 install opencv-python

apt-get install python-scipy

# Install other requirements
pip3 install Pillow==8.3.2 \
    aiortc==0.9.28 \
    requests==2.24.0 \
    scipy \
    grpcio==1.35.0