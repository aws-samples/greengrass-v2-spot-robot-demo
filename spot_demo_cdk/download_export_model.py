import gluoncv as gcv
from gluoncv.utils import export_block
import tarfile
import os

MODEL_NAME = "ssd_512_mobilenet1.0_voc"
MODEL_DIR = "./pretrained_models/{}".format(MODEL_NAME)

# create model directory
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR, exist_ok=True)

# export model
net = gcv.model_zoo.get_model(MODEL_NAME, pretrained=True)
export_block(
    "{}/{}".format(MODEL_DIR, MODEL_NAME),
    net,
    preprocess=True,
    layout="HWC",
)

# create model archive
with tarfile.open("{}.tar.gz".format(MODEL_DIR), "w:gz") as tar:
    tar.add(
        MODEL_DIR,
        arcname=os.path.basename(MODEL_NAME),
    )

print("Done.")
