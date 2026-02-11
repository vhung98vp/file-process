
import cv2
import numpy as np
from config import APP
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
import torch
from torch.amp import autocast
from vietocr.tool.translate import translate
from concurrent.futures import ThreadPoolExecutor
import copy


class FastPredictor(Predictor):
    def __init__(self, config):
        super().__init__(config)
        self.device = config['device']
        self.model_base = self.model.to(self.device).eval()
        self.model_large = copy.deepcopy(self.model_base)
        self.stream_base = torch.cuda.Stream()
        self.stream_large = torch.cuda.Stream()
        self.target_height = 32
        self.max_width = 512

    def preprocess_batch_opencv(self, images):
        """
        Process OpenCV + Dynamic Padding
        Input: List numpy array (Crop BGR or RGB)
        Output: Tensor (Batch_Size, Channel, Height, Width)
        """
        n_imgs = len(images)
        target_h = self.target_height
        max_w = self.max_width

        resized_imgs = []
        widths = []

        for img in images:
            h, w = img.shape[:2]

            scale = target_h / h
            new_w = int(w * scale)
            new_w = min(new_w, max_w)

            # Add small horizontal padding BEFORE resize (anti cut-off)
            img = cv2.copyMakeBorder(img, 0, 0, 5, 5, cv2.BORDER_CONSTANT, value=0)

            img = cv2.resize(img, (new_w, target_h), interpolation=cv2.INTER_LINEAR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            resized_imgs.append(img)
            widths.append(new_w)

        max_batch_width = max(max(widths), target_h)

        batch_np = np.zeros((n_imgs, target_h, max_batch_width, 3), dtype=np.float32)

        for i, img in enumerate(resized_imgs):
            w = img.shape[1]
            batch_np[i, :, :w, :] = img

        batch_np = batch_np / 255.0
        batch_tensor = torch.tensor(batch_np).permute(0, 3, 1, 2)

        return batch_tensor


    def predict_batch_fast(self, cv2_images, model=None, stream=None):
        if model is None:
            model = self.model_base
        if stream is None:
            stream = self.stream_base
        
        batch_tensor = self.preprocess_batch_opencv(cv2_images) 
        batch_tensor = batch_tensor.to(self.device, non_blocking=True)
        
        with torch.cuda.stream(stream):
            with torch.inference_mode():
                with autocast(device_type='cuda', dtype=torch.float16):
                    indices = translate(batch_tensor, model)[0]

        return [self.vocab.decode(indice) for indice in indices.tolist()]


    def _split_bucket(self, cv2_images):
        bucket_small = []
        bucket_large = []

        for idx, img in enumerate(cv2_images):
            h, w = img.shape[:2]
            scaled_w = w * (self.target_height / h)

            if scaled_w < self.max_width / 2:
                bucket_small.append((idx, img))
            else:
                bucket_large.append((idx, img))

        return bucket_small, bucket_large


    def _run_bucket(self, bucket, batch_size, *, model, stream):
        out = []
        for i in range(0, len(bucket), batch_size):
            chunk = bucket[i:i + batch_size]
            imgs = [x[1] for x in chunk]

            texts = self.predict_batch_fast(imgs, model=model, stream=stream)

            for k, text in enumerate(texts):
                original_idx = chunk[k][0]
                out.append((original_idx, text.strip()))

        return out



    def predict_batch_bucket(self, cv2_images):
        if len(cv2_images) == 0:
            return []
        if len(cv2_images) <= 32:
            return self.predict_batch_fast(cv2_images)

        bucket_small, bucket_large = self._split_bucket(cv2_images)

        results_map = {}
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []

            if bucket_small:
                futures.append(
                    executor.submit(
                        self._run_bucket,
                        bucket_small,
                        APP["small_batch_size"],
                        model=self.model_base,
                        stream=self.stream_base,
                    )
                )

            if bucket_large:
                futures.append(
                    executor.submit(
                        self._run_bucket,
                        bucket_large,
                        APP["large_batch_size"],
                        model=self.model_large,
                        stream=self.stream_large,
                    )
                )

            for future in futures:
                for original_idx, text in future.result():
                    results_map[original_idx] = text

        final_results = [results_map[i] for i in range(len(cv2_images))]
        return final_results


def vietocr_predictor():
    config = Cfg.load_config_from_file('./models/config.yml')
    config['device'] = 'cuda'
    return FastPredictor(config)