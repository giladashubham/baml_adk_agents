import os
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv
from baml_client import reset_baml_env_vars
from baml_client.async_client import b
from baml_client.types import ChatMessage

# Load environment variables from .env file
load_dotenv()

reset_baml_env_vars(os.environ.copy())

# --- Configuration Constants ---
ASSISTANT_CONTEXT = "Today is Wednesday, May 14 2025"
ASSISTANT_DOMAIN = "Airline"
INTENT_WORKFLOW_CONFIG: Dict[str, Any] = {
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
}


async def stream_and_print_clarification(stream_response: b.stream.DetectIntent) -> str:
    """
    Streams the partial responses and prints the clarification question incrementally.
    Returns the full clarification question.
    """
    full_clarification_question = ""
    print("BOT: ", end="")
    async for partial in stream_response:
        if partial.action == "ask_clarification" and partial.clarification_question:
            if partial.clarification_question.startswith(full_clarification_question):
                diff = partial.clarification_question[len(full_clarification_question) :]
                if diff:
                    print(diff, end="", flush=True)
                full_clarification_question = partial.clarification_question
            else:
                print(f"\rBOT: {partial.clarification_question}", end="", flush=True)
                full_clarification_question = partial.clarification_question

        # print(f"\nDEBUG: Partial: {partial.model_dump_json(indent=2)}") # For debugging stream
    print()
    return full_clarification_question


async def main():
    messages: List[ChatMessage] = []
    print("Starting conversation with BAML Airline Assistant.")
    print("Type 'end' at any time to exit.")
    user_input = input("USER: ").strip()
    if user_input.lower() == "end":
        print("Exiting conversation.")
        return
    messages.append(ChatMessage(role="user", content=user_input))
    while True:
        print("\nThinking...")  # Indicate that the bot is processing
        stream_response = b.stream.DetectIntent(
            todays_date=ASSISTANT_CONTEXT,
            use_case_domain=ASSISTANT_DOMAIN,
            intent_workflows=INTENT_WORKFLOW_CONFIG,  # Renamed for clarity from original
            chat=messages,  # Renamed for clarity
        )
        _ = await stream_and_print_clarification(stream_response)
        final_response = await stream_response.get_final_response()
        if final_response.action == "ask_clarification":
            user_input = input("USER: ").strip()
            if user_input.lower() == "end":
                print("Exiting conversation.")
                break
            if final_response.clarification_question:
                messages.append(ChatMessage(role="assistant", content=final_response.clarification_question))
            else:
                # This case should ideally not happen if action is "ask_clarification"
                print("WARN: Assistant asked for clarification but no question text found.")

            messages.append(ChatMessage(role="user", content=user_input))

        elif final_response.action == "final_response":  # Or whatever the actual action is for a determined intent
            print(f"\nIntent Detected: {final_response.intent}")
            if final_response.workflow:
                print(f"Workflow Triggered: {final_response.workflow}")
            else:
                print("No specific workflow triggered for this intent.")
            break  # Exit loop as intent is resolved
        else:
            print(f"\nReceived unexpected final action: {final_response.action}")
            if hasattr(final_response, "error_message") and final_response.error_message:
                print(f"Error: {final_response.error_message}")
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nConversation ended by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        # For debugging, you might want to print the full traceback
        # import traceback
        # traceback.print_exc()
