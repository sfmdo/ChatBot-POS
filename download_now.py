from fastembed import TextEmbedding
import os
cache_path = os.path.join(os.getcwd(), "models_cache")
print("Descargando modelo real...")
model = TextEmbedding(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    cache_dir=cache_path
)
list(model.embed(["test"]))
print("¡DESCARGA COMPLETA!")
