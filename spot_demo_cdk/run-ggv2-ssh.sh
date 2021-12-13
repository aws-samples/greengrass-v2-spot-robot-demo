if [ $# -ne 8 ]; then
  echo 1>&2 "Usage: $0 AWS-PROFILE-NAME SSH-USER SSH-HOST PORT ECR-REPO TARGET SPOT_SDK_VERSION THING-NAME"
  exit 3
fi

AWS_PROFILE=$1
USER=$2
HOST=$3
PORT=$4
REPO=$5
TARGET=$6
SPOT_SDK_VERSION=$7
TAG=${TARGET}-${SPOT_SDK_VERSION}
THING_NAME=$8

AWS_ACCESS_KEY_ID=$(aws configure get $AWS_PROFILE.aws_access_key_id)
AWS_SECRET_ACCESS_KEY=$(aws configure get $AWS_PROFILE.aws_secret_access_key)
REGION_ARG="profile.${AWS_PROFILE}.region"
REGION=$(aws configure get ${REGION_ARG})

HOST_STRING="${USER}@${HOST}"
ACCOUNT=$(aws sts get-caller-identity --profile $AWS_PROFILE | jq -r '.Account')
ECR_REGISTRY="${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE="${ECR_REGISTRY}/${REPO}:${TAG}"
DOCKER_LOGIN="docker login --username AWS --password-stdin ${ECR_REGISTRY}"

echo $IMAGE

ssh -p $PORT $HOST_STRING 'mkdir -p /home/spot/ggv2'

aws ecr get-login-password --profile $AWS_PROFILE | ssh -p $PORT $HOST_STRING $DOCKER_LOGIN
ssh -p $PORT $HOST_STRING "docker pull ${IMAGE}"

if [ "$TARGET" == "spotcore_ai" ]
then
  ssh -p $PORT $HOST_STRING "docker run -d --name aws-iot-greengrass-v2 --gpus all --privileged --rm --entrypoint /greengrass-entrypoint.sh -v /opt/payload_credentials:/payload_credentials -v /home/spot/ggv2:/greengrass/v2 -e AWS_REGION=${AWS_DEFAULT_REGION} -e THING_NAME=${THING_NAME} -e THING_GROUP_NAME=spot_group -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} --net=host ${IMAGE}"

  ## If using AWS_SESSION_TOKEN
  #ssh -p $PORT $HOST_STRING "docker run -d --name aws-iot-greengrass-v2 --gpus all --privileged --rm --entrypoint /greengrass-entrypoint.sh -v /opt/payload_credentials:/payload_credentials -v /home/spot/ggv2:/greengrass/v2 -e AWS_REGION=${AWS_REGION} -e THING_NAME=${THING_NAME} -e THING_GROUP_NAME=spot_group -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} -e AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN} --net=host ${IMAGE}"
else
  ssh -p $PORT $HOST_STRING "docker run -d --name aws-iot-greengrass-v2 --privileged --rm --entrypoint /greengrass-entrypoint.sh -v /opt/payload_credentials:/payload_credentials -v /home/spot/ggv2:/greengrass/v2 -e AWS_REGION=${AWS_DEFAULT_REGION} -e THING_NAME=${THING_NAME} -e THING_GROUP_NAME=spot_group -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} --net=host ${IMAGE}"

  ## If using AWS_SESSION_TOKEN
  #ssh -p $PORT $HOST_STRING "docker run -d --name aws-iot-greengrass-v2 --privileged --rm --entrypoint /greengrass-entrypoint.sh -v /opt/payload_credentials:/payload_credentials -v /home/spot/ggv2:/greengrass/v2 -e AWS_REGION=${AWS_REGION} -e THING_NAME=${THING_NAME} -e THING_GROUP_NAME=spot_group -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} -e AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN} --net=host ${IMAGE}"
fi

