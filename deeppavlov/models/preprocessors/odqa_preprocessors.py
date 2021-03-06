# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List, Callable, Union
from itertools import chain

from nltk import sent_tokenize

from deeppavlov.core.common.log import get_logger
from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

logger = get_logger(__name__)


@register('document_chunker')
class DocumentChunker(Component):
    """Make chunks from a document or a list of documents. Don't tear up sentences if needed.

    Args:
        sentencize_fn: a function for sentence segmentation
        keep_sentences: whether to tear up sentences between chunks or not
        tokens_limit: a number of tokens in a single chunk (usually this number corresponds to the squad model limit)
        flatten_result: whether to flatten the resulting list of lists of chunks
        paragraphs: whether to split document by paragrahs; if set to True, tokens_limit is ignored

    Attributes:
        keep_sentences: whether to tear up sentences between chunks or not
        tokens_limit: a number of tokens in a single chunk
        flatten_result: whether to flatten the resulting list of lists of chunks
        paragraphs: whether to split document by paragrahs; if set to True, tokens_limit is ignored

    """

    def __init__(self, sentencize_fn: Callable = sent_tokenize, keep_sentences: bool = True,
                 tokens_limit: int = 400, flatten_result: bool = False,
                 paragraphs: bool = False, *args, **kwargs) -> None:
        self._sentencize_fn = sentencize_fn
        self.keep_sentences = keep_sentences
        self.tokens_limit = tokens_limit
        self.flatten_result = flatten_result
        self.paragraphs = paragraphs

    def __call__(self, batch_docs: List[Union[str, List[str]]]) -> \
            List[Union[List[str], List[List[str]]]]:
        """Make chunks from a batch of documents. There can be several documents in each batch.
        Args:
            batch_docs: a batch of documents / a batch of lists of documents
        Returns:
            chunks of docs, flattened or not
        """

        result = []

        for docs in batch_docs:
            batch_chunks = []
            if isinstance(docs, str):
                docs = [docs]
            for doc in docs:
                if self.paragraphs:
                    split_doc = doc.split('\n\n')
                    split_doc = [sd.strip() for sd in split_doc]
                    split_doc = list(filter(lambda x: len(x) > 40, split_doc))
                    batch_chunks.append(split_doc)
                else:
                    doc_chunks = []
                    if self.keep_sentences:
                        sentences = sent_tokenize(doc)
                        n_tokens = 0
                        keep = []
                        for s in sentences:
                            n_tokens += len(s.split())
                            if n_tokens > self.tokens_limit:
                                if keep:
                                    doc_chunks.append(' '.join(keep))
                                    n_tokens = 0
                                    keep.clear()
                            keep.append(s)
                        if keep:
                            doc_chunks.append(' '.join(keep))
                        batch_chunks.append(doc_chunks)
                    else:
                        split_doc = doc.split()
                        doc_chunks = [split_doc[i:i + self.tokens_limit] for i in
                                      range(0, len(split_doc), self.tokens_limit)]
                        batch_chunks.append(doc_chunks)
            result.append(batch_chunks)

        if self.flatten_result:
            if isinstance(result[0][0], list):
                for i in range(len(result)):
                    flattened = list(chain.from_iterable(result[i]))
                    result[i] = flattened

        return result


@register('string_multiplier')
class StringMultiplier(Component):
    """Make a list of strings from a provided string. A length of the resulting list equals a length
    of a provided reference argument.

    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, batch_s: List[str], ref: List[str]) -> List[List[str]]:
        """ Multiply each string in a provided batch of strings.

        Args:
            batch_s: a batch of strings to be multiplied
            ref: a reference to obtain a length of the resulting list

        Returns:
            a multiplied s as list

        """
        res = []
        for s, r in zip(batch_s, ref):
            res.append([s] * len(r))

        return res
