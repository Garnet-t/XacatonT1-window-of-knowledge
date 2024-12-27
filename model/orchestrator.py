from backend_utils.file_handlers import FileHandlerFactory as FHF
from backend_utils.text_processor import DefaultTextProcessor as DTP
from backend_utils.qa_chain import QAChainRunner as QAR
from parameter_controller import ParameterController as PC
from typing import List, Optional, Tuple, Dict, IO
import logging
from pydantic.error_wrappers import ValidationError as VE

class Orchestrator:
    def __init__(self, config: PC) -> None:
        self._cfg = config
        logging.basicConfig(level=logging.INFO)
        self._auth = Auth()
        self._fh = FHF()
        self._tp = DTP(config)
        self._qa = QAR(config)

    def execute(self, data_sources: List[IO], query: str) -> str:
        def _setup():
            try:
                self._qa.setup()
            except VE:
                return "Invalid or missing API key. Please ensure you have entered a valid OpenAI API key."
            return None

        def _validate():
            if data_sources and len(data_sources) > 3:
                logging.warning("Please upload a maximum of 3 files")
                return False, "Please upload a maximum of 3 files"
            if not query or not data_sources:
                logging.warning("Both files and user question are required.")
                return False, "Both files and user question are required."
            return True, ""

        def _read():
            combined = ""
            for source in data_sources:
                if source is not None:
                    handler = self._fh.get_file_handler(source.type)
                    content = handler.read_file(source)
                    if not content:
                        logging.error(f"No text could be extracted from {source.name}. Please ensure the file is not encrypted or corrupted.")
                        return None
                    else:
                        combined += content
            return combined

        def _chunk(text: str) -> Optional[List[str]]:
            segments = self._tp.split_text(text)
            if not segments:
                logging.warning("Couldn't split the text into chunks. Please try again with different text.")
                return None
            return segments

        def _embed(segments: List[str]) -> Optional[Dict]:
            kb = self._tp.create_embeddings(segments)
            if not kb:
                logging.warning("Couldn't create embeddings from the text. Please try again.")
                return None
            return kb

        def _retrieve(kb: Dict, q: str) -> Optional[List[str]]:
            relevant = self._qa.get_relative_chunks(kb, q)
            if not relevant:
                logging.warning("Couldn't find any relevant chunks for your question. Please try asking a different question.")
                return None
            return relevant

        def _run_qa(docs: List[str], q: str) -> str:
            return self._qa.run_chain(docs, q)

        error = _setup()
        if error:
            return error

        is_valid, msg = _validate()
        if not is_valid:
            return msg

        text = _read()
        if text is None:
            return "No text could be extracted from the provided files. Please try again with different files."

        chunks = _chunk(text)
        if chunks is None:
            return "Couldn't split the text into chunks. Please try again with different text."

        kb = _embed(chunks)
        if kb is None:
            return "Couldn't create embeddings from the text. Please try again."

        relevant = _retrieve(kb, query)
        if relevant is None:
            return "Couldn't find any relevant chunks for your question. Please try asking a different question."

        return _run_qa(relevant, query)
