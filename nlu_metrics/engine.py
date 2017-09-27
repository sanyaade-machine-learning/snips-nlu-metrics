from __future__ import unicode_literals

import io
import json
import os
import zipfile
from abc import ABCMeta, abstractmethod

from nlu_metrics.utils.temp_utils import tempdir_ctx

TRAINED_ENGINE_FILENAME = "trained_assistant.json"


class Engine(object):
    """
    Abstract class which represents an engine that can be used in the metrics
    API. All engine classes must inherit from `Engine`.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, language):
        pass

    @abstractmethod
    def fit(self, dataset):
        pass

    @abstractmethod
    def parse(self, text):
        pass


def build_nlu_engine_class(training_class, inference_class):
    class NLUEngine(Engine):
        def __init__(self, language):
            super(NLUEngine, self).__init__(language)
            self.language = language
            self.inference_engine = None

        def fit(self, dataset):
            training_engine = training_class(self.language)
            training_engine.fit(dataset)
            trained_engine_dict = training_engine.to_dict()
            self.inference_engine = get_inference_nlu_engine(
                self.language, trained_engine_dict, inference_class)

        def parse(self, text):
            return self.inference_engine.parse(text)

    return NLUEngine


def get_trained_nlu_engine(train_dataset, training_engine_class):
    language = train_dataset["language"]
    engine = training_engine_class(language)
    engine.fit(train_dataset)
    return engine


def get_inference_nlu_engine(language, trained_engine_dict,
                             inference_engine_class):
    with tempdir_ctx() as engine_dir:
        trained_engine_path = os.path.join(engine_dir, TRAINED_ENGINE_FILENAME)
        archive_path = os.path.join(engine_dir, 'assistant.zip')

        with io.open(trained_engine_path, mode='w', encoding='utf8') as f:
            f.write(json.dumps(trained_engine_dict).decode())
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.write(trained_engine_path, arcname=TRAINED_ENGINE_FILENAME)
        with io.open(archive_path, mode='rb') as f:
            data_zip = bytearray(f.read())

    return inference_engine_class(language, data_zip=data_zip)