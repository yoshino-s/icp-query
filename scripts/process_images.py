import shutil
from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import DBSCAN

SIZE = (500, 190)
THUMBNAIL_SIZE = (50, 19)


def extract_features(image):
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    # gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    thumbnail = cv2.resize(blurred, THUMBNAIL_SIZE, interpolation=cv2.INTER_AREA)
    # hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    # normalized_hist = cv2.normalize(hist, hist).flatten()
    # mean_color = cv2.mean(blurred)[:3]  # 获取 BGR 三个通道的均值
    return thumbnail.flatten()


# 创建输出目录
output_dir = Path("data/clusters")
output_dir.mkdir(parents=True, exist_ok=True)

features = []
imgs: dict[str, np.ndarray] = {}

# 处理图片
for img_path in Path("data/big").glob("*.png"):
    img = cv2.imread(str(img_path))
    resized = cv2.resize(img, SIZE)
    imgs[img_path.name] = resized

    feat = extract_features(resized)
    features.append((img_path, feat))

X = np.array([feat for _, feat in features])

clt = DBSCAN(eps=0.8, min_samples=1, metric="hamming")
labels = clt.fit_predict(X)

# 分组输出
groups = {}
for label, (fname, feat) in zip(labels, features):
    groups.setdefault(label, []).append(fname)

shutil.rmtree(output_dir)

for label, img_paths in groups.items():
    assert len(img_paths) > 2, "每个聚类至少包含3张图片"
    print(f"  Cluster {label}: {len(img_paths)} images")
    cluster_dir = output_dir / f"cluster_{label}"
    cluster_dir.mkdir(parents=True, exist_ok=True)
    for img_path in img_paths:
        dest_path = cluster_dir / img_path.name
        cv2.imwrite(str(dest_path), imgs[img_path.name])

for label, img_paths in groups.items():
    images = []
    for img_path in img_paths:
        img = imgs[img_path.name]
        images.append(img)

    # 上下拼接图片
    concatenated = np.vstack(images)

    # 保存拼接后的图片
    concat_path = output_dir / f"concatenated_cluster_{label}.png"
    cv2.imwrite(str(concat_path), concatenated)

medium_dir = Path("data/medium")
shutil.rmtree(medium_dir, ignore_errors=True)
medium_dir.mkdir(parents=True, exist_ok=True)
# calculate medium of each cluster
for label, img_paths in groups.items():
    all_imgs = [imgs[img_path.name] for img_path in img_paths]
    medium = np.median(np.array(all_imgs), axis=0).astype(np.uint8)
    medium_path = medium_dir / f"{label}.png"
    cv2.imwrite(str(medium_path), medium)
