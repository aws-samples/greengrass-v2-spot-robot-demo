
apt-get install -y cmake pkg-config libssl-dev libcurl4-openssl-dev liblog4cplus-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base-apps gstreamer1.0-plugins-bad gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools

git clone --recursive https://github.com/awslabs/amazon-kinesis-video-streams-webrtc-sdk-c.git

cd /amazon-kinesis-video-streams-webrtc-sdk-c && git apply /shmsrc.patch

mkdir -p build; cd build; 

cmake ..

make

