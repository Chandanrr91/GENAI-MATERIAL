import pandas as pd
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Load the CSV file
file_path = "/Users/akellaprudhvi/mystuff/ecom/mara-olist-ecommerce-data/data/olist-ecommerce/olist_order_reviews_dataset.csv"
df = pd.read_csv(file_path)

# Filter out empty, null, and NaN values in the 'review_comment_message' column
df_filtered = df.dropna(subset=['review_comment_message'])
df_filtered = df_filtered[df_filtered['review_comment_message'].str.strip() != '']

df_sampled  = df_filtered
# Select first 200,000 rows after filtering (reduce for testing)
# df_sampled = df_filtered.head(200)

# Load pre-trained T5 model for Portuguese → English translation
model_name = "unicamp-dl/translation-pt-en-t5"  # ✅ Correct Model
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Enable GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)


# Define offline batch translation function
def translate_offline(texts, batch_size=10, max_length=300):
    """
    Translates a list of Portuguese sentences into English using T5.
    """
    translations = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]  # Get batch of sentences
        try:
            # Format text for T5 (Prefix with "translate Portuguese to English: ")
            formatted_texts = [f"translate Portuguese to English: {t}" for t in batch]

            # Tokenize inputs
            inputs = tokenizer(formatted_texts, return_tensors="pt", padding=True, truncation=True,
                               max_length=max_length)
            inputs = {key: value.to(device) for key, value in inputs.items()}  # Move to GPU if available

            # Generate translations
            translated_tokens = model.generate(**inputs, max_length=max_length)

            # Decode translated texts
            decoded_texts = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
            translations.extend(decoded_texts)

        except Exception as e:
            print(f"Error translating batch {i}-{i + batch_size}: {e}")
            translations.extend([None] * len(batch))  # Fallback for errors
    return translations


# Convert the column to a list and translate
df_sampled['review_comment_message_english'] = translate_offline(df_sampled['review_comment_message'].tolist(),
                                                                 batch_size=10)

# Save the updated DataFrame
output_file_path = "translated_reviews_offline_t5.csv"
df_sampled.to_csv(output_file_path, index=False)

print(f"✅ Offline T5 translation complete! File saved at: {output_file_path}")
