if [ $# -ne 7 ]; then
  echo 1>&2 "Usage: $0 AWS-PROFILE-NAME SSH-USER SSH-HOST SSH-PORT ECR-REPO TARGET SPOT_SDK_VERSION"
  exit 3
fi

AWS_DEFAULT_PROFILE=$1
USER=$2
HOST=$3
PORT=$4
REPO=$5
TARGET=$6
SPOT_SDK_VERSION=$7
TAG=${TARGET}-${SPOT_SDK_VERSION}

REGION_ARG="profile.${AWS_DEFAULT_PROFILE}.region"
REGION=$(aws configure get ${REGION_ARG})

HOST_STRING="${USER}@${HOST}"
ACCOUNT=$(aws sts get-caller-identity --profile $AWS_DEFAULT_PROFILE | jq -r '.Account')
ECR_REGISTRY="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE="${ECR_REGISTRY}/${REPO}:${TAG}"
DOCKER_LOGIN="docker login --username AWS --password-stdin ${ECR_REGISTRY}"

aws ecr describe-repositories --profile $AWS_DEFAULT_PROFILE --repository-names $REPO || aws ecr create-repository --profile $AWS_DEFAULT_PROFILE --repository-name $REPO

echo $HOST_STRING
echo $DOCKER_LOGIN

aws ecr get-login-password --profile $AWS_DEFAULT_PROFILE | ssh -p $PORT $HOST_STRING $DOCKER_LOGIN

#ssh -p $PORT $HOST_STRING 'rm -rf /tmp/gg; mkdir -p /tmp/gg'

#scp -r -P $PORT Dockerfile.${TARGET} install-spot-sdk.sh shmsrc.patch publish_shmsink.py install-kvs-webrtc-c.sh install-opencv.sh predictor.ag uploaded.jpg $HOST_STRING:/tmp/gg/

if [ "$TARGET" == "spotcore_ai" ]
then
scp -r -P $PORT install-inference.sh TensorRT-7.2.1.6.Ubuntu-18.04.x86_64-gnu.cuda-10.2.cudnn8.0.tar.gz $HOST_STRING:/tmp/gg/
fi

ssh -p $PORT $HOST_STRING "cd /tmp/gg; docker build --build-arg SPOT_SDK_VERSION=${SPOT_SDK_VERSION} -f Dockerfile.${TARGET} -t ${REPO}:${TAG} ."
ssh -p $PORT $HOST_STRING "docker tag ${REPO}:${TAG} ${IMAGE}"
ssh -p $PORT $HOST_STRING "docker push ${IMAGE}"

