#!/bin/sh

set -e

# Path that initial installation files are copied to
INIT_JAR_PATH=/opt/greengrassv2/

# If we have not already installed Greengrass
if [ ! -d $GGC_ROOT_PATH/alts/current/distro ]; then
	# Install Greengrass via the main installer, but do not start running
	env
	echo "Installing Greengrass for the first time..."
	java -Droot=$GGC_ROOT_PATH -Dlog.store=FILE -Dlog.level=INFO -jar $INIT_JAR_PATH/lib/Greengrass.jar --component-default-user root:root --provision true --aws-region $AWS_REGION --thing-name $THING_NAME --thing-group-name $THING_GROUP_NAME --start false --deploy-dev-tools true
else
	echo "Reusing existing Greengrass installation..."
fi

echo "Starting Greengrass..."
# Start greengrass kernel via the loader script and register container as a thing
sh $GGC_ROOT_PATH/alts/current/distro/bin/loader

