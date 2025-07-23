#!/usr/bin/env python
"""Robust extractor + BLIP-2 captioner."""
from logconf import logging
from pathlib import Path
from itertools import chain
from rich.progress import Progress

from unstructured.partition.auto import partition
from unstructured.documents.elements import Element                                  # type base
# from transformers import Blip2Processor, Blip2ForConditionalGeneration
from transformers import BlipProcessor, BlipForConditionalGeneration
from pptx import Presentation
from PIL import Image
import torch, uuid, json, traceback

BASE      = Path(__file__).resolve().parent.parent
RAW       = BASE / "raw"
RAW_IMG   = BASE / "raw_imgs"
CLEAN     = BASE / "clean"
RAW_IMG.mkdir(exist_ok=True)
CLEAN.mkdir(exist_ok=True)

proc  = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base",
            torch_dtype=torch.float16
        ).to("mps")

def caption(img_path: Path) -> str:
    try:
        inputs = proc(images=Image.open(img_path), return_tensors="pt").to("mps")
        ids = model.generate(**inputs, max_new_tokens=25)
        return proc.decode(ids[0], skip_special_tokens=True)
    except Exception:
        logging.exception(f"Caption failed {img_path}")
        return "image"

def textify(el: Element) -> str:
    """Return markdown or plain text for any unstructured element."""
    return getattr(el, "to_markdown", lambda: el.text)()

docs = chain(
    RAW.rglob("*.[pP][pP][tT][xX]"),
    RAW.rglob("*.[dD][oO][cC][xX]"),
    RAW.rglob("*.pdf"),
    # XLSX skipped until library fix
)

with Progress() as bar:
    for fp in bar.track(list(docs), description="Extracting docs"):
        try:
            doc_id = uuid.uuid4().hex
            els = partition(str(fp))
            md  = "\n".join(textify(e) for e in els)

            if fp.suffix.lower() == ".pptx":
                pres = Presentation(fp)
                for idx, slide in enumerate(pres.slides):
                    for shp in slide.shapes:
                        if shp.shape_type == 13:                               # picture
                            img = RAW_IMG / f"{doc_id}_{idx}.png"
                            with open(img, "wb") as f:
                                f.write(shp.image.blob)
                            md += f"\n\n![{caption(img)}]({img})"

            (CLEAN / f"{doc_id}.json").write_text(json.dumps({
                "id": doc_id, "title": fp.stem, "body": md, "source": str(fp)
            }))
            logging.info(f"📝 Extracted {fp.name}")
        except Exception:
            logging.error(f"❌ Skipped {fp.name}\n{traceback.format_exc()}")

