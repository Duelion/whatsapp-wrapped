"""Update sample report with Matrix names, word cloud, and fix avatars.

This script is used to generate the anonymized sample report from the real report.
Run after generating a report to create/update the sample_report.html file.
"""
import base64
import random
import re
from io import BytesIO

from wordcloud import WordCloud

# Matrix-themed words - including iconic/funny quotes and references
matrix_words = {
    # Iconic quotes and memes
    'spoon': 120,  # "There is no spoon"
    'whoa': 100,  # Neo's classic
    'kungfu': 95,  # "I know kung fu"
    'rabbit': 90,  # "Follow the white rabbit"
    'reddress': 85,  # Woman in the red dress
    'deja': 80,  # "Deja vu"
    'glitch': 75,  # "A glitch in the matrix"
    'cookie': 110,  # Oracle's cookies
    'dodge': 70,  # "Dodge this"
    'guns': 65,  # "Guns. Lots of guns."
    'woah': 60,  # Another Neo classic
    
    # Neo's words
    'matrix': 150, 'real': 100, 'choice': 90, 'believe': 85, 'free': 80,
    'one': 130, 'truth': 70, 'fight': 65, 'love': 60, 'destiny': 55,
    
    # Morpheus's words  
    'awaken': 95, 'redpill': 120, 'bluepill': 115, 'mind': 75, 'freedom': 70,
    'prophecy': 65, 'zion': 85, 'system': 60, 'control': 55, 'reality': 50,
    'illusion': 45, 'desert': 40,  # "Desert of the real"
    
    # Trinity's words
    'together': 70, 'trust': 65, 'strength': 60, 'heart': 55, 'protect': 50,
    'motorcycle': 45, 'rooftop': 40,
    
    # Oracle's words
    'know': 80, 'yourself': 75, 'future': 50, 'vase': 65,  # "The vase"
    'baked': 55, 'chocolate': 50,  # Her cookies
    
    # Agent Smith
    'smith': 90, 'virus': 70, 'purpose': 65, 'inevitable': 60,
    'humanity': 55, 'multiply': 50, 'mister': 85,  # "Mister Anderson"
    'anderson': 80,
    
    # General Matrix terms
    'hack': 55, 'code': 75, 'digital': 45, 'simulation': 60, 'agents': 70,
    'machines': 50, 'sentinels': 40, 'nebuchadnezzar': 35,
    'operator': 45, 'phone': 55, 'exit': 50, 'training': 40,
    'jump': 60, 'fly': 70, 'bullet': 80, 'slow': 55,  # Bullet time
    'unplugged': 65, 'jacked': 45, 'construct': 40, 'loading': 35,
    'sunglasses': 70, 'leather': 50, 'trenchcoat': 45,
    'karate': 40, 'backflip': 35, 'rooftop': 30,
    'helicopter': 45, 'lobby': 40,  # Lobby scene
    'pills': 60, 'wake': 55, 'sleep': 40, 'dream': 50,
    'battery': 45,  # Humans as batteries
    'squiddy': 35,  # Sentinels nickname
    'keymaker': 40, 'architect': 45, 'merovingian': 35,
    'french': 30, 'cake': 40,  # Merovingian's cake scene
}

# Name mappings (real -> Matrix characters)
NAME_MAP = {
    'Gonzalo Irarrazaval': 'Neo',
    'Rencoret': 'Morpheus', 
    'David Acuña': 'Trinity',
    'Eduardo Montes': 'Oracle',
    'Fsoza': 'Cypher',
    'Pucho': 'Tank',
    'Jaime': 'Dozer',
    'Felix De Vicente': 'Mouse',
    'Guru': 'Niobe',
    'Chicken Center': 'The Matrix',
}

# Color palette matching the theme (Matrix green + accents)
COLORS = ['#22c55e', '#3b82f6', '#8b5cf6', '#06b6d4', '#f59e0b', '#f43f5e']


def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    """Custom color function for word cloud."""
    # Make "matrix" and key words more likely to be green
    if word.lower() in ['matrix', 'code', 'hack', 'digital', 'glitch']:
        return '#22c55e' if random.random() > 0.3 else random.choice(COLORS)
    return random.choice(COLORS)


def generate_matrix_wordcloud() -> str:
    """Generate Matrix-themed word cloud and return as base64 data URI."""
    wc = WordCloud(
        width=1200,
        height=500,
        background_color='#09090b',
        color_func=color_func,
        max_words=150,
        min_font_size=10,
        max_font_size=120,
        prefer_horizontal=0.8,
        relative_scaling=0.5,
        margin=8,
        mode='RGB',
    )
    
    wc.generate_from_frequencies(matrix_words)
    
    # Convert to base64
    buffer = BytesIO()
    wc.to_image().save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return f'data:image/png;base64,{img_base64}'


def replace_names(content: str) -> str:
    """Replace real names with Matrix character names."""
    for real_name, matrix_name in NAME_MAP.items():
        content = content.replace(real_name, matrix_name)
    return content


def fix_avatars(content: str) -> str:
    """Fix avatar initials to match Matrix character names."""
    avatar_replacements = [
        (r'(<div class="user-avatar"[^>]*>)G(</div>\s*<div class="user-info">\s*<div class="user-name">Neo)',
         r'\1N\2'),
        (r'(<div class="user-avatar"[^>]*>)R(</div>\s*<div class="user-info">\s*<div class="user-name">Morpheus)',
         r'\1M\2'),
        (r'(<div class="user-avatar"[^>]*>)D(</div>\s*<div class="user-info">\s*<div class="user-name">Trinity)',
         r'\1T\2'),
        (r'(<div class="user-avatar"[^>]*>)E(</div>\s*<div class="user-info">\s*<div class="user-name">Oracle)',
         r'\1O\2'),
        (r'(<div class="user-avatar"[^>]*>)F(</div>\s*<div class="user-info">\s*<div class="user-name">Cypher)',
         r'\1C\2'),
        (r'(<div class="user-avatar"[^>]*>)P(</div>\s*<div class="user-info">\s*<div class="user-name">Tank)',
         r'\1T\2'),
        (r'(<div class="user-avatar"[^>]*>)J(</div>\s*<div class="user-info">\s*<div class="user-name">Dozer)',
         r'\1D\2'),
        (r'(<div class="user-avatar"[^>]*>)F(</div>\s*<div class="user-info">\s*<div class="user-name">Mouse)',
         r'\1M\2'),
        (r'(<div class="user-avatar"[^>]*>)G(</div>\s*<div class="user-info">\s*<div class="user-name">Niobe)',
         r'\1N\2'),
    ]
    
    for pattern, replacement in avatar_replacements:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    return content


def main():
    """Main function to generate sample report."""
    # Read the generated report
    with open('WhatsApp_Chat_-_Chicken_Center_report.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Step 1: Replace names
    print('[1/4] Replacing names with Matrix characters...')
    content = replace_names(content)
    
    # Step 2: Fix avatar initials
    print('[2/4] Fixing avatar initials...')
    content = fix_avatars(content)
    
    # Step 3: Generate and insert Matrix word cloud
    print('[3/4] Generating Matrix word cloud...')
    new_data_uri = generate_matrix_wordcloud()
    pattern = r'<img src="data:image/png;base64,[^"]+" alt="Word Cloud"'
    replacement = f'<img src="{new_data_uri}" alt="Word Cloud"'
    content = re.sub(pattern, replacement, content)
    
    # Step 4: Save sample report
    print('[4/4] Saving sample report...')
    with open('sample_report.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('\n[SUCCESS] Sample report generated successfully!')
    print('   File: sample_report.html')
    print('   Characters: Neo, Morpheus, Trinity, Oracle, Cypher, Tank, Dozer, Mouse, Niobe')


if __name__ == '__main__':
    main()

