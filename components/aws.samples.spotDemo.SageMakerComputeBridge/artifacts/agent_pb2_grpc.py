# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import agent_pb2 as agent__pb2


class AgentStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Predict = channel.unary_unary(
            "/AWS.SageMaker.Edge.Agent/Predict",
            request_serializer=agent__pb2.PredictRequest.SerializeToString,
            response_deserializer=agent__pb2.PredictResponse.FromString,
        )
        self.LoadModel = channel.unary_unary(
            "/AWS.SageMaker.Edge.Agent/LoadModel",
            request_serializer=agent__pb2.LoadModelRequest.SerializeToString,
            response_deserializer=agent__pb2.LoadModelResponse.FromString,
        )
        self.UnLoadModel = channel.unary_unary(
            "/AWS.SageMaker.Edge.Agent/UnLoadModel",
            request_serializer=agent__pb2.UnLoadModelRequest.SerializeToString,
            response_deserializer=agent__pb2.UnLoadModelResponse.FromString,
        )
        self.ListModels = channel.unary_unary(
            "/AWS.SageMaker.Edge.Agent/ListModels",
            request_serializer=agent__pb2.ListModelsRequest.SerializeToString,
            response_deserializer=agent__pb2.ListModelsResponse.FromString,
        )
        self.DescribeModel = channel.unary_unary(
            "/AWS.SageMaker.Edge.Agent/DescribeModel",
            request_serializer=agent__pb2.DescribeModelRequest.SerializeToString,
            response_deserializer=agent__pb2.DescribeModelResponse.FromString,
        )
        self.CaptureData = channel.unary_unary(
            "/AWS.SageMaker.Edge.Agent/CaptureData",
            request_serializer=agent__pb2.CaptureDataRequest.SerializeToString,
            response_deserializer=agent__pb2.CaptureDataResponse.FromString,
        )
        self.GetCaptureDataStatus = channel.unary_unary(
            "/AWS.SageMaker.Edge.Agent/GetCaptureDataStatus",
            request_serializer=agent__pb2.GetCaptureDataStatusRequest.SerializeToString,
            response_deserializer=agent__pb2.GetCaptureDataStatusResponse.FromString,
        )


class AgentServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Predict(self, request, context):
        """
        perform inference on a model.

        Note:
        1. users can chose to send the tensor data in the protobuf message or
        through a shared memory segment on a per tensor basis, the Predict
        method with handle the decode transparently.
        2. serializing large tensors into the protobuf message can be quite expensive,
        based on our measurements it is recommended to use shared memory of
        tenors larger than 256KB.
        3. SMEdge IPC server will not use shared memory for returning output tensors,
        i.e., the output tensor data will always send in byte form encoded
        in the tensors of PredictResponse.
        4. currently SMEdge IPC server cannot handle concurrent predict calls, all
        these call will be serialized under the hood. this shall be addressed
        in a later release.
        Status Codes:
        1. OK - prediction is successful
        2. UNKNOWN - unknown error has occurred
        3. INTERNAL - an internal error has occurred
        4. NOT_FOUND - when model not found
        5. INVALID_ARGUMENT - when tenors types mismatch

        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def LoadModel(self, request, context):
        """
        perform load for a model
        Note:
        1. currently only local filesystem paths are supported for loading models.
        2. currently only one model could be loaded at any time, loading of multiple
        models simultaneously shall be implemented in the future.
        3. users are required to unload any loaded model to load another model.
        Status Codes:
        1. OK - load is successful
        2. UNKNOWN - unknown error has occurred
        3. INTERNAL - an internal error has occurred
        4. NOT_FOUND - model doesn't exist at the url
        5. ALREADY_EXISTS - model with the same name is already loaded
        6. RESOURCE_EXHAUSTED - memory is not available to load the model
        7. FAILED_PRECONDITION - model package could not be loaded

        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def UnLoadModel(self, request, context):
        """
        perform unload for a model
        Status Codes:
        1. OK - unload is successful
        2. UNKNOWN - unknown error has occurred
        3. INTERNAL - an internal error has occurred
        4. NOT_FOUND - model doesn't exist

        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def ListModels(self, request, context):
        """
        lists the loaded models
        Status Codes:
        1. OK - unload is successful
        2. UNKNOWN - unknown error has occurred
        3. INTERNAL - an internal error has occurred

        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def DescribeModel(self, request, context):
        """
        describes a model
        Status Codes:
        1. OK - load is successful
        2. UNKNOWN - unknown error has occurred
        3. INTERNAL - an internal error has occurred
        4. NOT_FOUND - model doesn't exist at the url

        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def CaptureData(self, request, context):
        """
        allows users to capture input and output tensors along with auxiliary data.
        Status Codes:
        1. OK - data capture successfully initiated
        2. UNKNOWN - unknown error has occurred
        3. INTERNAL - an internal error has occurred
        5. ALREADY_EXISTS - capture initiated for the given `capture_id`
        6. RESOURCE_EXHAUSTED - buffer is full cannot accept any more requests.
        7. OUT_OF_RANGE - timestamp is in the future.
        8. INVALID_ARGUMENT - capture_id is not of expected format or input tensor paramater is invalid
        9. FAILED_PRECONDITION - Indicates failed network access, when using cloud for capture data.

        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def GetCaptureDataStatus(self, request, context):
        """
        allows users to query status of capture data operation
        Status Codes:
        1. OK - data capture successfully initiated
        2. UNKNOWN - unknown error has occurred
        3. INTERNAL - an internal error has occurred
        4. NOT_FOUND - given capture id doesn't exist.

        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


def add_AgentServicer_to_server(servicer, server):
    rpc_method_handlers = {
        "Predict": grpc.unary_unary_rpc_method_handler(
            servicer.Predict,
            request_deserializer=agent__pb2.PredictRequest.FromString,
            response_serializer=agent__pb2.PredictResponse.SerializeToString,
        ),
        "LoadModel": grpc.unary_unary_rpc_method_handler(
            servicer.LoadModel,
            request_deserializer=agent__pb2.LoadModelRequest.FromString,
            response_serializer=agent__pb2.LoadModelResponse.SerializeToString,
        ),
        "UnLoadModel": grpc.unary_unary_rpc_method_handler(
            servicer.UnLoadModel,
            request_deserializer=agent__pb2.UnLoadModelRequest.FromString,
            response_serializer=agent__pb2.UnLoadModelResponse.SerializeToString,
        ),
        "ListModels": grpc.unary_unary_rpc_method_handler(
            servicer.ListModels,
            request_deserializer=agent__pb2.ListModelsRequest.FromString,
            response_serializer=agent__pb2.ListModelsResponse.SerializeToString,
        ),
        "DescribeModel": grpc.unary_unary_rpc_method_handler(
            servicer.DescribeModel,
            request_deserializer=agent__pb2.DescribeModelRequest.FromString,
            response_serializer=agent__pb2.DescribeModelResponse.SerializeToString,
        ),
        "CaptureData": grpc.unary_unary_rpc_method_handler(
            servicer.CaptureData,
            request_deserializer=agent__pb2.CaptureDataRequest.FromString,
            response_serializer=agent__pb2.CaptureDataResponse.SerializeToString,
        ),
        "GetCaptureDataStatus": grpc.unary_unary_rpc_method_handler(
            servicer.GetCaptureDataStatus,
            request_deserializer=agent__pb2.GetCaptureDataStatusRequest.FromString,
            response_serializer=agent__pb2.GetCaptureDataStatusResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "AWS.SageMaker.Edge.Agent", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


# This class is part of an EXPERIMENTAL API.
class Agent(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Predict(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/AWS.SageMaker.Edge.Agent/Predict",
            agent__pb2.PredictRequest.SerializeToString,
            agent__pb2.PredictResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def LoadModel(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/AWS.SageMaker.Edge.Agent/LoadModel",
            agent__pb2.LoadModelRequest.SerializeToString,
            agent__pb2.LoadModelResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def UnLoadModel(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/AWS.SageMaker.Edge.Agent/UnLoadModel",
            agent__pb2.UnLoadModelRequest.SerializeToString,
            agent__pb2.UnLoadModelResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def ListModels(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/AWS.SageMaker.Edge.Agent/ListModels",
            agent__pb2.ListModelsRequest.SerializeToString,
            agent__pb2.ListModelsResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def DescribeModel(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/AWS.SageMaker.Edge.Agent/DescribeModel",
            agent__pb2.DescribeModelRequest.SerializeToString,
            agent__pb2.DescribeModelResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def CaptureData(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/AWS.SageMaker.Edge.Agent/CaptureData",
            agent__pb2.CaptureDataRequest.SerializeToString,
            agent__pb2.CaptureDataResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

    @staticmethod
    def GetCaptureDataStatus(
        request,
        target,
        options=(),
        channel_credentials=None,
        call_credentials=None,
        insecure=False,
        compression=None,
        wait_for_ready=None,
        timeout=None,
        metadata=None,
    ):
        return grpc.experimental.unary_unary(
            request,
            target,
            "/AWS.SageMaker.Edge.Agent/GetCaptureDataStatus",
            agent__pb2.GetCaptureDataStatusRequest.SerializeToString,
            agent__pb2.GetCaptureDataStatusResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
        )

