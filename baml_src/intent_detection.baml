// Defining a data model.
class ChatMessage {
  role "user" | "assistant"
  content string
}

class Workflow{
  workflow_id string
  workflow_guidelines string[]
}

class Intent {
  intent_id string
  workflows Workflow[]
}
class IntentWorkflowGuideline {
 intent_workflows Intent[]
}

class ActionClarification {
  action "ask_clarification" @stream.done
  clarification_question string @description("A short follow up clarification question for customer.") @stream.not_null
}

class ActionIntentDetected {
  action "detected_intent"
  intent string
  workflow string 
  @stream.done
}



function DetectIntent(todays_date: string, use_case_domain: string,intent_workflows: IntentWorkflowGuideline, chat: ChatMessage[]) -> string{
  // Specify a client as provider/model-name
  // you can use custom LLM params with a custom client name from clients.baml like "client CustomHaiku"
  client "openai/gpt-4.1" 
  prompt #"
    System Role:
      You are tasked with accurately selecting the most appropriate workflow_id to route a customer's request

    Use Case Domain: {{use_case_domain}}

    todays date:{{todays_date}}

    Available Intents and their workflows:
    {{ intent_workflows }}

    How to Handle Different Requests:
    1. Requests Needing More Details:
      If a request is related to {{use_case_domain}} but lacks sufficient detail, ask follow-up questions to clarify exactly what the customer needs.

    2. Requests  is related to {{use_case_domain}} but outside Supported Workflows:
      1. Explain that we are unable to assist with this at the moment
      2. Then ask if there’s anything else you can help with.

    3. Requests Unrelated to {{use_case_domain}}:
      If a request falls outside the scope of {{use_case_domain}}, politely explain that you are only able to help with matters relating to our domain. Invite the customer to ask if they have any needs that match the available workflows.


    {% for m in chat %}
     {{ _.role(m.role) }} 
     {{ m.content }}
     {% endfor %}

    {{ _.role('system') }}
    {{ ctx.output_format }}
    Response Guidelines:
      Keep responses clear, informative, and concise, upholding a professional yet friendly tone. 
      Avoid using emojis, bullet points, or structured lists. Always write in a conversational and engaging manner, encouraging the customer to share more details or other questions. 

    Reminders:
      Always speak as a representative of {{use_case_domain}}, using “I” or “we” to refer to the organization.
      Never direct customers to contact the {{use_case_domain}} or its staff outside of this support channel.
  "#
}



// Test the function with a sample resume. Open the VSCode playground to run this.
test shubham_test {
  functions [DetectIntent]
  args {
    todays_date "Today is Wednesday, May 14 2025"
    use_case_domain "Airline"
    intent_workflows {
      intent_workflows [
        {
          intent_id "ModifyBooking"
          workflows [
            {
              workflow_id "Wheelchair_Assistance",
              workflow_guidelines [
                "If customer conversation is about wheelchair assistance then trigger this workflow."
              ]
            },
            {
              workflow_id "Prebook_Meal",
              workflow_guidelines [
      "If customer conversation is about pre booking the meal then trigger this workflow."
    ]
            },
            {
              workflow_id "Name_Correction",
              workflow_guidelines [
       "If customer conversation is about correcting their name in ticket then trigger this workflow."
    
    ]
            }
          ]
        }

      ]
    }
    chat [
      { role "user", content "I need wheelchair." }
    ]
  }
}


test shubham_test_2 {
  functions [DetectIntent]
  args {
    todays_date "Today is Wednesday, May 14 2025",
    use_case_domain "Airline",
    intent_workflows {
      intent_workflows [
        {
          intent_id "ModifyBooking"
          workflows [
            {
              workflow_id "Wheelchair_Assistance",
              workflow_guidelines [
                "If customer conversation is about wheelchair assistance then trigger this workflow."
              ]
            },
            {
              workflow_id "Prebook_Meal",
              workflow_guidelines [
                "If customer conversation is about pre booking the meal then trigger this workflow."
              ]
            },
            {
              workflow_id "Name_Correction",
              workflow_guidelines [
                "If customer conversation is about correcting their name in ticket then trigger this workflow."
              
              ]
            }
          ]
        }
      ]
    },
    chat [
      { role "user", content "I want to modify my booking." }
    ]
  }
}


test shubham_test_3 {
  functions [DetectIntent]
  args {
    todays_date "Today is Wednesday, May 14 2025"
    use_case_domain "Airline"
    intent_workflows {
      intent_workflows [
        {
          intent_id "ModifyBooking"
          workflows [
            {
              workflow_id "Wheelchair_Assistance",
              workflow_guidelines [
                "If customer conversation is about wheelchair assistance then trigger this workflow."
              ]
            },
            {
              workflow_id "Prebook_Meal",
              workflow_guidelines [
      "If customer conversation is about pre booking the meal then trigger this workflow."
    ]
            },
            {
              workflow_id "Name_Correction",
              workflow_guidelines [
       "If customer conversation is about correcting their name in ticket then trigger this workflow."
    
    ]
            }
          ]
        }

      ]
    }
    chat [
      { role "user", content "I want to do a flight check in" }
    ]
  }
}

test shubham_test_4 {
  functions [DetectIntent]
  args {
    todays_date "Today is Wednesday, May 14 2025"
    use_case_domain "Airline"
    intent_workflows {
      intent_workflows [
        {
          intent_id "ModifyBooking"
          workflows [
            {
              workflow_id "Wheelchair_Assistance",
              workflow_guidelines [
                "If customer conversation is about wheelchair assistance then trigger this workflow."
              ]
            },
            {
              workflow_id "Prebook_Meal",
              workflow_guidelines [
      "If customer conversation is about pre booking the meal then trigger this workflow."
    ]
            },
            {
              workflow_id "Name_Correction",
              workflow_guidelines [
       "If customer conversation is about correcting their name in ticket then trigger this workflow."
    
    ]
            }
          ]
        }

      ]
    }
    chat [
      { role "user", content "I want to book a haircut" }
    ]
  }
}