from autogluon.vision import ImagePredictor

classifier_model_path = "/models/predictor.ag"
predictor = ImagePredictor.load(classifier_model_path)


def predict():
    result = int(predictor.predict("/images/local.jpg")[0])
    return {"result": result}
