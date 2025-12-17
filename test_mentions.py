#!/usr/bin/env python3
import polars as pl
from whatsapp_wrapped.analytics import extract_word_frequencies

# Create test data with mentions
test_df = pl.DataFrame({
    'message_type': ['text', 'text', 'text', 'text'],
    'message': [
        'Hola @Gonzalo como estas?',
        'El numero es @32984238948923',
        'Este es un mensaje normal sin menciones',
        'Otro mensaje con @usuario123 y texto'
    ]
})

# Extract word frequencies
word_freq = extract_word_frequencies(test_df)

print('Word frequencies shape:', word_freq.shape)
print('Top words:')

# Check that mentions are filtered out
words = word_freq['word'].to_list()
print('Words found:', len(words), 'words')
for word in words[:5]:  # Show first 5 words
    print(f'  - {repr(word)}')

# Verify mentions are not present
mentions_present = any('@' in word for word in words)
print('Mentions present:', mentions_present)

# Test stopwords
stopwords_test_df = pl.DataFrame({
    'message_type': ['text', 'text', 'text'],
    'message': [
        'El mensaje fue eliminado',
        'Los mensajes eliminados no se muestran',
        'deleted message'
    ]
})

stopwords_freq = extract_word_frequencies(stopwords_test_df)
stopwords_words = stopwords_freq['word'].to_list()
print('Stopwords test - words found:', len(stopwords_words))
for word in stopwords_words:
    print(f'  - {repr(word)}')

# Check if stopwords are filtered
has_stopwords = any(word in ['mensaje', 'mensajes', 'eliminado', 'eliminados', 'deleted', 'message', 'messages'] for word in stopwords_words)
print('Stopwords present:', has_stopwords)
