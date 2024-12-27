from backend_utils.file_handlers import FileHandlerFactory as FHF
from backend_utils.text_processor import DefaultTextProcessor as DTP
from backend_utils.qa_chain import QAChainRunner as QAR
from parameter_controller import ParameterController as PC
from typing import List, Optional, Tuple, Dict, IO
import logging
from pydantic.error_wrappers import ValidationError as VE

class Orchestrator:
    def __init__(self, config: PC, kafka_bootstrap_servers: str, kafka_topic: str) -> None:
        self._cfg = config
        logging.basicConfig(level=logging.INFO)
        self._auth = Auth()
        self._fh = FHF()
        self._tp = DTP(config)
        self._qa = QAR(config)
        self._kb_plug = KnowledgeBasePlug(kafka_bootstrap_servers, kafka_topic)

    def execute(self, data_sources: List[IO], query: str) -> str:
        def _setup():
            try:
                self._qa.setup()
            except VE:
                return "Неверный или отсутствующий API ключ. Пожалуйста, убедитесь, что вы ввели действительный ключ API OpenAI."
            return None

        def _validate():
            if data_sources and len(data_sources) > 3:
                logging.warning("Пожалуйста, загрузите максимум 3 файла")
                return False, "Пожалуйста, загрузите максимум 3 файла"
            if not query or not data_sources:
                logging.warning("Требуются как файлы, так и вопрос пользователя.")
                return False, "Требуются как файлы, так и вопрос пользователя."
            return True, ""

        def _embed(segments: List[str]) -> Optional[Dict]:
            # Отправка фрагментов в Kafka для обработки
            messages = [{"text": chunk} for chunk in segments]
            self._kb_plug.produce_messages(messages)

            # Потребление обработанных вложений из Kafka
            processed_messages = self._kb_plug.consume_messages()
            if not processed_messages:
                logging.warning("Не удалось создать вложения из текста. Пожалуйста, попробуйте снова.")
                return None

            # Обработка вложений с помощью Spark
            embeddings = self._kb_plug.process_with_spark(processed_messages)
            if not embeddings:
                logging.warning("Не удалось создать вложения из текста. Пожалуйста, попробуйте снова.")
                return None

            return embeddings

        # ... (остальная часть кода)

def закрыть_ресурсы(self) -> None:
    """
    Закрывает потребителя Kafka, продюсера и сессию Spark.
    """
    try:
        self.consumer.close()
        self.producer.close()
        self.spark.stop()
        logging.info("Ресурсы Kafka и Spark закрыты успешно.")
    except Exception as e:
        logging.error(f"Ошибка при закрытии ресурсов: {e}")

### Пример использования

if __name__ == "__main__":
    # Инициализация ModelLauncher и Orchestrator
    launcher = ModelLauncher("config.yaml")
    launcher.initialize()

    # Инициализация KnowledgeBasePlug
    kafka_servers = "localhost:9092"
    kafka_topic = "knowledge_base_topic"
    kb_plug = KnowledgeBasePlug(kafka_servers, kafka_topic)

    # Пример файлов и вопроса (замените на реальные входные данные)
    example_files = []  # Список объектов файлов
    example_question = "Какая основная тема?"

    # Запуск QA pipeline
    result = launcher.run(example_files, example_question)
    print(result)

    # Закрытие ресурсов
    kb_plug.закрыть_ресурсы()
