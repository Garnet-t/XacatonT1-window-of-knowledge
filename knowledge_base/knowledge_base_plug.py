from pyspark.sql import SparkSession
from kafka import KafkaConsumer, KafkaProducer
import json
from typing import List, Dict, Optional
import logging

class KnowledgeBasePlug:
    def __init__(self, kafka_bootstrap_servers: str, kafka_topic: str, spark_app_name: str = "KnowledgeBaseProcessor") -> None:
        """
        Инициализирует KnowledgeBasePlug с конфигурациями для Kafka и Spark.
        
        Аргументы:
            kafka_bootstrap_servers: Адреса серверов Kafka (например, "localhost:9092").
            kafka_topic: Тема Kafka для получения/отправки сообщений.
            spark_app_name: Название Spark-приложения. По умолчанию "KnowledgeBaseProcessor".
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic
        self.spark_app_name = spark_app_name

        # Инициализация Kafka-потребителя и продюсера
        self.consumer = KafkaConsumer(
            self.kafka_topic,
            bootstrap_servers=self.kafka_bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )

        # Инициализация Spark-сессии
        self.spark = SparkSession.builder \
            .appName(self.spark_app_name) \
            .getOrCreate()

        logging.info("KnowledgeBasePlug успешно инициализирован.")

    def consume_messages(self) -> Optional[List[Dict]]:
        """
        Получает сообщения из темы Kafka.
        
        Возвращает:
            List[Dict]: Список сообщений, полученных из Kafka.
        """
        messages = []
        try:
            for message in self.consumer:
                messages.append(message.value)
                if len(messages) >= 100:  # Обработка пакетами по 100 сообщений
                    break
            return messages
        except Exception as e:
            logging.error(f"Ошибка при получении сообщений из Kafka: {e}")
            return None

    def produce_messages(self, messages: List[Dict]) -> None:
        """
        Отправляет сообщения в тему Kafka.
        
        Аргументы:
            messages: Список сообщений для отправки.
        """
        try:
            for message in messages:
                self.producer.send(self.kafka_topic, value=message)
            self.producer.flush()
            logging.info(f"Отправлено {len(messages)} сообщений в Kafka.")
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщений в Kafka: {e}")

    def process_with_spark(self, data: List[Dict]) -> Optional[Dict]:
        """
        Обрабатывает данные с использованием Spark (например, для создания эмбеддингов или фильтрации сегментов).
        
        Аргументы:
            data: Список словарей, содержащих текстовые сегменты или эмбеддинги.
        
        Возвращает:
            Dict: Обработанные данные (например, эмбеддинги или отфильтрованные сегменты).
        """
        try:
            # Конвертация данных в Spark DataFrame
            df = self.spark.createDataFrame(data)

            # Пример: Выполнение обработки (например, фильтрации или трансформации)
            processed_df = df.filter(df["text"].isNotNull())  # Пример фильтрации

            # Преобразование обратно в словарь
            processed_data = processed_df.toPandas().to_dict(orient="records")
            return processed_data
        except Exception as e:
            logging.error(f"Ошибка при обработке данных с использованием Spark: {e}")
            return None
