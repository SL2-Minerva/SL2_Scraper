
from pythainlp.tokenize import syllable_tokenize


def segmenting(text):
    # work_split = word_tokenize(text, engine="newmm")
    word_split = syllable_tokenize(text)

    return list(filter(lambda x: x != ' ', word_split))


def compare_text_segmenting_all(text, keyword):
    segmented_keyword = segmenting(keyword)

    return all(
        word in text for word in segmented_keyword
    )
