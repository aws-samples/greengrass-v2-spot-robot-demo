import logging
import random
import sys

import agent_pb2
import agent_pb2_grpc
import cv2
import grpc
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Uncomment this for grpc debug log
# os.environ['GRPC_VERBOSITY'] = 'DEBUG'
SIZE = 512
TENSOR_SHAPE = [1, 3, 512, 512]
TENSOR_NAME = "data"
DATA_TYPE = 5


class EdgeManagerClient:
    def __init__(self):
        self.agent_socket = "unix:///tmp/aws.greengrass.SageMakerEdgeManager.sock"
        self.agent_channel = grpc.insecure_channel(
            self.agent_socket, options=(("grpc.enable_http_proxy", 0),)
        )
        self.agent_client = agent_pb2_grpc.AgentStub(self.agent_channel)

    def list_models(self):
        return self.agent_client.ListModels(agent_pb2.ListModelsRequest())

    def list_model_tensors(self, models):
        return {
            model.name: {
                "inputs": model.input_tensor_metadatas,
                "outputs": model.output_tensor_metadatas,
            }
            for model in self.list_models().models
        }

    def load_model(self, model_name, model_path):
        load_request = agent_pb2.LoadModelRequest()
        load_request.url = model_path
        load_request.name = model_name
        return self.agent_client.LoadModel(load_request)

    def unload_model(self, name):
        unload_request = agent_pb2.UnLoadModelRequest()
        unload_request.name = name
        return self.agent_client.UnLoadModel(unload_request)

    def predict_image(self, model_name, img):
        logger.info("predict_image()")
        image_tensor = agent_pb2.Tensor()
        image_tensor.byte_data = img.tobytes()
        image_tensor.tensor_metadata.name = TENSOR_NAME
        image_tensor.tensor_metadata.data_type = DATA_TYPE
        image_tensor.tensor_metadata.shape.extend(TENSOR_SHAPE)
        predict_request = agent_pb2.PredictRequest()
        predict_request.name = model_name
        predict_request.tensors.append(image_tensor)
        predict_response = self.agent_client.Predict(predict_request)
        logger.info(predict_response)
        return predict_response

    def get_prediction(self, model_name, img):
        logger.info("get_prediction()")
        # Mean and Std deviation of the RGB colors (collected from Imagenet dataset)

        try:
            mean = [123.68, 116.779, 103.939]
            std = [58.393, 57.12, 57.375]

            frame = self.resize_short_within(img, short=SIZE, max_size=SIZE * 2)
            nn_input_size = SIZE
            nn_input = cv2.resize(frame, (nn_input_size, int(nn_input_size / 4 * 3)))
            nn_input = cv2.copyMakeBorder(
                nn_input,
                int(nn_input_size / 8),
                int(nn_input_size / 8),
                0,
                0,
                cv2.BORDER_CONSTANT,
                value=(0, 0, 0),
            )
            copy_frame = nn_input[:]
            nn_input = nn_input.astype("float32")
            nn_input = nn_input.reshape((nn_input_size * nn_input_size, 3))
            scaled_frame = np.transpose(nn_input)
            scaled_frame[0, :] = scaled_frame[0, :] - mean[0]
            scaled_frame[0, :] = scaled_frame[0, :] / std[0]
            scaled_frame[1, :] = scaled_frame[1, :] - mean[1]
            scaled_frame[1, :] = scaled_frame[1, :] / std[1]
            scaled_frame[2, :] = scaled_frame[2, :] - mean[2]
            scaled_frame[2, :] = scaled_frame[2, :] / std[2]

            predict_response = self.predict_image(model_name, scaled_frame)

            i = 0
            detections = []

            for t in predict_response.tensors:
                # print("Flattened RAW Output Tensor : " + str(i + 1))
                i += 1
                deserialized_bytes = np.frombuffer(t.byte_data, dtype=np.float32)
                detections.append(np.asarray(deserialized_bytes))

            # convert the bounding boxes
            new_list = []
            for index, item in enumerate(detections[2]):
                if index % 4 == 0:
                    new_list.append(detections[2][index - 4 : index])
            detections[2] = new_list[1:]

            # get classes, scores, bboxes
            classes = detections[0]
            scores = detections[1]
            bounding_boxes = new_list[1:]

            # logger.info(bounding_boxes)
            # logger.info(scores)
            # logger.info(classes)

            return bounding_boxes, scores, classes

        except Exception as e:
            logger.error(e)

    def _get_interp_method(self, interp, sizes=()):
        """Get the interpolation method for resize functions.
        The major purpose of this function is to wrap a random interp method selection
        and a auto-estimation method.
    ​
        Parameters
        ----------
        interp : int
            interpolation method for all resizing operations
    ​
            Possible values:
            0: Nearest Neighbors Interpolation.
            1: Bilinear interpolation.
            2: Area-based (resampling using pixel area relation). It may be a
            preferred method for image decimation, as it gives moire-free
            results. But when the image is zoomed, it is similar to the Nearest
            Neighbors method. (used by default).
            3: Bicubic interpolation over 4x4 pixel neighborhood.
            4: Lanczos interpolation over 8x8 pixel neighborhood.
            9: Cubic for enlarge, area for shrink, bilinear for others
            10: Random select from interpolation method metioned above.
            Note:
            When shrinking an image, it will generally look best with AREA-based
            interpolation, whereas, when enlarging an image, it will generally look best
            with Bicubic (slow) or Bilinear (faster but still looks OK).
            More details can be found in the documentation of OpenCV, please refer to
            http://docs.opencv.org/master/da/d54/group__imgproc__transform.html.
        sizes : tuple of int
            (old_height, old_width, new_height, new_width), if None provided, auto(9)
            will return Area(2) anyway.
    ​
        Returns
        -------
        int
            interp method from 0 to 4
        """
        if interp == 9:
            if sizes:
                assert len(sizes) == 4
                oh, ow, nh, nw = sizes
                if nh > oh and nw > ow:
                    return 2
                elif nh < oh and nw < ow:
                    return 3
                else:
                    return 1
            else:
                return 2
        if interp == 10:
            return random.randint(0, 4)
        if interp not in (0, 1, 2, 3, 4):
            raise ValueError("Unknown interp method %d" % interp)

    def resize_short_within(
        self, img, short=512, max_size=1024, mult_base=32, interp=2
    ):
        """
        resizes the short side of the image so the aspect ratio remains the same AND the short
        side matches the convolutional layer for the network
    ​
        Args:
        -----
        img: np.array
            image you want to resize
        short: int
            the size to reshape the image to
        max_size: int
            the max size of the short side
        mult_base: int
            the size scale to readjust the resizer
        interp: int
            see '_get_interp_method'
        Returns:
        --------
        img: np.array
            the resized array
        """
        h, w, _ = img.shape
        im_size_min, im_size_max = (h, w) if w > h else (w, h)
        scale = float(short) / float(im_size_min)
        if np.round(scale * im_size_max / mult_base) * mult_base > max_size:
            # fit in max_size
            scale = float(np.floor(max_size / mult_base) * mult_base) / float(
                im_size_max
            )
        new_w, new_h = (
            int(np.round(w * scale / mult_base) * mult_base),
            int(np.round(h * scale / mult_base) * mult_base),
        )
        img = cv2.resize(
            img,
            (new_w, new_h),
            interpolation=self._get_interp_method(interp, (h, w, new_h, new_w)),
        )
        return img
