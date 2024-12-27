 ServerCore module interconnects all the previous modules (ModelLauncher, Orchestrator, and KnowledgeBasePlug) to create a fully functional server. This server will expose an API for handling file uploads and user questions, and it will orchestrate the entire QA pipeline.

### ServerCore Module

from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
import logging
from model_launcher import ModelLauncher
from knowledge_base_plug import KnowledgeBasePlug
import uvicorn

class ServerCore:
    def __init__(self, config_path: str, kafka_bootstrap_servers: str, kafka_topic: str) -> None:
        """
        Initializes the ServerCore with configurations for ModelLauncher and KnowledgeBasePlug.
        
        Args:
            config_path: Path to the configuration file for ModelLauncher.
            kafka_bootstrap_servers: Kafka bootstrap servers for KnowledgeBasePlug.
            kafka_topic: Kafka topic for KnowledgeBasePlug.
        """
        self.config_path = config_path
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_topic = kafka_topic

        # Initialize ModelLauncher and KnowledgeBasePlug
        self.model_launcher = ModelLauncher(self.config_path)
        self.kb_plug = KnowledgeBasePlug(self.kafka_bootstrap_servers, self.kafka_topic)

        # Initialize FastAPI app
        self.app = FastAPI(title="QA Pipeline Server", description="Server for handling QA pipeline requests.")

        # Register API endpoints
        self._register_endpoints()

        logging.info("ServerCore initialized successfully.")

    def _register_endpoints(self) -> None:
        """
        Registers API endpoints for the server.
        """

        @self.app.post("/upload-and-query/")
        async def upload_and_query(files: List[UploadFile] = File(...), question: str = ""):
            """
            Endpoint for uploading files and submitting a question.
            
            Args:
                files: List of uploaded files.
                question: User's question input.
            
            Returns:
                dict: Response from the QA pipeline.
            """
            if not files or not question:
                raise HTTPException(status_code=400, detail="Both files and question are required.")

            try:
                # Initialize the model launcher if not already initialized
                if not self.model_launcher._orchestrator:
                    self.model_launcher.initialize()

                # Run the QA pipeline
                result = self.model_launcher.run(files, question)
                return {"response": result}
            except Exception as e:
                logging.error(f"Error processing request: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """
            Handles server shutdown by closing resources.
            """
            self.kb_plug.close()
            logging.info("Server resources closed successfully.")

    def run(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """
        Runs the FastAPI server.
        
        Args:
            host: Host address for the server. Defaults to "0.0.0.0".
            port: Port for the server. Defaults to 8000.
        """
        logging.info(f"Starting server on {host}:{port}...")
        uvicorn.run(self.app, host=host, port=port)

# Example usage
if __name__ == "__main__":
    # Configuration paths
    config_path = "config.yaml"
    kafka_bootstrap_servers = "localhost:9092"
    kafka_topic = "knowledge_base_topic"

    # Initialize and run the server
    server = ServerCore(config_path, kafka_bootstrap_servers, kafka_topic)
    server.run()
### Key Features of ServerCore:
1. FastAPI Integration:
   - Exposes a REST API for uploading files and submitting questions.
   - Uses UploadFile for handling file uploads and File for parsing multipart form data.
