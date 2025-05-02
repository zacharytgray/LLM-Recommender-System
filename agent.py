from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from colorama import Fore
import asyncio
import json # Added import
from memory import MemoryManager # Added import

class Agent:
    def __init__(self, modelName):
        self.modelName = modelName
        self.memory = [] # This handles short-term conversation history
        self.temperature = 0.2
        self.model = ChatOllama(model=self.modelName, base_url="http://localhost:11434", temperature=self.temperature)
        self.instructionsFilename = "SystemInstructions/ConversationInstructions.txt"
        self.systemInstructions = ""
        self.importInstructions()

        # Initialize Memory Manager for long-term profile
        self.profile_path = "user_profile.json"
        self.memory_manager = MemoryManager(self.profile_path)
        profile_summary = self.memory_manager.get_profile_summary()

        # Add initial system message (including profile summary if available)
        initial_system_message = self.systemInstructions
        if profile_summary != "No profile information available yet.":
             initial_system_message += f"\n\nCurrent User Profile Summary:\n{profile_summary}"
        self.addToMemory('system', initial_system_message)

        self.responseTimeout = 60
        
    def importInstructions(self):
        try:
            with open(self.instructionsFilename, 'r') as f:
                self.systemInstructions += f.read()
        except FileNotFoundError:
            print(f"{Fore.RED}Instructions file not found: {self.instructionsFilename}{Fore.RESET}")
            exit(1)
            
    def addToMemory(self, role, content):
        if role == 'system':
            self.memory.append(SystemMessage(content=content))
        elif role == 'user':
            self.memory.append(HumanMessage(content=content))
        elif role == 'assistant':
            self.memory.append(AIMessage(content=content))
        else:
            raise ValueError(f"Unknown role: {role}") 

    async def extract_and_update_preferences(self, user_input):
        """Analyzes the user's message to extract preferences and update the profile."""
        if not user_input:
            return # Don't try to extract if there's no user input

        extraction_prompt_text = f"""
        Analyze the following user message. Identify any stated preferences about movies (e.g., liked/disliked genres, actors, directors, themes, specific movie mentions). 
        Format the extracted preferences as a JSON object where keys are preference types (e.g., 'liked_genres', 'disliked_actors', 'mentioned_movies') and values are the specific preferences mentioned.
        Only log information about movies. For instance, if the user says "I like fantasy books", log it as "liked_genres": ["fantasy"]. Do not log the book preference.
        If no preferences are mentioned, return an empty JSON object {{}}.

        User Message: "{user_input}"

        Extracted Preferences (JSON):
        """
        
        extraction_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an AI assistant specialized in extracting user preferences from user messages."),
            HumanMessage(content=extraction_prompt_text)
        ])
        
        # Use a separate chain/model call for extraction if desired, or reuse self.model
        extraction_chain = extraction_prompt | self.model 
        
        try:
            extraction_response = await extraction_chain.ainvoke({})
            extracted_text = extraction_response.content if isinstance(extraction_response, AIMessage) else extraction_response
            
            # Clean the response to get potential JSON
            json_part = extracted_text.strip().split('```json')[-1].split('```')[0].strip()
            if not json_part:
                 json_part = extracted_text.strip() # Fallback if no markdown code block

            # Try parsing the JSON
            extracted_prefs = json.loads(json_part)
            
            if isinstance(extracted_prefs, dict) and extracted_prefs:
                print(f"{Fore.MAGENTA}Extracted preferences: {extracted_prefs}{Fore.RESET}") # Debugging
                updated = False
                for key, value in extracted_prefs.items():
                    # Basic update logic: Overwrite or append if value is a list and key exists as list
                    # More sophisticated merging could be added here.
                    if isinstance(value, list) and key in self.memory_manager.profile and isinstance(self.memory_manager.profile[key], list):
                        # Append unique items
                        current_list = self.memory_manager.profile[key]
                        new_items = [item for item in value if item not in current_list]
                        if new_items:
                            self.memory_manager.update_profile(key, current_list + new_items)
                            updated = True
                    elif value: # Only update if value is not empty
                        self.memory_manager.update_profile(key, value)
                        updated = True
                
                if updated:
                    self.memory_manager.save_profile() # Save profile if changes were made
            
        except json.JSONDecodeError:
            print(f"{Fore.YELLOW}Could not decode JSON from preference extraction response: {extracted_text}{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.RED}Error during preference extraction: {e}{Fore.RESET}")

    async def generateResponseAsync(self, role=None, inputText=None): # Generate response based on input
        last_user_input = inputText # Store user input for extraction
        try:
            if inputText and role:
                self.addToMemory(role, inputText)

            history = ChatPromptTemplate.from_messages(self.memory)
            chain = history | self.model
            response = await chain.ainvoke({})
            response_content = response.content if isinstance(response, AIMessage) else response
            self.addToMemory('assistant', response_content)

            # --- Extract preferences after generating response, using only user input ---
            if last_user_input: # Only extract if there was user input
                await self.extract_and_update_preferences(last_user_input)
            # --- End Preference Extraction ---

            return response_content.strip()
        except Exception as e:
            print(f"{Fore.RED}Error generating response: {e}{Fore.RESET}")
            # Consider returning a default error message instead of exiting
            return "Sorry, I encountered an error while generating a response."
            # exit(1) # Avoid exiting the whole application on generation error

    def generateResponse(self, role=None, inputText=None): # Generate response based on input
        try:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                asyncio.wait_for(
                    self.generateResponseAsync(role, inputText),
                    timeout = self.responseTimeout
                    )
                )
            return response
        except asyncio.TimeoutError:
            print(f"{Fore.RED}Timeout error while generating response for Agent{Fore.RESET}")
            exit(1)
            
    def printMemory(self):
        print(f"----------------{Fore.LIGHTYELLOW_EX}Conversation History:{Fore.RESET}----------------")
        for i, message in enumerate(self.memory):
            # if i == 0: # Skip the system message
            #     continue
            if isinstance(message, SystemMessage):
                print(f"{Fore.LIGHTRED_EX}System: {message.content}{Fore.RESET}")
            elif isinstance(message, HumanMessage):
                print(f"{Fore.LIGHTGREEN_EX}Partner: {message.content}{Fore.RESET}")
            elif isinstance(message, AIMessage):
                print(f"{Fore.LIGHTBLUE_EX}Agent: {message.content}{Fore.RESET}")
            else:
                print(f"Unknown message type: {message}")
            print("----------------------------------------------------------------------------------------")
        print(f"----------------{Fore.LIGHTYELLOW_EX}END History:{Fore.RESET}----------------")

        # Also print the long-term profile
        print(f"\n----------------{Fore.LIGHTYELLOW_EX}User Profile:{Fore.RESET}----------------")
        profile_summary = self.memory_manager.get_profile_summary()
        print(profile_summary)
        print(f"----------------{Fore.LIGHTYELLOW_EX}END Profile:{Fore.RESET}----------------")

    def save_agent_profile(self):
        """Saves the agent's long-term user profile."""
        self.memory_manager.save_profile()
        print(f"{Fore.CYAN}User profile saved to {self.profile_path}{Fore.RESET}")