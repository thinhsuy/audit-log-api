from core.agent.tool_format import ToolAdditionalParams, ToolResponseFormat
from textwrap import dedent
from core.agent.pandas_agent import Pandas_Agent, Connector, Condition

def params_format(name: str, type: str, description: str, required: bool = True):
    return {
        "name": name,
        "values": {
            "type": type,
            "description": description
        },
        "required": required
    }

def tool_format(
    tool_name: str,
    tool_description: str,
    params: list,
    tool_type: str = "function",
    tool_params_type: str = "object"
):
    return {
        "type": tool_type,
        "function": {
            "name": tool_name,
            "description": tool_description,
            "parameters": {
                "type": tool_params_type,
                "properties": {param["name"]: param["values"] for param in params},
                "required": [param["name"] for param in params if param["required"]],
            },
        }
    }

# ===============================================================================

async def search_data_postgres(
    user_query: str,
    additional_params: ToolAdditionalParams = None
):
    """
    Generate search to DB using pandasAI agent,
    allow connector connect to logs and tenants table only,
    because this allow `client-role` access this feature
    """
    tenant_id = additional_params.get_kwargs("tenant_id")
    # allow search based on `tenant_id` only
    logs_connector = Connector(table_name="audit_logs", conditions=[
        Condition(column="tenant_id", operator="=", value=tenant_id)
    ]).create()
    tenants_connector = Connector(table_name="tenants", conditions=[
        Condition(column="id", operator="=", value=tenant_id)
    ]).create()

    search_response = Pandas_Agent.get_search(
        query=user_query,
        connectors=[logs_connector, tenants_connector]
    )
    return ToolResponseFormat(
        content=f"""
Result of searching data from databse:
{search_response}
"""
    )

def generate_search_data_postgres_spec(params: list = []): 
    params.append(params_format(
        name="user_query",
        type="string",
        description=dedent("Query of user, which is converted into English. \
            PLEASE keep the original meaning and sentence structure of user query."),
    ))
    params.append(params_format(
        name="additional_params",
        type="object",
        description="Additional parameters object",
        required=False
    ))
    return tool_format(
        tool_name="search_data_postgres",
        tool_description="Use this tool/function to get information about logs or tenants from database",
        params=params
    )


AUDIT_LOG_FUNCTIONS_LIST = {
    'search_data_postgres': search_data_postgres,
}

AUDIT_LOG_FUNCTION_SPEC = [
    generate_search_data_postgres_spec()
]
