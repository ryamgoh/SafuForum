import nltk
nltk.data.path.append('./data')
nltk.download('brown', download_dir='./data')

from nltk.corpus import brown

brown_data = brown.words()
brown_text = " ".join(brown_data)