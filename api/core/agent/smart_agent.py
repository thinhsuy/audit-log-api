import json
import inspect
from openai import AsyncAzureOpenAI
from core.config import logger
from core.agent.tool_format import (
    ToolAdditionalParams,
    ToolResponseFormat,
    AgentResponseFormat,
    ToolCallFormat,
)
from core.schemas.v1.chat import Conversation
from core.schemas.v1.enum import ChatRoleEnum
from typing import List


class SmartAgent:
    def __init__(
        self,
        client: AsyncAzureOpenAI,
        functions_list: dict,  # function list {"function name": function}
        functions_spec: list[dict],  # function describe [{..}, {..}]
        engine: str,  # name of model in Azure
        persona: str = "",
        init_message: str = None,  # system prompt
        name=None,
    ) -> "SmartAgent":
        if init_message is not None:
            init_hist = [
                {"role": "system", "content": persona},
                {"role": "assistant", "content": init_message},
            ]
        else:
            init_hist = [{"role": "system", "content": persona}]

        self.init_history = init_hist
        self.persona = persona
        self.engine = engine
        self.name = name
        self.client = client
        self.max_retry = 5
        self.max_token = 800

        self.functions_spec = functions_spec
        self.functions_list = functions_list

    @staticmethod
    def filter_conversation(
        conversation: List[Conversation],
    ) -> List[Conversation]:
        return [
            convers
            for convers in conversation
            if (
                isinstance(convers, Conversation)
                and convers.role
                in [
                    ChatRoleEnum.SYSTEM,
                    ChatRoleEnum.USER,
                    ChatRoleEnum.ASSISTANT,
                ]
            )
        ]

    async def run(
        self,
        user_input: str,
        conversation: List[Conversation] = None,
        additional_params: ToolAdditionalParams = None,
    ):
        if user_input is None:  # if no input return init message
            return self.init_history, self.init_history[1]["content"]
        if conversation is None:  # if no history return init message
            conversation = self.init_history.copy()

        conversation.append(
            Conversation(role=ChatRoleEnum.USER, content=user_input)
        )
        tool_call_results: list[ToolResponseFormat] = []
        tool_call_trackback: list[ToolCallFormat] = []
        # try to loop the chain of thougt to get out the final response
        for _ in range(self.max_retry):
            response = await self.client.chat.completions.create(
                model=self.engine,
                messages=[
                    convers.chat_format_dump()
                    for convers in conversation
                ],
                tools=self.functions_spec,
                tool_choice="auto",
                # max_tokens=1000,
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            finish_reason = response.choices[0].finish_reason
            response_message = response.choices[0].message

            if finish_reason == "content_filter":
                logger.warning("Content filter triggered.")
                logger.warning(
                    "Last message: {}\n".format(
                        conversation[-1].model_dump()
                    )
                )
                logger.warning("Full response: {}\n".format(response))
                continue
            elif response_message.content is None:
                response_message.content = ""

            tool_calls = response_message.tool_calls

            if tool_calls:
                # extend conversation with assistant's reply
                conversation.append(
                    Conversation(
                        role=response_message.role,
                        content=response_message.content,
                        tool_calls=response_message.tool_calls,
                    )
                )
                for tool_call in tool_calls:
                    function_name = tool_call.function.name

                    if function_name not in self.functions_list:
                        conversation.pop()
                        continue
                    function_to_call = self.functions_list[
                        function_name
                    ]

                    # verify function has correct number of arguments
                    function_args = json.loads(
                        tool_call.function.arguments
                    )

                    if (
                        SmartAgent.check_args(
                            function_to_call, function_args
                        )
                        is False
                    ):
                        conversation.pop()
                        continue

                    if additional_params:
                        function_args["additional_params"] = (
                            additional_params
                        )
                    if not inspect.iscoroutinefunction(
                        function_to_call(**function_args)
                    ):
                        function_response: ToolResponseFormat = (
                            await function_to_call(**function_args)
                        )
                    else:
                        function_response: ToolResponseFormat = (
                            function_to_call(**function_args)
                        )

                    tool_call_results.append(function_response)
                    # tool_call_trackback.append(tool_called)
                    # extend conversation with function response
                    conversation.append(Conversation(
                        tool_call_id=tool_call.id,
                        role=ChatRoleEnum.TOOL,
                        function_name=function_name,
                        content=function_response.content,
                    ))
                continue
            else:
                break  # if no function call break out of loop as this indicates that the agent finished the research and is ready to respond to the user

        assistant_response = response_message.content

        return AgentResponseFormat(
            content=assistant_response,
            conversation=SmartAgent.filter_conversation(conversation),
            tool_results=tool_call_results,
            tool_called=tool_call_trackback,
        )

    @staticmethod
    def check_args(function, args):
        sig = inspect.signature(function)
        params = sig.parameters

        for name in args:
            if name not in params:
                return False

        for name, param in params.items():
            if param.default is param.empty and name not in args:
                return False

    async def stream_response(self, conversation):
        response = await self.client.chat.completions.create(
            model=self.engine,
            messages=conversation,
            stream=True,
            max_tokens=800,
            temperature=0,
        )
        async for chunk in response:
            if "choices" in chunk and chunk["choices"]:
                for choice in chunk["choices"]:
                    if (
                        "delta" in choice
                        and "content" in choice["delta"]
                    ):
                        yield choice["delta"]["content"]
