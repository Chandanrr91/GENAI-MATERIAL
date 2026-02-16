import pandas as pd
import torch
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from concurrent.futures import ThreadPoolExecutor

# Load dataset
file_path = "/Users/akellaprudhvi/mystuff/ecom/mara-olist-ecommerce-data/data/olist-ecommerce/olist_order_reviews_dataset.csv"
df = pd.read_csv(file_path)

# Filter out empty, null, and NaN values
df_filtered = df.dropna(subset=['review_comment_message'])
df_filtered = df_filtered[df_filtered['review_comment_message'].str.strip() != '']

# Load pre-trained M2M100 model for Portuguese to English translation
model_name = "facebook/m2m100_418M"
tokenizer = M2M100Tokenizer.from_pretrained(model_name)
model = M2M100ForConditionalGeneration.from_pretrained(model_name)

# Enable GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# Define batch translation function
def translate_batch(texts, max_length=256):
    """
    Translates a batch of Portuguese sentences into English.
    """
    try:
        # Tokenize and move to GPU if available
        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
        inputs = {key: value.to(device) for key, value in inputs.items()}

        # Generate translations
        translated_tokens = model.generate(**inputs, max_length=max_length)

        # Decode to readable text
        return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)

    except Exception as e:
        print(f"Error translating batch: {e}")
        return [None] * len(texts)

# Define parallel batch processing
def translate_parallel(text_list, batch_size=32, num_workers=4):
    """
    Translates a list of sentences in parallel using batch processing.
    """
    translations = [None] * len(text_list)  # Placeholder for translated text
    num_batches = len(text_list) // batch_size + (1 if len(text_list) % batch_size > 0 else 0)

    def process_batch(i):
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, len(text_list))
        batch = text_list[start_idx:end_idx]
        translations[start_idx:end_idx] = translate_batch(batch)

    # Run batch processing in parallel
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        executor.map(process_batch, range(num_batches))

    return translations

# Apply batch + parallel translation
df_filtered['review_comment_message_english'] = translate_parallel(df_filtered['review_comment_message'].tolist(), batch_size=32, num_workers=4)

# Save the updated DataFrame
output_file_path = "translated_reviews_parallel_batch.csv"
df_filtered.to_csv(output_file_path, index=False)

print(f"✅ Parallel Batch Translation Complete! File saved as: {output_file_path}")
