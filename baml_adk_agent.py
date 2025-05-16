import os
import logging
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Final

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.adk.events import Event


# --- baml imports ---
from baml_client.async_client import b
from baml_client.types import ChatMessage
from baml_client import reset_baml_env_vars


# --- Constants ---
APP_NAME: Final[str] = "Intent_detection"
USER_ID: Final[str] = "12345"
SESSION_ID: Final[str] = "123344"

# --- Configure Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

reset_baml_env_vars(os.environ.copy())
# Load environment variables from .env file
load_dotenv()


def convert_adk_events_to_baml_chat_messages(
    adk_events: List[Event],
) -> List[ChatMessage]:
    """Converts a list of ADK Events to a list of BAML ChatMessages."""
    messages = []
    for event in adk_events:
        if event.content and event.content.parts:
            # Assuming the first part of the content is the text
            text_content = event.content.parts[0].text
            if text_content:
                role = "user" if event.author == "user" else "assistant"
                messages.append(ChatMessage(role=role, content=text_content))
    return messages


class BamlAgent(BaseAgent):
    """
    An agent that uses a BAML client to detect user intent based on conversation history
    and predefined workflows.
    """

    def __init__(self, name: str):
        super().__init__(name=name)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Orchestrates the intent detection workflow using BAML.
        Streams partial and final intent detection results as ADK Events.
        """
        logger.info(f"[{self.name}] Invoked. Processing intent detection.")
        logger.debug(f"[{self.name}] Current session events: {len(ctx.session.events)}")

        todays_date = ctx.session.state.get("todays_date", "Unknown date")
        use_case_domain = ctx.session.state.get("use_case_domain", "General")
        intent_workflows = ctx.session.state.get("intent_workflows", {})

        chat_history = convert_adk_events_to_baml_chat_messages(ctx.session.events)

        if not chat_history:
            logger.warning(f"[{self.name}] No chat history found to process for intent.")
            # Optionally yield an event indicating no action or an error
            # For now, just return
            return

        logger.debug(f"[{self.name}] Calling BAML DetectIntent with domain: {use_case_domain}")

        # The BAML stream likely yields partial updates to an object like IntentResponse
        # Each `baml_stream_chunk` would be an instance of that (partially filled) object
        final_baml_output_json = ""
        try:
            stream = b.stream.DetectIntent(
                todays_date=todays_date,
                use_case_domain=use_case_domain,
                intent_workflows=intent_workflows,  # Assuming 'entities' is the correct param name for BAML
                chat=chat_history,
            )
            # Process stream for partial updates
            async for baml_stream_chunk in stream:
                # Assuming baml_stream_chunk has model_dump_json()
                # and represents the evolving state of the detected intent
                if not isinstance(baml_stream_chunk, str):
                    # if pydantic model
                    current_baml_output_json = baml_stream_chunk.model_dump_json()
                else:
                    current_baml_output_json = baml_stream_chunk
                final_baml_output_json = current_baml_output_json

                event_part = types.Part(text=current_baml_output_json)
                event_content = types.Content(parts=[event_part])
                yield Event(
                    author=self.name,
                    invocation_id=ctx.invocation_id,
                    content=event_content,
                    partial=True,  # Indicate it's part of a stream
                )

            # After the stream is exhausted, yield the final complete event
            if final_baml_output_json:
                event_part = types.Part(text=final_baml_output_json)
                event_content = types.Content(parts=[event_part])
                yield Event(
                    author=self.name,
                    invocation_id=ctx.invocation_id,
                    content=event_content,
                    partial=False,  # This is the final, complete message for this turn
                )
            else:
                logger.warning(f"[{self.name}] BAML stream produced no output.")

        except Exception as e:
            logger.error(f"[{self.name}] Error during BAML stream processing: {e}", exc_info=True)
            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                error_message=f"[{self.name}] Error during BAML stream processing: {e}",
                partial=False,
            )

        logger.info(f"[{self.name}] Intent detection processing complete.")


def get_initial_session_state() -> Dict[str, Any]:
    """Returns the initial state for the session."""
    return {
        "intent_workflows": {
            "intent_workflows": [
                {
                    "intent_id": "ModifyBooking",
                    "workflows": [
                        {
                            "workflow_id": "Wheelchair_Assistance",
                            "workflow_guidelines": [
                                "If customer conversation is about wheelchair assistance then trigger this workflow."
                            ],
                        },
                        {
                            "workflow_id": "Prebook_Meal",
                            "workflow_guidelines": [
                                "If customer conversation is about pre booking the meal then trigger this workflow."
                            ],
                        },
                        {
                            "workflow_id": "Name_Correction",
                            "workflow_guidelines": [
                                "If customer conversation is about correcting their name in ticket then trigger this workflow."
                            ],
                        },
                    ],
                }
            ]
        },
        "todays_date": "Today is Wednesday, May 14 2025",
        "use_case_domain": "Airline",
    }


def _print_event_details(event: Event) -> None:
    """Helper function to print details of an ADK Event."""
    if event.content and event.content.parts:
        part_text = event.content.parts[0].text
        if event.get_function_calls():
            print(f"  Type: Tool Call Request: {part_text}")
        elif event.get_function_responses():
            print(f"  Type: Tool Result: {part_text}")
        elif part_text:
            if event.partial:
                print(f"  Type: Streaming Text Chunk: {part_text}")
            else:
                print(f"  Type: Complete Text Message: {part_text}")
        else:
            print("  Type: Other Content (e.g., code result)")
    elif event.actions and (event.actions.state_delta or event.actions.artifact_delta):
        print("  Type: State/Artifact Update")
    else:
        print("  Type: Control Signal or Other (e.g., empty event marking end of stream)")

    if event.is_final_response() and event.content and event.content.parts:
        print(f"Assistant: {event.content.parts[0].text})")


async def main_async():
    """Main asynchronous function to run the agent and interact with the user."""
    logger.info("Starting BAML Agent application...")

    baml_agent = BamlAgent(name="baml_intent_agent")
    session_service = InMemorySessionService()

    initial_state = get_initial_session_state()

    # Create or get session
    try:
        session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        if session:
            logger.info(f"Found existing session {SESSION_ID} for user {USER_ID}.")
            # Optionally, update state if needed, or reset if behavior requires it
            # session_service.update_session(session.session_key, state=initial_state)
        else:
            session = session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                session_id=SESSION_ID,
                state=initial_state,
            )
            logger.info(f"Created new session {SESSION_ID} for user {USER_ID}.")
    except Exception as e:
        logger.error(f"Error managing session: {e}", exc_info=True)
        return

    logger.info(f"Initial session state: {session.state}")

    runner = Runner(
        agent=baml_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    print("\nConversation with BAML Intent Agent started. Type 'exit' or 'quit' to end.")
    while True:
        try:
            user_input = await asyncio.to_thread(input, "You: ")  # Use asyncio.to_thread for input
        except KeyboardInterrupt:
            print("\nExiting...")
            break

        if user_input.lower() in ["exit", "quit"]:
            print("Ending conversation. Session data might persist in InMemorySessionService.")
            break

        if not user_input.strip():
            print("Agent: Please say something.")
            continue

        new_user_message = types.Content(role="user", parts=[types.Part(text=user_input)])

        print("--- Agent Response ---")
        try:
            async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=new_user_message):
                _print_event_details(event)
        except Exception as e:
            logger.error(f"Error during agent run: {e}", exc_info=True)
            print(f"System Error: An error occurred: {e}")
        print("--- End Agent Response ---")

        current_session = session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        if current_session:
            logger.debug(f"Session {SESSION_ID} now has {len(current_session.events)} events.")

        else:
            logger.error("Session lost unexpectedly!")
            break

    logger.info("BAML Agent application finished.")


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Application terminated by user.")
