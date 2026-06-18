# training/ — train member models (Part 1b)

LoRA SFT pipeline that turns the `data_synthesis/` corpora into **member models** for the
consortium.

Pipeline: `prepare_data.py` -> `pack_data.py` -> `train_rehearsal.py` -> `merge_ckpt.py`.
`train_full.py` is the full-SFT variant, `chat_template.py` holds the THINK/ANSWER template,
and `Dockerfile` builds the training image. Heavy deps: `../requirements.txt`.

Members feed `../consortium/` (fusion) and are scored by `../evaluation/`.
