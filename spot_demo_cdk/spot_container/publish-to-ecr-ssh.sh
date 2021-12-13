if [ $# -ne 6 ]; then
  echo 1>&2 "Usage: $0 AWS-PROFILE-NAME SSH-USER SSH-HOST ECR-REPO TARGET SPOT_SDK_VERSION"
  exit 3
fi

AWS_DEFAULT_PROFILE=$1
USER=$2
HOST=$3
REPO=$4
TARGET=$5
SPOT_SDK_VERSION=$6
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

aws ecr get-login-password --profile $AWS_DEFAULT_PROFILE | ssh -p 20022 $HOST_STRING $DOCKER_LOGIN

ssh -p 20022 $HOST_STRING 'rm -rf /tmp/gg; mkdir -p /tmp/gg'

scp -r -P 20022 Dockerfile.${TARGET} greengrass-entrypoint.sh install-spot-sdk.sh $HOST_STRING:/tmp/gg/

if [ "$TARGET" == "spotcore_ai" ]
then
scp -r -P 20022 install-inference.sh TensorRT-7.2.1.6.Ubuntu-18.04.x86_64-gnu.cuda-10.2.cudnn8.0.tar.gz $HOST_STRING:/tmp/gg/
fi

ssh -p 20022 $HOST_STRING "cd /tmp/gg; docker build --build-arg SPOT_SDK_VERSION=${SPOT_SDK_VERSION} -f Dockerfile.${TARGET} -t ${REPO}:${TAG} ."
ssh -p 20022 $HOST_STRING "docker tag ${REPO}:${TAG} ${IMAGE}"
ssh -p 20022 $HOST_STRING "docker push ${IMAGE}"

