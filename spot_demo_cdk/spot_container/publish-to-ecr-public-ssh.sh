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

HOST_STRING="${USER}@${HOST}"
IMAGE="public.ecr.aws/n2w1d3c1/${REPO}:${TAG}"
DOCKER_LOGIN="docker login --username AWS --password-stdin public.ecr.aws/n2w1d3c1"

aws ecr-public get-login-password --profile $AWS_DEFAULT_PROFILE --region us-east-1 | ssh -p 20022 $HOST_STRING $DOCKER_LOGIN

ssh -p 20022 $HOST_STRING "docker tag ${REPO}:${TAG} ${IMAGE}"
ssh -p 20022 $HOST_STRING "docker push ${IMAGE}"

