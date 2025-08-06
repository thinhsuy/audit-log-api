from pandasai.connectors import PostgreSQLConnector
from pandasai import SmartDataframe, SmartDatalake, Agent
from core.config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    PANDAS_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT_NAME,
)
from pandasai.llm.azure_openai import AzureOpenAI
from typing import List, Literal
from core.config import logger
from pydantic import BaseModel

class Condition(BaseModel):
    column: str
    operator: Literal["=", ">", "<", ">=", "<=", "LIKE"]
    value: str


class Connector:
    def __init__(
        self, table_name: str, conditions: List[Condition] = None
    ) -> "Connector":
        self.connector_config: dict = {
            "host": DB_HOST,
            "port": DB_PORT,
            "database": DB_NAME,
            "username": DB_USER,
            "password": DB_PASSWORD,
            "table": table_name,
        }
        if conditions:
            # list condition format configure [column, operator, value]
            self.connector_config["where"] = [
                [condition.column, condition.operator, condition.value]
                for condition in conditions
            ]

    def create(self, connector_relations=None) -> PostgreSQLConnector:
        return PostgreSQLConnector(
            config=self.connector_config,
            connector_relations=connector_relations,
        )


class PandasAgent:
    def __init__(self):
        self.pandas_key: str = PANDAS_API_KEY
        self.llm = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME,
            api_version=AZURE_OPENAI_API_VERSION,
        )

    def get_search(
        self, query: str, connectors: List[PostgreSQLConnector] = None
    ) -> str:
        try:
            if not connectors:
                logger.error(f"Must have at least 1 connector")
                return None

            SmartDF = (
                SmartDataframe
                if len(connectors) == 1
                else SmartDatalake
            )

            self.df = SmartDF(
                connectors,
                config={
                    "llm": self.llm,
                    "pandasai_api_key": self.pandas_key,
                },
            )
            response = self.df.chat(query)
            return response
        except Exception as ex:
            logger.error(
                f"There an error when searching pandasai: {ex}"
            )
            return None


# Singleton initialization
Pandas_Agent = PandasAgent()
