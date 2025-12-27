## moderation_image_catornotclassifier

FastStream/RabbitMQ worker that consumes moderation image jobs, downloads an image from S3/SeaweedFS, runs a cat-vs-not model, and publishes a per-service moderation result.

### Model artifact (trainer output)

The trainer currently saves `ai/catornot_imageclassifier/outputs/model.pth` as a checkpoint dict:
- keys: `epoch`, `model_state_dict`, `optimizer_state_dict`, `loss`
- the worker loads `model_state_dict` into the `CatCNNModel` architecture (see `app/inference.py`)

Recommended container mount: `/model/model.pth` (default `MODEL_PATH`).

### Key env vars

- `AMQP_URL`
- `S3_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`
- `MODEL_PATH`, `TORCH_DEVICE` (`cpu` default), `CAT_THRESHOLD`, `NOT_CAT_THRESHOLD`
- `IMAGE_BUCKET` (and optional `ALLOWED_BUCKETS=bucket-a,bucket-b`)
- `MAX_IMAGE_BYTES`, `MAX_IMAGE_PIXELS`
