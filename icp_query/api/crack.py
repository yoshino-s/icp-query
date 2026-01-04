import base64
import logging
import os
from pathlib import Path

import cv2
import ddddocr
import numpy as np
import onnxruntime

logging.basicConfig(level=logging.INFO)


def create_onnx_session(model_path: str):
    """Create an ONNX Runtime session using GPU if available.

    Detection logic:
    - If the system has CUDAExecutionProvider available and the env var
      USE_ONNX_CUDA is not explicitly set to 0/false, we enable CUDA.
    - Fallback to CPUExecutionProvider otherwise.
    """
    available_providers = onnxruntime.get_available_providers()
    use_cuda_env = os.getenv("USE_ONNX_CUDA")
    # Consider a set of accelerated providers (CUDA, TensorRT, CoreML, DML, ROCm, etc.)
    accelerated_candidates = [
        "CUDAExecutionProvider",
        "TensorrtExecutionProvider",
        "DmlExecutionProvider",
        "ROCMExecutionProvider",
        "CoreMLExecutionProvider",
        "OpenVINOExecutionProvider",
        "MIGraphXExecutionProvider",
    ]

    # Find the first available accelerated provider from the list
    active_accel = None
    for p in accelerated_candidates:
        if p in available_providers:
            active_accel = p
            break

    # Environment variable to control CUDA/acceleration usage. If USE_ONNX_CUDA is set to
    # 0/false/no the acceleration is disabled even when available.
    disabled = use_cuda_env is not None and use_cuda_env.lower() in ("0", "false", "no")

    if active_accel and not disabled:
        providers = [active_accel, "CPUExecutionProvider"]
    else:
        providers = ["CPUExecutionProvider"]

    logging.info(
        "ONNX available providers: %s, active providers: %s",
        available_providers,
        providers,
    )

    return onnxruntime.InferenceSession(model_path, providers=providers)


session = create_onnx_session("siamese.onnx")

SIZE = (500, 190)


medium_imgs = Path(__file__).parent.parent / "data" / "medium"

bg_files = [cv2.imread(str(bg_file)) for bg_file in medium_imgs.glob("*.png")]


def extract_features(image):
    # assert size is SIZE
    assert image.shape[1] == SIZE[0] and image.shape[0] == SIZE[1]

    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    # gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    thumbnail = cv2.resize(blurred, (50, 20), interpolation=cv2.INTER_AREA)
    # hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    # normalized_hist = cv2.normalize(hist, hist).flatten()
    # mean_color = cv2.mean(blurred)[:3]  # 获取 BGR 三个通道的均值
    return thumbnail.flatten()


bg_features = [extract_features(bg) for bg in bg_files]


def find_background(img: np.ndarray):
    global bg_files

    features = extract_features(img)
    distances = []
    for bg_feature in bg_features:
        distance = np.linalg.norm(features - bg_feature)
        distances.append(distance)
    min_distance_index = np.argmin(distances)
    bg = bg_files[min_distance_index]

    # calculate the diff
    assert bg.shape == img.shape, f"bg shape error {bg.shape}, img shape {img.shape}"
    diff = cv2.absdiff(img, bg)
    # diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    # _, diff = cv2.threshold(diff, thresh, 255, cv2.THRESH_BINARY)
    diff = cv2.bitwise_not(diff)

    return bg, diff


class Crack:
    def __init__(self):
        self.detect_model = ddddocr.DdddOcr(det=True, show_ad=False)

    def read_base64_image(self, base64_string):
        img_data = base64.b64decode(base64_string)

        np_array = np.frombuffer(img_data, np.uint8)

        img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        return img

    def detect(self, big_img, show=False):
        img = self.read_base64_image(big_img)
        _, diff = find_background(img)
        self.big_img = img

        out = self.detect_model.detection(
            img_bytes=cv2.imencode(".png", diff)[1].tobytes()
        )
        r = [
            [int(box[0]), int(box[1]), int(box[2] - box[0]), int(box[3] - box[1])]
            for box in out
        ]
        if show:
            copy = self.big_img.copy()
            for box in r:
                cv2.rectangle(
                    copy,
                    (box[0], box[1]),
                    (box[0] + box[2], box[1] + box[3]),
                    (0, 255, 0),
                    2,
                )
            cv2.imshow("img", copy)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        if len(r) != 5:
            raise ValueError("检测到的验证码框数量不正确")
        return r

    def siamese(self, small_img, boxes, show=False):
        positions = [165, 200, 231, 265]
        result_list = []

        big_img_copy = self.big_img.copy()
        small_imgs = self.read_base64_image(small_img)

        for idx, x in enumerate(positions):
            if len(result_list) == 4:
                break
            raw_image2 = small_imgs[11 : 11 + 28, x : x + 26]
            img2 = cv2.cvtColor(raw_image2, cv2.COLOR_BGR2RGB)
            img2 = cv2.resize(img2, (105, 105))
            image_data_2 = np.array(img2) / 255.0
            image_data_2 = np.transpose(image_data_2, (2, 0, 1))
            image_data_2 = np.expand_dims(image_data_2, axis=0).astype(np.float32)
            for box in boxes:
                raw_image1 = self.big_img[
                    box[1] : box[1] + box[3] + 2, box[0] : box[0] + box[2] + 2
                ]
                img1 = cv2.cvtColor(raw_image1, cv2.COLOR_BGR2RGB)
                img1 = cv2.resize(img1, (105, 105))

                image_data_1 = np.array(img1) / 255.0
                image_data_1 = np.transpose(image_data_1, (2, 0, 1))
                image_data_1 = np.expand_dims(image_data_1, axis=0).astype(np.float32)

                inputs = {"input": image_data_1, "input.53": image_data_2}
                output = session.run(None, inputs)
                output_sigmoid = 1 / (1 + np.exp(-output[0]))
                res = output_sigmoid[0][0]
                if res >= 0.7:
                    result_list.append([box[0], box[1]])
                    cv2.rectangle(
                        big_img_copy,
                        (box[0], box[1]),
                        (box[0] + box[2], box[1] + box[3]),
                        (0, 255, 0),
                        2,
                    )
                    cv2.putText(
                        big_img_copy,
                        str(idx),
                        (box[0], box[1]),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1,
                    )
                    break

        if show:
            concatenated = np.vstack((big_img_copy, small_imgs))
            cv2.imshow("img", concatenated)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return result_list


if __name__ == "__main__":
    crack = Crack()
    boxes = crack.detect("./1.png")
    print(crack.siamese("./2.png", boxes))
