from typing import List, IO
import logging

class ModelLauncher:
    def __init__(self, config_path: str = "config.yaml") -> None:
        """
        Initializes the ModelLauncher with configurations.
        
        Args:
            config_path: Path to the configuration file. Defaults to "config.yaml".
        """
        self._config = self._load_config(config_path)
        self._orchestrator = None

    def _load_config(self, config_path: str) -> ParameterController:
        """
        Loads the configuration from the specified file.
        
        Args:
            config_path: Path to the configuration file.
        
        Returns:
            ParameterController: An instance of ParameterController with loaded configurations.
        """
        try:
            return ParameterController(config_path)
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            raise

    def initialize(self) -> None:
        """
        Initializes the Orchestrator with the loaded configurations.
        """
        try:
            self._orchestrator = Orchestrator(self._config)
            logging.info("Orchestrator initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Orchestrator: {e}")
            raise

    def run(self, files: List[IO], question: str) -> str:
        """
        Executes the QA pipeline using the Orchestrator.
        
        Args:
            files: List of uploaded files.
            question: User's question input.
        
        Returns:
            str: The response from the QA pipeline.
        """
        if not self._orchestrator:
            raise RuntimeError("Orchestrator is not initialized. Call initialize() first.")
        
        try:
            logging.info("Running QA pipeline...")
            return self._orchestrator.execute(files, question)
        except Exception as e:
            logging.error(f"Error during QA pipeline execution: {e}")
            return f"An error occurred: {e}"

# Example usage
if __name__ == "__main__":
    launcher = ModelLauncher("config.yaml")
    launcher.initialize()

    # Example files and question (replace with actual inputs)
    example_files = []  # List of file objects
    example_question = "What is the main topic?"

    result = launcher.run(example_files, example_question)
    print(result)
