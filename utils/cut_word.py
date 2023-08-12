import jieba
from django.db.models import Func, Value


class ToTsVector(Func):
    function = 'to_tsvector'
    template = "%(function)s('english', %(expressions)s)"


def cut_word(raw: str):
    seg_list = jieba.cut_for_search(raw)
    segmented_comment = " ".join(seg_list)
    return segmented_comment


def get_cut_word_search_vector(raw: str):
    return ToTsVector(Value(cut_word(raw)))
